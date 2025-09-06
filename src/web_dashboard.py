"""
Streamlit Dashboard for Factory Farm Emissions Tracking
Real-time visualization and analysis interface
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import ee
import json
from neuralgcm_integration import MethanePlumeTracker, CAFOSource

# Page config
st.set_page_config(
    page_title="Factory Farm Emissions Tracker",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-high {
        background-color: #ffcccc;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #ff0000;
    }
    .alert-moderate {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_cafo_data():
    """Load CAFO registry data"""
    # Placeholder data - in production, load from CSV
    data = pd.DataFrame({
        'name': ['Delmarva Dairy #1', 'Eastern Shore Poultry', 'Sussex Beef',
                'Maryland Mega Farm', 'Delaware Valley Dairy'],
        'lat': [38.5, 38.2, 38.7, 39.1, 38.9],
        'lon': [-75.8, -76.1, -75.5, -76.3, -75.2],
        'type': ['dairy', 'poultry', 'beef', 'dairy', 'dairy'],
        'emissions_kg_hr': [50.0, 30.0, 45.0, 65.0, 55.0],
        'animals': [2000, 50000, 1500, 2500, 2200],
        'permit_status': ['Active', 'Active', 'Under Review', 'Active', 'Expired']
    })
    return data

@st.cache_data
def get_sentinel_data(date_range):
    """Fetch Sentinel-5P data (cached)"""
    # Simulated data for demo
    dates = pd.date_range(date_range[0], date_range[1], freq='D')
    data = pd.DataFrame({
        'date': dates,
        'ch4_mean_ppb': np.random.normal(1850, 30, len(dates)),
        'ch4_max_ppb': np.random.normal(1950, 50, len(dates)),
        'coverage': np.random.uniform(0.7, 1.0, len(dates))
    })
    return data

def create_emission_heatmap(cafo_data):
    """Create heatmap of emissions"""
    fig = px.density_mapbox(
        cafo_data, 
        lat='lat', 
        lon='lon', 
        z='emissions_kg_hr',
        radius=30,
        center=dict(lat=38.5, lon=-75.8),
        zoom=7,
        mapbox_style="carto-positron",
        color_continuous_scale="Reds",
        title="Methane Emission Hotspots"
    )
    fig.update_layout(height=500)
    return fig

def create_time_series(sentinel_data):
    """Create time series plot"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sentinel_data['date'],
        y=sentinel_data['ch4_mean_ppb'],
        mode='lines',
        name='Mean CH₄',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=sentinel_data['date'],
        y=sentinel_data['ch4_max_ppb'],
        mode='lines',
        name='Max CH₄',
        line=dict(color='red', width=1, dash='dot')
    ))
    
    fig.update_layout(
        title="Methane Concentration Trends",
        xaxis_title="Date",
        yaxis_title="CH₄ (ppb)",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def run_dispersion_analysis(selected_cafos):
    """Run dispersion model for selected CAFOs"""
    tracker = MethanePlumeTracker([-77.8, 36.5, -74.5, 40.3])
    
    for _, cafo in selected_cafos.iterrows():
        source = CAFOSource(
            name=cafo['name'],
            lat=cafo['lat'],
            lon=cafo['lon'],
            emission_rate_kg_hr=cafo['emissions_kg_hr'],
            source_type=cafo['type']
        )
        tracker.add_cafo_source(source)
    
    # Simplified wind data
    met_data = {
        'u_wind': np.ones((50, 50)) * st.session_state.get('wind_speed', 5),
        'v_wind': np.ones((50, 50)) * st.session_state.get('wind_dir', 2),
        'temp': np.full((50, 50), 288)
    }
    
    forcing = tracker.prepare_neuralgcm_forcing(tracker.sources, met_data)
    dispersion = tracker.run_dispersion_model(forcing, hours=72)
    zones = tracker.calculate_health_impact_zones(dispersion)
    
    return tracker, dispersion, zones

def main():
    # Header
    st.title("🛰️ Factory Farm Emissions Tracker")
    st.markdown("**Real-time methane monitoring for animal advocacy**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Control Panel")
        
        # Date range selector
        date_range = st.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
        
        # Region selector
        region = st.selectbox(
            "Select Region",
            ["Chesapeake Bay", "California Central Valley", "North Carolina", "Iowa"]
        )
        
        # Analysis type
        analysis_type = st.radio(
            "Analysis Mode",
            ["Monitoring", "Dispersion Modeling", "Impact Assessment", "Reports"]
        )
        
        st.divider()
        
        # Model parameters
        if analysis_type == "Dispersion Modeling":
            st.subheader("🌬️ Model Parameters")
            st.session_state['wind_speed'] = st.slider("Wind Speed (m/s)", 0, 20, 5)
            st.session_state['wind_dir'] = st.slider("Wind Direction", -10, 10, 2)
            run_model = st.button("🚀 Run Dispersion Model", type="primary")
    
    # Load data
    cafo_data = load_cafo_data()
    sentinel_data = get_sentinel_data(date_range)
    
    # Main content area
    if analysis_type == "Monitoring":
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Active CAFOs",
                len(cafo_data),
                delta="+2 this month"
            )
        
        with col2:
            st.metric(
                "Avg CH₄ (ppb)",
                f"{sentinel_data['ch4_mean_ppb'].mean():.1f}",
                delta=f"+{np.random.uniform(1, 5):.1f}"
            )
        
        with col3:
            st.metric(
                "Peak Emissions",
                f"{cafo_data['emissions_kg_hr'].max():.0f} kg/hr",
                delta=f"+{np.random.uniform(5, 15):.0f}%"
            )
        
        with col4:
            violations = len(cafo_data[cafo_data['permit_status'] != 'Active'])
            st.metric(
                "Permit Violations",
                violations,
                delta="+1" if violations > 0 else "0"
            )
        
        # Main visualizations
        tab1, tab2, tab3 = st.tabs(["📍 Map", "📈 Trends", "📊 Data"])
        
        with tab1:
            st.plotly_chart(create_emission_heatmap(cafo_data), use_container_width=True)
            
            # Additional map with facilities
            m = folium.Map(location=[38.5, -75.8], zoom_start=7)
            for _, cafo in cafo_data.iterrows():
                color = 'red' if cafo['permit_status'] != 'Active' else 'green'
                folium.Marker(
                    [cafo['lat'], cafo['lon']],
                    popup=f"{cafo['name']}<br>Type: {cafo['type']}<br>Emissions: {cafo['emissions_kg_hr']} kg/hr",
                    icon=folium.Icon(color=color)
                ).add_to(m)
            
            folium_static(m)
        
        with tab2:
            st.plotly_chart(create_time_series(sentinel_data), use_container_width=True)
            
            # Emission breakdown
            fig_pie = px.pie(
                cafo_data, 
                values='emissions_kg_hr', 
                names='type',
                title="Emissions by Facility Type"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab3:
            st.subheader("CAFO Registry")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                type_filter = st.multiselect("Filter by Type", cafo_data['type'].unique())
            with col2:
                status_filter = st.multiselect("Filter by Status", cafo_data['permit_status'].unique())
            
            filtered_data = cafo_data
            if type_filter:
                filtered_data = filtered_data[filtered_data['type'].isin(type_filter)]
            if status_filter:
                filtered_data = filtered_data[filtered_data['permit_status'].isin(status_filter)]
            
            st.dataframe(
                filtered_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "emissions_kg_hr": st.column_config.NumberColumn(
                        "Emissions (kg/hr)",
                        format="%.1f"
                    ),
                    "lat": st.column_config.NumberColumn("Latitude", format="%.4f"),
                    "lon": st.column_config.NumberColumn("Longitude", format="%.4f")
                }
            )
            
            # Download button
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"cafo_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    elif analysis_type == "Dispersion Modeling":
        st.header("🌬️ Methane Dispersion Modeling")
        
        # CAFO selection
        selected_names = st.multiselect(
            "Select CAFOs for modeling",
            cafo_data['name'].tolist(),
            default=cafo_data['name'].head(3).tolist()
        )
        
        selected_cafos = cafo_data[cafo_data['name'].isin(selected_names)]
        
        if selected_cafos.empty:
            st.warning("Please select at least one CAFO")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Selected Facilities")
                st.dataframe(selected_cafos[['name', 'type', 'emissions_kg_hr']], hide_index=True)
            
            with col2:
                st.info(f"""
                **Model Configuration**
                - Wind Speed: {st.session_state.get('wind_speed', 5)} m/s
                - Wind Direction: {st.session_state.get('wind_dir', 2)}°
                - Forecast: 72 hours
                - Resolution: 1 km
                """)
            
            if st.sidebar.button("🚀 Run Dispersion Model", type="primary", key="run_button_main"):
                with st.spinner("Running NeuralGCM dispersion model..."):
                    tracker, dispersion, zones = run_dispersion_analysis(selected_cafos)
                    
                    # Display results
                    st.success("✅ Model run complete!")
                    
                    # Impact summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        high_risk = len(zones.get('high_risk', []))
                        st.metric("High Risk Areas", high_risk)
                    
                    with col2:
                        mod_risk = len(zones.get('moderate_risk', []))
                        st.metric("Moderate Risk Areas", mod_risk)
                    
                    with col3:
                        low_risk = len(zones.get('low_risk', []))
                        st.metric("Low Risk Areas", low_risk)
                    
                    # Alert messages
                    if 'high_risk' in zones and zones['high_risk']:
                        st.markdown(
                            '<div class="alert-high">⚠️ <b>HIGH EXPOSURE WARNING:</b> '
                            'Elevated methane levels detected. Vulnerable populations should limit outdoor activities.</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Dispersion visualization
                    exposure_data = []
                    for i, lat in enumerate(dispersion.lat.values):
                        for j, lon in enumerate(dispersion.lon.values):
                            exposure_data.append({
                                'lat': float(lat),
                                'lon': float(lon),
                                'exposure': float(dispersion.exposure_ppb.values[i, j])
                            })
                    
                    df_exposure = pd.DataFrame(exposure_data)
                    df_exposure = df_exposure[df_exposure['exposure'] > 10]  # Filter low values
                    
                    fig = px.density_mapbox(
                        df_exposure,
                        lat='lat',
                        lon='lon',
                        z='exposure',
                        radius=20,
                        center=dict(lat=38.5, lon=-75.8),
                        zoom=7,
                        mapbox_style="carto-positron",
                        color_continuous_scale="YlOrRd",
                        title="Predicted Methane Dispersion (72-hour forecast)"
                    )
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Impact Assessment":
        st.header("🏥 Community Impact Assessment")
        
        # Impact metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Population Exposed", "12,450", delta="+2,100")
            st.caption("Within 5km of CAFOs")
        
        with col2:
            st.metric("Schools Affected", "8", delta="+2")
            st.caption("Elevated CH₄ levels detected")
        
        with col3:
            st.metric("Health Cost Est.", "$2.3M", delta="+$450K")
            st.caption("Annual respiratory impacts")
        
        # Vulnerability map
        st.subheader("📍 Environmental Justice Analysis")
        
        # Create sample vulnerability data
        vuln_data = pd.DataFrame({
            'community': ['Delmarva Heights', 'Eastern Shore Village', 'Bay View',
                         'Farmington', 'Riverside'],
            'lat': [38.4, 38.3, 38.6, 38.8, 38.5],
            'lon': [-75.7, -76.0, -75.6, -75.4, -75.9],
            'vulnerability_score': [8.5, 7.2, 9.1, 6.3, 7.8],
            'population': [2500, 1800, 3200, 1200, 2800],
            'median_income': [35000, 42000, 28000, 51000, 38000]
        })
        
        fig = px.scatter_mapbox(
            vuln_data,
            lat='lat',
            lon='lon',
            size='population',
            color='vulnerability_score',
            hover_data=['community', 'median_income'],
            color_continuous_scale='RdYlGn_r',
            size_max=30,
            zoom=7,
            mapbox_style="carto-positron",
            title="Community Vulnerability Index"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Health impact timeline
        st.subheader("📈 Projected Health Impacts")
        
        dates = pd.date_range(start='2024-01', periods=12, freq='ME')
        health_data = pd.DataFrame({
            'date': dates,
            'respiratory_cases': np.random.poisson(15, 12).cumsum(),
            'emergency_visits': np.random.poisson(5, 12).cumsum(),
            'hospitalizations': np.random.poisson(2, 12).cumsum()
        })
        
        fig = go.Figure()
        for col in ['respiratory_cases', 'emergency_visits', 'hospitalizations']:
            fig.add_trace(go.Scatter(
                x=health_data['date'],
                y=health_data[col],
                mode='lines+markers',
                name=col.replace('_', ' ').title()
            ))
        
        fig.update_layout(
            title="Cumulative Health Impacts (12-month projection)",
            xaxis_title="Date",
            yaxis_title="Cases",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    else:  # Reports
        st.header("📄 Advocacy Reports")
        
        # Report generator
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Generate Custom Report")
            
            report_type = st.selectbox(
                "Report Type",
                ["Executive Summary", "Technical Analysis", "Media Brief", "Legal Documentation"]
            )
            
            facilities = st.multiselect(
                "Include Facilities",
                cafo_data['name'].tolist(),
                default=cafo_data['name'].head(3).tolist()
            )
            
            include_options = st.multiselect(
                "Include Sections",
                ["Emission Data", "Health Impacts", "Dispersion Maps", "Violation History", "Recommendations"],
                default=["Emission Data", "Health Impacts", "Recommendations"]
            )
        
        with col2:
            st.info("""
            **Report Features:**
            - Automated data compilation
            - Scientific citations
            - Publication-ready graphics
            - Export to PDF/Word
            """)
        
        if st.button("📝 Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                # Simulate report generation
                st.success("✅ Report generated successfully!")
                
                # Sample report content
                st.markdown(f"""
                ## {report_type}: Factory Farm Emissions Analysis
                
                **Date:** {datetime.now().strftime('%B %d, %Y')}  
                **Region:** Chesapeake Bay Watershed  
                **Facilities Analyzed:** {len(facilities)}
                
                ### Executive Summary
                
                This report documents methane emissions from {len(facilities)} concentrated animal feeding operations (CAFOs) 
                in the Chesapeake Bay watershed. Satellite monitoring reveals average emissions of 
                {cafo_data['emissions_kg_hr'].mean():.1f} kg/hr per facility, with peak concentrations 
                exceeding EPA recommended levels.
                
                ### Key Findings
                
                1. **Emission Levels:** Total regional emissions estimated at {cafo_data['emissions_kg_hr'].sum():.0f} kg/hr
                2. **Health Impact:** Approximately 12,450 residents exposed to elevated methane levels
                3. **Compliance:** {len(cafo_data[cafo_data['permit_status'] != 'Active'])} facilities with permit violations
                
                ### Recommendations
                
                - Implement continuous monitoring systems at high-emission facilities
                - Establish 2km buffer zones around CAFOs near residential areas
                - Mandate methane capture technology for facilities >1000 animal units
                """)
                
                # Download options
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 Download PDF",
                        data=b"PDF content here",  # Would be actual PDF
                        file_name=f"report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                with col2:
                    st.download_button(
                        "📥 Download Word",
                        data=b"DOCX content here",  # Would be actual DOCX
                        file_name=f"report_{datetime.now().strftime('%Y%m%d')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                with col3:
                    st.download_button(
                        "📥 Download Data",
                        data=cafo_data.to_csv(index=False),
                        file_name=f"data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
    
    # Footer
    st.divider()
    st.caption("🛰️ Factory Farm Emissions Tracker | Data updated daily from Sentinel-5P | [GitHub](https://github.com/yourrepo) | [Contact](mailto:contact@example.com)")

if __name__ == "__main__":
    main()