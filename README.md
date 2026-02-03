# 💰 Wage Liability Risk Engine

Real-time EOR termination liability monitoring across 10 countries.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)

## 🎯 What This Does

- **Calculates termination liability** for employees across 10 countries (Brazil, France, Germany, India, Philippines, Mexico, UK, Netherlands, Singapore, Australia)
- **Models severance, notice periods, and statutory bonuses** using country-specific labor law formulas
- **Tracks FX exposure** with currency volatility ratings
- **Identifies concentration risk** at the portfolio level
- **Generates alerts** when thresholds are breached



## 📊 Features

| Tab | Description |
|-----|-------------|
| **Dashboard** | Portfolio overview with liability treemap, risk distribution, FX volatility, and active alerts |
| **Employees** | Individual employee risk analysis with filtering and sorting |
| **Countries** | Country-specific rules and liability breakdown |
| **Rules** | Reference table of all country rules and FX rates |

## 🧮 Calculation Logic

### Notice Period
- **Brazil**: 30 days + 3 days per year of service (max 90)
- **France**: Tiered by tenure (0-6mo: none, 6mo-2yr: 1mo, 2yr+: 2mo)
- **Germany**: 4 weeks to 28 weeks based on tenure
- **Mexico**: No notice (but 3 months constitutional indemnity)

### Severance
- **Brazil**: 40% penalty on FGTS balance
- **France**: 1/4 month per year (first 10), 1/3 after
- **Germany**: 0.5 months per year (market practice)
- **India**: Gratuity after 5 years (15 days per year)
- **Mexico**: 3 months + 12 days per year seniority premium
- **Netherlands**: Transitievergoeding (1/3 month per year, capped at €94k)

### Risk Score
Composite weighted score (0-100):
- Liability magnitude: 35%
- FX volatility: 25%
- Legal risk rating: 15%
- Base risk: 25%

## 📁 Project Structure

```
wage-liability-app/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml       # Theme configuration
└── README.md             # This file
```




---

Built by [Malik Ali] | [LinkedIn](https://linkedin.com/in/yourprofile) |
