# Factory Farm Emissions Tracker 🛰️

## Exposing Hidden Emissions: Open-Source Satellite Tracking for Animal Advocacy

### 🎯 Mission

We're building the first open-source system to track and visualize methane emissions from factory farms using satellite data, making the invisible environmental impact of industrial animal agriculture visible and actionable for advocates.

## 🌍 The Problem

Factory farms (CAFOs - Concentrated Animal Feeding Operations) are major contributors to climate change through methane emissions, yet their environmental impact remains largely invisible to the public and policymakers. Current monitoring solutions cost $100K+ and are inaccessible to grassroots animal welfare organizations.

## 💡 Our Solution

This project democratizes environmental monitoring by providing free, open-source tools that:

- **Track methane plumes** from dairy farms, beef feedlots, and poultry operations using Sentinel-5P satellite data
- **Map emission patterns** across watersheds and communities
- **Quantify environmental impact** with scientific rigor
- **Generate evidence** for advocacy campaigns and policy work

## 🚀 Current Focus: Chesapeake Bay Watershed

We're starting with the Chesapeake Bay region, home to hundreds of industrial poultry operations that impact both animal welfare and environmental health. Our initial analysis covers:

- Delmarva Peninsula (MD Eastern Shore, DE, VA Eastern Shore)
- Major poultry and dairy CAFOs
- Manure lagoons and waste management sites
- 12-month emission trends and seasonal patterns

## 🛠️ Technical Stack

- **Satellite Data**: Sentinel-5P TROPOMI (methane column observations)
- **Processing**: Google Earth Engine for large-scale geospatial analysis
- **Future Integration**: 
  - NASA EMIT for high-resolution plume detection
  - Integrated Methane Inversion (IMI) for flux modeling
  - NeuralGCM for atmospheric dispersion modeling

## 📊 Use Cases for Advocates

1. **Policy Campaigns**: Provide data-driven evidence for stricter emissions regulations
2. **Corporate Accountability**: Track emissions from specific supplier facilities
3. **Community Impact**: Show how factory farm emissions affect nearby residents
4. **Media & Outreach**: Create compelling visualizations for public awareness
5. **Legal Action**: Support environmental justice cases with scientific data

## 🏃 Quick Start

### Prerequisites

- Google Earth Engine account (free): [Sign up here](https://code.earthengine.google.com)
- Python 3.8+ (optional for local analysis)

### Running the Analysis

1. **Google Earth Engine (Recommended for beginners)**
   - Open the [GEE Code Editor](https://code.earthengine.google.com)
   - Copy contents from `scripts/gee_ch4_chesapeake.js`
   - Click "Run" to generate methane maps and time series

2. **Local Python Setup (For advanced users)**
   ```bash
   # Clone the repository
   git clone https://github.com/[username]/factory-farm-monitoring.git
   cd factory-farm-monitoring
   
   # Set up environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   
   # Authenticate Earth Engine
   earthengine authenticate
   ```

## 📁 Project Structure

```
├── scripts/               # Google Earth Engine analysis scripts
│   ├── gee_ch4_chesapeake.js  # Chesapeake methane monitoring
│   └── gee_no2_nyc.js         # NYC area NO2 analysis
├── src/                   # Python modules
│   └── config.py         # Geographic boundaries and constants
├── data/                 # CAFO locations and metadata (coming soon)
├── outputs/              # Generated maps and reports
└── docs/                 # Additional documentation
```

## 🤝 How to Contribute

We welcome contributions from:
- **Animal welfare advocates** - Help identify priority monitoring locations
- **Data scientists** - Improve emission detection algorithms
- **GIS specialists** - Enhance mapping and visualization
- **Policy experts** - Guide evidence requirements for campaigns
- **Developers** - Build web interfaces and automation tools

### Getting Started with Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-contribution`)
3. Commit your changes (`git commit -m 'Add new analysis for [region]'`)
4. Push to the branch (`git push origin feature/your-contribution`)
5. Open a Pull Request

### Priority Contributions Needed

- [ ] CAFO location database for different regions
- [ ] Web dashboard for non-technical users
- [ ] Automated report generation
- [ ] Integration with corporate supply chain data
- [ ] Mobile app for field verification
- [ ] Additional regional analyses (California, North Carolina, Iowa)

## 📈 Roadmap

**Phase 1 (Current)**: Chesapeake Bay baseline analysis
- ✅ Sentinel-5P methane tracking setup
- ✅ Monthly composite generation
- 🔄 CAFO source registry development
- 🔄 Seasonal pattern analysis

**Phase 2 (Q1 2025)**: Enhanced Detection
- [ ] EMIT plume integration for point-source detection
- [ ] Machine learning for anomaly detection
- [ ] Automated alerting system

**Phase 3 (Q2 2025)**: Modeling & Prediction
- [ ] IMI flux modeling implementation
- [ ] NeuralGCM dispersion patterns
- [ ] Health impact assessment tools

**Phase 4 (Q3 2025)**: Accessibility & Scale
- [ ] User-friendly web interface
- [ ] API for programmatic access
- [ ] National coverage expansion

## 🔬 Scientific Rigor

All analyses follow peer-reviewed methodologies:
- Methane quantification based on [Jacob et al. 2022](https://doi.org/10.5194/amt-15-3329-2022)
- Quality filtering using Sentinel-5P QA bands
- Uncertainty quantification included in all estimates
- Validation against ground-based measurements where available

## 📚 Resources

- [Sentinel-5P Data Guide](https://sentinel.esa.int/web/sentinel/missions/sentinel-5p)
- [Google Earth Engine Documentation](https://developers.google.com/earth-engine)
- [EPA FLIGHT Database](https://ghgdata.epa.gov/ghgp/main.do) - Cross-reference facility emissions
- [Environmental Working Group CAFO Map](https://www.ewg.org/interactive-maps/2020-iowa-factory-farms/)

## 🤲 Support & Community

- **Questions?** Open an issue on GitHub
- **Ideas?** Start a discussion in the Discussions tab
- **Updates**: Follow project progress at [RReverie.org](https://rreverie.org)
- **Contact**: [project email] for collaboration inquiries

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. All code and processed data are free to use for advocacy, research, and policy work.

## 🙏 Acknowledgments

- Sentinel-5P team for open satellite data
- Google Earth Engine for computational infrastructure
- Animal welfare organizations providing ground truth data
- Open Philanthropy and The Good Food Institute for advocacy frameworks

---

*"Making the invisible visible, one satellite pass at a time."*

**Together, we can hold factory farms accountable and advocate for a more compassionate, sustainable food system.** 🌱