"""
Prophet-based Baseline Modeling and Anomaly Detection
Uses Facebook Prophet for robust time series analysis
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProphetAnomalyDetector:
    """
    Detects anomalies in CH4 time series using Prophet
    Accounts for seasonal patterns and trends
    """
    
    def __init__(self, 
                 confidence_interval: float = 0.95,
                 anomaly_threshold: float = 2.0):
        """
        Initialize anomaly detector
        
        Args:
            confidence_interval: Confidence interval for predictions (0.95 = 95%)
            anomaly_threshold: Number of standard deviations for anomaly detection
        """
        self.confidence_interval = confidence_interval
        self.anomaly_threshold = anomaly_threshold
        self.models = {}  # Store trained models per facility
        
    def prepare_data_for_prophet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for Prophet (requires 'ds' and 'y' columns)
        
        Args:
            df: DataFrame with 'date' and 'ch4_ppb' columns
            
        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        prophet_df = pd.DataFrame()
        prophet_df['ds'] = pd.to_datetime(df['date'])
        prophet_df['y'] = df['ch4_ppb']
        
        # Remove any NaN values
        prophet_df = prophet_df.dropna()
        
        # Sort by date
        prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)
        
        return prophet_df
    
    def build_baseline_model(self, 
                           timeseries: pd.DataFrame,
                           facility_type: str = 'dairy') -> Prophet:
        """
        Build Prophet model with appropriate seasonalities
        
        Args:
            timeseries: DataFrame with CH4 time series
            facility_type: Type of facility (affects seasonality)
            
        Returns:
            Trained Prophet model
        """
        
        # Prepare data
        prophet_df = self.prepare_data_for_prophet(timeseries)
        
        if len(prophet_df) < 30:
            logger.warning(f"Insufficient data for Prophet model ({len(prophet_df)} points)")
            return None
        
        # Initialize Prophet with custom parameters
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,  # CH4 doesn't have weekly patterns
            daily_seasonality=False,
            changepoint_prior_scale=0.05,  # Conservative change detection
            interval_width=self.confidence_interval,
            uncertainty_samples=1000
        )
        
        # Add custom seasonalities based on facility type
        if facility_type in ['dairy', 'beef']:
            # Dairy/beef have stronger summer peaks (manure decomposition)
            model.add_seasonality(
                name='summer_peak',
                period=365.25,
                fourier_order=5,
                prior_scale=10
            )
        elif facility_type == 'poultry':
            # Poultry has different seasonal pattern
            model.add_seasonality(
                name='quarterly',
                period=365.25/4,
                fourier_order=3,
                prior_scale=5
            )
        
        # Add monthly seasonality for all types
        model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=3,
            prior_scale=5
        )
        
        try:
            # Fit model
            model.fit(prophet_df)
            logger.info(f"Prophet model trained on {len(prophet_df)} observations")
            
            return model
            
        except Exception as e:
            logger.error(f"Error training Prophet model: {e}")
            return None
    
    def detect_anomalies(self, 
                        model: Prophet,
                        timeseries: pd.DataFrame,
                        recent_days: int = 30) -> Dict:
        """
        Detect anomalies in recent data using trained model
        
        Args:
            model: Trained Prophet model
            timeseries: Full time series DataFrame
            recent_days: Number of recent days to check for anomalies
            
        Returns:
            Dictionary with anomaly detection results
        """
        
        if model is None:
            return {'error': 'No model available'}
        
        # Prepare data
        prophet_df = self.prepare_data_for_prophet(timeseries)
        
        # Make predictions
        forecast = model.predict(prophet_df)
        
        # Focus on recent period
        recent_date = prophet_df['ds'].max() - timedelta(days=recent_days)
        recent_mask = prophet_df['ds'] >= recent_date
        
        recent_actual = prophet_df[recent_mask].copy()
        recent_forecast = forecast[recent_mask].copy()
        
        if len(recent_actual) == 0:
            return {'error': 'No recent data available'}
        
        # Merge actual and predicted
        comparison = pd.merge(
            recent_actual,
            recent_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            on='ds'
        )
        
        # Calculate residuals and z-scores
        comparison['residual'] = comparison['y'] - comparison['yhat']
        comparison['residual_std'] = (comparison['yhat_upper'] - comparison['yhat_lower']) / 4
        comparison['z_score'] = comparison['residual'] / comparison['residual_std']
        
        # Identify anomalies
        comparison['is_anomaly'] = np.abs(comparison['z_score']) > self.anomaly_threshold
        
        # Calculate enhancement (positive anomalies only)
        comparison['enhancement_ppb'] = np.where(
            comparison['residual'] > 0,
            comparison['residual'],
            0
        )
        
        # Get anomaly dates and magnitudes
        anomalies = comparison[comparison['is_anomaly']].copy()
        
        results = {
            'baseline_mean': recent_forecast['yhat'].mean(),
            'baseline_std': comparison['residual_std'].mean(),
            'anomaly_count': len(anomalies),
            'anomaly_dates': anomalies['ds'].dt.date.tolist(),
            'anomaly_magnitudes': anomalies['residual'].tolist(),
            'max_enhancement_ppb': comparison['enhancement_ppb'].max(),
            'mean_enhancement_ppb': comparison['enhancement_ppb'].mean(),
            'anomaly_details': anomalies[['ds', 'y', 'yhat', 'residual', 'z_score']].to_dict('records'),
            'recent_data': comparison
        }
        
        return results
    
    def validate_model(self, 
                      model: Prophet,
                      timeseries: pd.DataFrame,
                      horizon_days: int = 30) -> Dict:
        """
        Validate model performance using cross-validation
        
        Args:
            model: Trained Prophet model
            timeseries: Time series data
            horizon_days: Forecast horizon for validation
            
        Returns:
            Dictionary with validation metrics
        """
        
        if model is None:
            return {'error': 'No model available'}
        
        prophet_df = self.prepare_data_for_prophet(timeseries)
        
        # Need at least 3 periods for cross-validation
        if len(prophet_df) < horizon_days * 3:
            return {'error': 'Insufficient data for cross-validation'}
        
        try:
            # Perform cross-validation
            df_cv = cross_validation(
                model,
                initial=f'{len(prophet_df) - horizon_days * 2} days',
                period=f'{horizon_days // 2} days',
                horizon=f'{horizon_days} days'
            )
            
            # Calculate performance metrics
            df_p = performance_metrics(df_cv)
            
            metrics = {
                'mape': df_p['mape'].mean(),  # Mean absolute percentage error
                'rmse': df_p['rmse'].mean(),  # Root mean squared error
                'mae': df_p['mae'].mean(),    # Mean absolute error
                'coverage': df_p['coverage'].mean()  # Prediction interval coverage
            }
            
            logger.info(f"Model validation: MAPE={metrics['mape']:.2%}, RMSE={metrics['rmse']:.1f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in model validation: {e}")
            return {'error': str(e)}
    
    def analyze_facility(self,
                        facility_id: str,
                        timeseries: pd.DataFrame,
                        facility_type: str = 'dairy') -> Dict:
        """
        Complete analysis pipeline for a facility
        
        Args:
            facility_id: Facility identifier
            timeseries: CH4 time series data
            facility_type: Type of facility
            
        Returns:
            Complete analysis results
        """
        
        logger.info(f"Analyzing facility {facility_id} ({facility_type})")
        
        # Build baseline model
        model = self.build_baseline_model(timeseries, facility_type)
        
        if model is None:
            return {
                'facility_id': facility_id,
                'error': 'Could not build baseline model',
                'data_points': len(timeseries)
            }
        
        # Store model for future use
        self.models[facility_id] = model
        
        # Detect anomalies
        anomalies = self.detect_anomalies(model, timeseries)
        
        # Validate model
        validation = self.validate_model(model, timeseries)
        
        # Combine results
        results = {
            'facility_id': facility_id,
            'facility_type': facility_type,
            'data_points': len(timeseries),
            'date_range': {
                'start': timeseries['date'].min().isoformat() if 'date' in timeseries else None,
                'end': timeseries['date'].max().isoformat() if 'date' in timeseries else None
            },
            'baseline': {
                'mean_ppb': anomalies.get('baseline_mean', None),
                'std_ppb': anomalies.get('baseline_std', None)
            },
            'anomalies': {
                'count': anomalies.get('anomaly_count', 0),
                'dates': anomalies.get('anomaly_dates', []),
                'max_enhancement_ppb': anomalies.get('max_enhancement_ppb', 0),
                'mean_enhancement_ppb': anomalies.get('mean_enhancement_ppb', 0)
            },
            'validation': validation,
            'confidence': self._calculate_confidence(anomalies, validation)
        }
        
        return results
    
    def _calculate_confidence(self, 
                            anomalies: Dict,
                            validation: Dict) -> str:
        """
        Calculate confidence level based on anomalies and validation
        
        Returns:
            Confidence level: 'HIGH', 'MEDIUM', 'LOW'
        """
        
        if 'error' in validation or 'error' in anomalies:
            return 'LOW'
        
        # Check validation metrics
        mape = validation.get('mape', 1.0)
        coverage = validation.get('coverage', 0)
        
        if mape < 0.05 and coverage > 0.9:
            return 'HIGH'
        elif mape < 0.10 and coverage > 0.8:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_results(self, 
                    results: Dict,
                    output_path: str = "outputs/prophet_analysis.json"):
        """Save analysis results to JSON file"""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert any numpy/pandas types to native Python types
        def convert_types(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            else:
                return obj
        
        clean_results = convert_types(results)
        
        with open(output_file, 'w') as f:
            json.dump(clean_results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_file}")


# Example usage
if __name__ == "__main__":
    from gee_data_fetcher import Sentinel5PFetcher
    
    # Initialize components
    fetcher = Sentinel5PFetcher(authenticate=False)  # Use synthetic data
    detector = ProphetAnomalyDetector(confidence_interval=0.95, anomaly_threshold=2.0)
    
    # Get sample time series
    test_facility = 'MD_DAIRY_001'
    test_lat, test_lon = 38.521, -75.823
    
    print(f"\n🔍 Testing Prophet anomaly detection for {test_facility}")
    
    # Fetch time series (synthetic for testing)
    start = datetime(2023, 1, 1)
    end = datetime(2023, 12, 31)
    timeseries = fetcher.get_point_timeseries(test_lat, test_lon, start, end)
    
    if not timeseries.empty:
        # Analyze facility
        results = detector.analyze_facility(
            test_facility,
            timeseries,
            facility_type='dairy'
        )
        
        print(f"\n📊 Analysis Results:")
        print(f"Data points: {results['data_points']}")
        print(f"Baseline: {results['baseline']['mean_ppb']:.1f} ± {results['baseline']['std_ppb']:.1f} ppb")
        print(f"Anomalies detected: {results['anomalies']['count']}")
        
        if results['anomalies']['count'] > 0:
            print(f"Max enhancement: {results['anomalies']['max_enhancement_ppb']:.1f} ppb")
            print(f"Anomaly dates: {results['anomalies']['dates'][:5]}")  # First 5
        
        if 'mape' in results['validation']:
            print(f"\nModel validation:")
            print(f"  MAPE: {results['validation']['mape']:.2%}")
            print(f"  RMSE: {results['validation']['rmse']:.1f} ppb")
            print(f"  Coverage: {results['validation']['coverage']:.2%}")
        
        print(f"\nConfidence: {results['confidence']}")
        
        # Save results
        detector.save_results(results)
        print(f"\n✅ Results saved to outputs/prophet_analysis.json")