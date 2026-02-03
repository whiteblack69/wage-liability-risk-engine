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

## 🖥️ Live Demo

[**View Live App →**](https://your-app-name.streamlit.app)

## 🚀 Deployment Guide

### Option 1: Streamlit Cloud (Recommended - Free)

**Step 1: Create GitHub Repository**

1. Go to [github.com](https://github.com) and sign in
2. Click **New Repository** (green button)
3. Name it `wage-liability-risk-engine`
4. Set to **Public**
5. Click **Create Repository**

**Step 2: Upload Files**

1. On your new repo page, click **"uploading an existing file"**
2. Drag and drop these files:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml` (create folder first or upload separately)
3. Click **Commit changes**

**Step 3: Deploy to Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **Sign in with GitHub**
3. Click **New app**
4. Select your repository: `your-username/wage-liability-risk-engine`
5. Branch: `main`
6. Main file path: `app.py`
7. Click **Deploy!**

**Step 4: Wait ~2 minutes**

Your app will be live at: `https://your-app-name.streamlit.app`

---

### Option 2: Local Development

```bash
# Clone the repo
git clone https://github.com/your-username/wage-liability-risk-engine.git
cd wage-liability-risk-engine

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Open http://localhost:8501

---

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
