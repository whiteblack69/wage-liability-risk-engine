"""
Wage Liability Risk Assessment Engine
Single-file Streamlit application for EOR termination liability modeling
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Wage Liability Risk Engine",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# COUNTRY RULES (Embedded)
# ============================================================================
COUNTRY_RULES = {
    "BR": {
        "name": "Brazil",
        "currency": "BRL",
        "notice_period": {"base_days": 30, "additional_days_per_year": 3, "max_days": 90},
        "severance": {"formula_type": "fgts_based", "fgts_penalty_percent": 40},
        "statutory_bonuses": {"13th_month": True, "vacation_bonus": 33.33},
        "legal_risk": "high"
    },
    "FR": {
        "name": "France",
        "currency": "EUR",
        "notice_period": {"tiers": [
            {"min_months": 0, "max_months": 6, "days": 0},
            {"min_months": 6, "max_months": 24, "days": 30},
            {"min_months": 24, "max_months": 999, "days": 60}
        ]},
        "severance": {"formula": "tiered", "min_tenure_months": 8},
        "statutory_bonuses": {"paid_leave_days_per_month": 2.5},
        "legal_risk": "medium"
    },
    "DE": {
        "name": "Germany",
        "currency": "EUR",
        "notice_period": {"tiers": [
            {"min_years": 0, "weeks": 4},
            {"min_years": 2, "weeks": 4},
            {"min_years": 5, "weeks": 8},
            {"min_years": 8, "weeks": 12},
            {"min_years": 10, "weeks": 16},
            {"min_years": 15, "weeks": 24},
            {"min_years": 20, "weeks": 28}
        ]},
        "severance": {"formula": "market_practice", "months_per_year": 0.5},
        "statutory_bonuses": {},
        "legal_risk": "medium"
    },
    "IN": {
        "name": "India",
        "currency": "INR",
        "notice_period": {"typical_days": 30, "senior_days": 90},
        "severance": {"formula": "gratuity", "min_tenure_years": 5},
        "statutory_bonuses": {"statutory_bonus_percent": 8.33, "salary_cap": 21000},
        "legal_risk": "low"
    },
    "PH": {
        "name": "Philippines",
        "currency": "PHP",
        "notice_period": {"standard_days": 30},
        "severance": {"formula": "one_month_per_year"},
        "statutory_bonuses": {"13th_month": True},
        "legal_risk": "medium"
    },
    "MX": {
        "name": "Mexico",
        "currency": "MXN",
        "notice_period": {"days": 0},
        "severance": {"constitutional_months": 3, "seniority_days_per_year": 12},
        "statutory_bonuses": {"aguinaldo_days": 15, "vacation_premium_percent": 25},
        "legal_risk": "high"
    },
    "GB": {
        "name": "United Kingdom",
        "currency": "GBP",
        "notice_period": {"tiers": [
            {"min_years": 0, "weeks": 1},
            {"min_years": 2, "weeks_per_year": 1, "max_weeks": 12}
        ]},
        "severance": {"formula": "statutory_redundancy", "weekly_cap": 700, "max_years": 20},
        "statutory_bonuses": {},
        "legal_risk": "medium"
    },
    "NL": {
        "name": "Netherlands",
        "currency": "EUR",
        "notice_period": {"tiers": [
            {"min_years": 0, "months": 1},
            {"min_years": 5, "months": 2},
            {"min_years": 10, "months": 3},
            {"min_years": 15, "months": 4}
        ]},
        "severance": {"formula": "transition_payment", "months_per_year": 0.33, "max_eur": 94000},
        "statutory_bonuses": {"holiday_allowance_percent": 8},
        "legal_risk": "medium"
    },
    "SG": {
        "name": "Singapore",
        "currency": "SGD",
        "notice_period": {"tiers": [
            {"tenure": "< 26 weeks", "days": 1},
            {"tenure": "26w - 2y", "weeks": 1},
            {"tenure": "2y - 5y", "weeks": 2},
            {"tenure": "5y+", "weeks": 4}
        ]},
        "severance": {"formula": "market_practice", "weeks_per_year": 2, "min_tenure_years": 2},
        "statutory_bonuses": {},
        "legal_risk": "low"
    },
    "AU": {
        "name": "Australia",
        "currency": "AUD",
        "notice_period": {"tiers": [
            {"min_years": 1, "weeks": 1},
            {"min_years": 3, "weeks": 2},
            {"min_years": 5, "weeks": 3},
            {"min_years": 999, "weeks": 4}
        ], "over_45_extra_week": True},
        "severance": {"formula": "nse_scale", "scale": [4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16]},
        "statutory_bonuses": {},
        "legal_risk": "medium"
    }
}

# FX Rates (fallback - updates can be added via API later)
FX_RATES = {
    "BRL": 5.85, "EUR": 0.92, "INR": 83.50, "PHP": 56.80,
    "MXN": 17.25, "GBP": 0.79, "SGD": 1.34, "AUD": 1.55, "USD": 1.0
}

FX_VOLATILITY = {
    "BRL": 0.18, "EUR": 0.04, "INR": 0.08, "PHP": 0.06,
    "MXN": 0.14, "GBP": 0.05, "SGD": 0.03, "AUD": 0.07
}

# ============================================================================
# SAMPLE DATA
# ============================================================================
SAMPLE_EMPLOYEES = [
    {"employee_id": "EMP001", "name": "Maria Santos", "country_code": "BR", "start_date": "2021-03-15", "monthly_salary_local": 18500, "currency": "BRL", "department": "Engineering", "job_level": "senior", "age": 34},
    {"employee_id": "EMP002", "name": "Jean-Pierre Dubois", "country_code": "FR", "start_date": "2019-06-01", "monthly_salary_local": 6200, "currency": "EUR", "department": "Product", "job_level": "lead", "age": 42},
    {"employee_id": "EMP003", "name": "Hans Mueller", "country_code": "DE", "start_date": "2018-01-10", "monthly_salary_local": 7500, "currency": "EUR", "department": "Engineering", "job_level": "principal", "age": 51},
    {"employee_id": "EMP004", "name": "Priya Sharma", "country_code": "IN", "start_date": "2020-08-20", "monthly_salary_local": 185000, "currency": "INR", "department": "Operations", "job_level": "manager", "age": 38},
    {"employee_id": "EMP005", "name": "Miguel Rodriguez", "country_code": "MX", "start_date": "2022-05-01", "monthly_salary_local": 65000, "currency": "MXN", "department": "Sales", "job_level": "senior", "age": 29},
    {"employee_id": "EMP006", "name": "Anna Garcia", "country_code": "PH", "start_date": "2021-11-15", "monthly_salary_local": 95000, "currency": "PHP", "department": "Customer Success", "job_level": "specialist", "age": 27},
    {"employee_id": "EMP007", "name": "James Wilson", "country_code": "GB", "start_date": "2017-09-01", "monthly_salary_local": 5800, "currency": "GBP", "department": "Finance", "job_level": "director", "age": 48},
    {"employee_id": "EMP008", "name": "Sophie van der Berg", "country_code": "NL", "start_date": "2020-02-14", "monthly_salary_local": 5500, "currency": "EUR", "department": "HR", "job_level": "manager", "age": 35},
    {"employee_id": "EMP009", "name": "David Chen", "country_code": "SG", "start_date": "2019-04-01", "monthly_salary_local": 9500, "currency": "SGD", "department": "Engineering", "job_level": "staff", "age": 31},
    {"employee_id": "EMP010", "name": "Emma Thompson", "country_code": "AU", "start_date": "2016-07-22", "monthly_salary_local": 11500, "currency": "AUD", "department": "Marketing", "job_level": "head", "age": 44},
    {"employee_id": "EMP011", "name": "Lucas Oliveira", "country_code": "BR", "start_date": "2023-01-09", "monthly_salary_local": 12000, "currency": "BRL", "department": "Engineering", "job_level": "mid", "age": 26},
    {"employee_id": "EMP012", "name": "Marie Lefevre", "country_code": "FR", "start_date": "2022-11-01", "monthly_salary_local": 4800, "currency": "EUR", "department": "Design", "job_level": "senior", "age": 33},
    {"employee_id": "EMP013", "name": "Thomas Schmidt", "country_code": "DE", "start_date": "2020-06-15", "monthly_salary_local": 5200, "currency": "EUR", "department": "Support", "job_level": "specialist", "age": 28},
    {"employee_id": "EMP014", "name": "Amit Patel", "country_code": "IN", "start_date": "2018-03-01", "monthly_salary_local": 320000, "currency": "INR", "department": "Engineering", "job_level": "principal", "age": 45},
    {"employee_id": "EMP015", "name": "Carlos Hernandez", "country_code": "MX", "start_date": "2021-08-10", "monthly_salary_local": 48000, "currency": "MXN", "department": "Operations", "job_level": "coordinator", "age": 31},
    {"employee_id": "EMP016", "name": "Grace Reyes", "country_code": "PH", "start_date": "2020-01-20", "monthly_salary_local": 120000, "currency": "PHP", "department": "Finance", "job_level": "senior", "age": 36},
    {"employee_id": "EMP017", "name": "Oliver Brown", "country_code": "GB", "start_date": "2023-03-15", "monthly_salary_local": 4200, "currency": "GBP", "department": "Engineering", "job_level": "mid", "age": 25},
    {"employee_id": "EMP018", "name": "Daan de Vries", "country_code": "NL", "start_date": "2018-09-01", "monthly_salary_local": 6800, "currency": "EUR", "department": "Product", "job_level": "senior", "age": 39},
    {"employee_id": "EMP019", "name": "Rachel Tan", "country_code": "SG", "start_date": "2022-07-01", "monthly_salary_local": 7200, "currency": "SGD", "department": "Sales", "job_level": "manager", "age": 32},
    {"employee_id": "EMP020", "name": "Michael Roberts", "country_code": "AU", "start_date": "2019-11-11", "monthly_salary_local": 9800, "currency": "AUD", "department": "Engineering", "job_level": "senior", "age": 37},
    {"employee_id": "EMP021", "name": "Fernanda Costa", "country_code": "BR", "start_date": "2017-05-20", "monthly_salary_local": 25000, "currency": "BRL", "department": "Product", "job_level": "director", "age": 41},
    {"employee_id": "EMP022", "name": "Pierre Martin", "country_code": "FR", "start_date": "2016-12-01", "monthly_salary_local": 8500, "currency": "EUR", "department": "Engineering", "job_level": "staff", "age": 52},
    {"employee_id": "EMP023", "name": "Julia Becker", "country_code": "DE", "start_date": "2021-04-01", "monthly_salary_local": 4800, "currency": "EUR", "department": "Marketing", "job_level": "specialist", "age": 30},
    {"employee_id": "EMP024", "name": "Ravi Kumar", "country_code": "IN", "start_date": "2019-10-15", "monthly_salary_local": 210000, "currency": "INR", "department": "Product", "job_level": "lead", "age": 40},
    {"employee_id": "EMP025", "name": "Isabella Morales", "country_code": "MX", "start_date": "2020-03-01", "monthly_salary_local": 72000, "currency": "MXN", "department": "Engineering", "job_level": "senior", "age": 34},
]

# ============================================================================
# CALCULATION ENGINE
# ============================================================================

def calculate_tenure(start_date_str: str) -> Tuple[int, int, float]:
    """Calculate tenure in days, months, and years"""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = date.today()
    days = (today - start_date).days
    months = days // 30
    years = days / 365.25
    return days, months, years


def convert_to_usd(amount: float, currency: str) -> float:
    """Convert local currency to USD"""
    rate = FX_RATES.get(currency, 1.0)
    return amount / rate if rate != 0 else amount


def get_volatility_rating(currency: str) -> str:
    """Get volatility rating for currency"""
    vol = FX_VOLATILITY.get(currency, 0.10)
    if vol >= 0.12:
        return "High"
    elif vol >= 0.06:
        return "Medium"
    return "Low"


def calculate_notice_period(employee: dict, country: dict) -> Tuple[int, float]:
    """Calculate notice period in days and cost"""
    _, tenure_months, tenure_years = calculate_tenure(employee["start_date"])
    daily_rate = employee["monthly_salary_local"] / 22
    notice_config = country.get("notice_period", {})
    notice_days = 0
    
    if "base_days" in notice_config:
        # Brazil style
        base = notice_config.get("base_days", 30)
        per_year = notice_config.get("additional_days_per_year", 0)
        max_days = notice_config.get("max_days", 90)
        notice_days = min(base + int(tenure_years * per_year), max_days)
    elif "tiers" in notice_config:
        for tier in notice_config["tiers"]:
            if "min_months" in tier:
                if tenure_months >= tier.get("min_months", 0):
                    notice_days = tier.get("days", 0)
            elif "min_years" in tier:
                if tenure_years >= tier.get("min_years", 0):
                    if "weeks" in tier:
                        notice_days = tier["weeks"] * 7
                    elif "weeks_per_year" in tier:
                        max_weeks = tier.get("max_weeks", 12)
                        notice_days = min(int(tenure_years) * tier["weeks_per_year"], max_weeks) * 7
                    elif "months" in tier:
                        notice_days = tier["months"] * 30
    elif "typical_days" in notice_config:
        notice_days = notice_config["typical_days"]
        if employee.get("job_level") in ["director", "head", "principal", "lead"]:
            notice_days = notice_config.get("senior_days", notice_days)
    elif "standard_days" in notice_config:
        notice_days = notice_config["standard_days"]
    elif "days" in notice_config:
        notice_days = notice_config["days"]
    
    return notice_days, notice_days * daily_rate


def calculate_severance(employee: dict, country: dict) -> float:
    """Calculate severance pay"""
    _, tenure_months, tenure_years = calculate_tenure(employee["start_date"])
    monthly_salary = employee["monthly_salary_local"]
    sev_config = country.get("severance", {})
    formula = sev_config.get("formula", sev_config.get("formula_type", ""))
    
    # Check minimum tenure
    min_months = sev_config.get("min_tenure_months", 0)
    min_years = sev_config.get("min_tenure_years", 0)
    if tenure_months < min_months or tenure_years < min_years:
        return 0.0
    
    if formula == "fgts_based":
        # Brazil: 40% penalty on FGTS balance
        fgts_balance = monthly_salary * 0.08 * 12 * tenure_years
        return fgts_balance * (sev_config.get("fgts_penalty_percent", 40) / 100)
    
    elif formula == "tiered":
        # France: 1/4 month per year (first 10), 1/3 after
        if tenure_years <= 10:
            return 0.25 * monthly_salary * tenure_years
        return (0.25 * monthly_salary * 10) + (0.33 * monthly_salary * (tenure_years - 10))
    
    elif formula == "market_practice":
        # Germany/Singapore: X months per year
        months_per_year = sev_config.get("months_per_year", 0.5)
        weeks_per_year = sev_config.get("weeks_per_year", 0)
        if weeks_per_year:
            return (monthly_salary / 4.33) * weeks_per_year * tenure_years
        return months_per_year * monthly_salary * tenure_years
    
    elif formula == "gratuity":
        # India: 15 days per year after 5 years
        if tenure_years >= 5:
            daily_rate = monthly_salary / 26
            return 15 * daily_rate * tenure_years
        return 0
    
    elif formula == "one_month_per_year":
        # Philippines
        return monthly_salary * max(1, tenure_years)
    
    elif "constitutional_months" in sev_config:
        # Mexico: 3 months + seniority premium
        base = sev_config["constitutional_months"] * monthly_salary
        seniority = (monthly_salary / 30) * sev_config.get("seniority_days_per_year", 12) * tenure_years
        return base + seniority
    
    elif formula == "statutory_redundancy":
        # UK
        weekly_pay = min(monthly_salary / 4.33, sev_config.get("weekly_cap", 700))
        years_counted = min(tenure_years, sev_config.get("max_years", 20))
        return weekly_pay * years_counted
    
    elif formula == "transition_payment":
        # Netherlands
        severance = (sev_config.get("months_per_year", 0.33)) * monthly_salary * tenure_years
        return min(severance, sev_config.get("max_eur", 94000))
    
    elif formula == "nse_scale":
        # Australia
        scale = sev_config.get("scale", [])
        if tenure_years >= 1 and scale:
            year_index = min(int(tenure_years) - 1, len(scale) - 1)
            weeks = scale[year_index]
            return (monthly_salary / 4.33) * weeks
    
    return 0


def calculate_statutory_bonuses(employee: dict, country: dict) -> float:
    """Calculate prorated statutory bonus accruals"""
    monthly_salary = employee["monthly_salary_local"]
    bonuses = country.get("statutory_bonuses", {})
    
    today = date.today()
    year_start = date(today.year, 1, 1)
    year_progress = (today - year_start).days / 365
    
    total = 0.0
    
    if bonuses.get("13th_month"):
        total += monthly_salary * year_progress
    
    if "aguinaldo_days" in bonuses:
        daily_rate = monthly_salary / 30
        total += daily_rate * bonuses["aguinaldo_days"] * year_progress
    
    if "holiday_allowance_percent" in bonuses:
        annual = monthly_salary * 12 * (bonuses["holiday_allowance_percent"] / 100)
        total += annual * year_progress
    
    if "statutory_bonus_percent" in bonuses:
        cap = bonuses.get("salary_cap", monthly_salary)
        capped = min(monthly_salary, cap)
        total += capped * 12 * (bonuses["statutory_bonus_percent"] / 100) * year_progress
    
    if "vacation_bonus" in bonuses:
        total += monthly_salary * (bonuses["vacation_bonus"] / 100) * year_progress
    
    return total


def calculate_vacation_accrual(employee: dict, country_code: str) -> float:
    """Calculate accrued vacation payout"""
    monthly_salary = employee["monthly_salary_local"]
    today = date.today()
    year_start = date(today.year, 1, 1)
    days_in_year = (today - year_start).days
    
    accrual_rates = {
        "BR": 30, "FR": 25, "DE": 20, "IN": 21, "PH": 5,
        "MX": 12, "GB": 28, "NL": 20, "SG": 14, "AU": 20
    }
    
    annual_days = accrual_rates.get(country_code, 20)
    days_accrued = (annual_days / 365) * days_in_year
    daily_rate = monthly_salary / 22
    
    return days_accrued * daily_rate


def calculate_employee_liability(employee: dict) -> dict:
    """Calculate full liability for an employee"""
    country_code = employee["country_code"]
    country = COUNTRY_RULES.get(country_code, {})
    
    notice_days, notice_cost = calculate_notice_period(employee, country)
    severance = calculate_severance(employee, country)
    bonuses = calculate_statutory_bonuses(employee, country)
    vacation = calculate_vacation_accrual(employee, country_code)
    
    total_local = notice_cost + severance + bonuses + vacation
    total_usd = convert_to_usd(total_local, employee["currency"])
    
    # Risk score calculation
    liability_score = min(total_usd / 100000, 1.0) * 35
    fx_score = FX_VOLATILITY.get(employee["currency"], 0.10) / 0.20 * 25
    legal_scores = {"high": 0.9, "medium": 0.5, "low": 0.2}
    legal_score = legal_scores.get(country.get("legal_risk", "medium"), 0.5) * 15
    risk_score = min(liability_score + fx_score + legal_score + 10, 100)
    
    return {
        "employee_id": employee["employee_id"],
        "name": employee["name"],
        "country_code": country_code,
        "country_name": country.get("name", country_code),
        "currency": employee["currency"],
        "notice_days": notice_days,
        "notice_cost": notice_cost,
        "severance": severance,
        "bonuses": bonuses,
        "vacation": vacation,
        "total_local": total_local,
        "total_usd": total_usd,
        "risk_score": risk_score,
        "fx_volatility": get_volatility_rating(employee["currency"]),
        "legal_risk": country.get("legal_risk", "medium").title(),
        "tenure_years": calculate_tenure(employee["start_date"])[2]
    }


def calculate_portfolio(employees: List[dict]) -> dict:
    """Calculate liability for entire portfolio"""
    results = [calculate_employee_liability(emp) for emp in employees]
    
    total_liability = sum(r["total_usd"] for r in results)
    
    # Aggregate by country
    by_country = {}
    for r in results:
        code = r["country_code"]
        if code not in by_country:
            by_country[code] = {
                "country_name": r["country_name"],
                "employee_count": 0,
                "total_usd": 0,
                "employees": []
            }
        by_country[code]["employee_count"] += 1
        by_country[code]["total_usd"] += r["total_usd"]
        by_country[code]["employees"].append(r["employee_id"])
    
    # Add percentages
    for code, data in by_country.items():
        data["percent"] = (data["total_usd"] / total_liability * 100) if total_liability > 0 else 0
    
    # Generate alerts
    alerts = []
    for code, data in by_country.items():
        if data["percent"] > 30:
            alerts.append(f"🚨 CONCENTRATION: {data['country_name']} holds {data['percent']:.1f}% of total liability")
    
    for r in results:
        if r["total_usd"] > 100000:
            alerts.append(f"⚠️ HIGH EXPOSURE: {r['name']} liability ${r['total_usd']:,.0f}")
        if FX_VOLATILITY.get(r["currency"], 0) > 0.15:
            alerts.append(f"💱 FX RISK: {r['name']} exposed to high {r['currency']} volatility")
    
    return {
        "employees": results,
        "by_country": by_country,
        "total_liability_usd": total_liability,
        "total_employees": len(results),
        "high_risk_count": sum(1 for r in results if r["risk_score"] > 70),
        "avg_risk_score": sum(r["risk_score"] for r in results) / len(results) if results else 0,
        "alerts": alerts
    }


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_metric_card(label: str, value: str, delta: str = None):
    """Render a styled metric"""
    st.metric(label, value, delta)


def create_country_treemap(by_country: dict):
    """Create country liability treemap"""
    data = [{
        "Country": info["country_name"],
        "Liability (USD)": info["total_usd"],
        "Employees": info["employee_count"],
        "% of Total": info["percent"]
    } for code, info in by_country.items()]
    
    df = pd.DataFrame(data)
    
    fig = px.treemap(
        df, path=["Country"], values="Liability (USD)",
        color="% of Total", color_continuous_scale="RdYlGn_r",
        hover_data=["Employees", "% of Total"],
        title="Liability Distribution by Country"
    )
    fig.update_layout(height=400, margin=dict(t=50, l=25, r=25, b=25))
    return fig


def create_risk_histogram(employees: list):
    """Create risk score distribution"""
    scores = [e["risk_score"] for e in employees]
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=scores, nbinsx=15, marker_color="#6366f1", opacity=0.8))
    fig.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="High Risk")
    fig.add_vline(x=40, line_dash="dash", line_color="orange", annotation_text="Medium")
    
    fig.update_layout(
        title="Risk Score Distribution",
        xaxis_title="Risk Score", yaxis_title="Count",
        height=350, showlegend=False
    )
    return fig


def create_fx_chart():
    """Create FX volatility chart"""
    data = [{
        "Currency": curr,
        "Volatility (%)": vol * 100,
        "Rating": get_volatility_rating(curr)
    } for curr, vol in FX_VOLATILITY.items()]
    
    df = pd.DataFrame(data).sort_values("Volatility (%)", ascending=True)
    colors = df["Rating"].map({"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"})
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Currency"], x=df["Volatility (%)"],
        orientation="h", marker_color=colors,
        text=df["Volatility (%)"].round(1).astype(str) + "%",
        textposition="outside"
    ))
    fig.add_vline(x=15, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
    
    fig.update_layout(
        title="30-Day Currency Volatility",
        xaxis_title="Volatility (%)", yaxis_title="",
        height=350, margin=dict(l=80)
    )
    return fig


def create_liability_pie(employees: list):
    """Create liability breakdown pie chart"""
    totals = {
        "Notice Period": sum(e["notice_cost"] for e in employees),
        "Severance": sum(e["severance"] for e in employees),
        "Statutory Bonuses": sum(e["bonuses"] for e in employees),
        "Vacation Accrual": sum(e["vacation"] for e in employees)
    }
    
    # Convert to USD for comparison
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=list(totals.keys()),
        values=list(totals.values()),
        hole=0.4,
        marker_colors=["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd"]
    ))
    
    fig.update_layout(
        title="Liability Components (Local Currency)",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown("# 💰 Wage Liability Risk Engine")
    st.markdown("*Real-time EOR termination liability monitoring across 10 countries*")
    st.markdown("---")
    
    # Calculate portfolio
    portfolio = calculate_portfolio(SAMPLE_EMPLOYEES)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Employees", portfolio["total_employees"])
        st.metric("Total Liability", f"${portfolio['total_liability_usd']:,.0f}")
        st.metric("Avg Risk Score", f"{portfolio['avg_risk_score']:.1f}/100")
        st.metric("High Risk Count", portfolio["high_risk_count"])
        
        st.markdown("---")
        st.markdown("### 🌍 Countries Covered")
        for code, info in portfolio["by_country"].items():
            st.write(f"**{info['country_name']}**: {info['employee_count']} employees")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This tool calculates termination liability using country-specific:
        - Notice period rules
        - Severance formulas
        - Statutory bonuses
        - FX exposure
        
        Built for EOR portfolio demonstration.
        """)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "👥 Employees", "🌍 Countries", "📋 Rules"])
    
    # TAB 1: Dashboard
    with tab1:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Liability", f"${portfolio['total_liability_usd']:,.0f}")
        with col2:
            st.metric("Employees", portfolio["total_employees"])
        with col3:
            st.metric("High Risk", portfolio["high_risk_count"])
        with col4:
            st.metric("Avg Risk Score", f"{portfolio['avg_risk_score']:.1f}")
        
        # Alerts
        if portfolio["alerts"]:
            st.markdown("### 🚨 Active Alerts")
            for alert in portfolio["alerts"]:
                if "CONCENTRATION" in alert or "HIGH" in alert:
                    st.error(alert)
                elif "FX" in alert:
                    st.warning(alert)
                else:
                    st.info(alert)
        else:
            st.success("✅ All thresholds within normal range")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_country_treemap(portfolio["by_country"]), use_container_width=True)
        with col2:
            st.plotly_chart(create_risk_histogram(portfolio["employees"]), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_fx_chart(), use_container_width=True)
        with col2:
            st.plotly_chart(create_liability_pie(portfolio["employees"]), use_container_width=True)
    
    # TAB 2: Employee Analysis
    with tab2:
        st.markdown("### 👥 Employee Risk Analysis")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            countries = ["All"] + list(set(e["country_name"] for e in portfolio["employees"]))
            selected_country = st.selectbox("Filter by Country", countries)
        with col2:
            risk_filter = st.selectbox("Filter by Risk", ["All", "High (>70)", "Medium (40-70)", "Low (<40)"])
        with col3:
            sort_by = st.selectbox("Sort by", ["Risk Score ↓", "Liability ↓", "Name"])
        
        # Filter and sort
        filtered = portfolio["employees"]
        if selected_country != "All":
            filtered = [e for e in filtered if e["country_name"] == selected_country]
        
        if risk_filter == "High (>70)":
            filtered = [e for e in filtered if e["risk_score"] > 70]
        elif risk_filter == "Medium (40-70)":
            filtered = [e for e in filtered if 40 <= e["risk_score"] <= 70]
        elif risk_filter == "Low (<40)":
            filtered = [e for e in filtered if e["risk_score"] < 40]
        
        if sort_by == "Risk Score ↓":
            filtered = sorted(filtered, key=lambda x: x["risk_score"], reverse=True)
        elif sort_by == "Liability ↓":
            filtered = sorted(filtered, key=lambda x: x["total_usd"], reverse=True)
        else:
            filtered = sorted(filtered, key=lambda x: x["name"])
        
        st.markdown(f"*Showing {len(filtered)} employees*")
        
        # Table
        df = pd.DataFrame([{
            "ID": e["employee_id"],
            "Name": e["name"],
            "Country": e["country_name"],
            "Tenure (yrs)": f"{e['tenure_years']:.1f}",
            "Liability (USD)": f"${e['total_usd']:,.0f}",
            "Risk Score": f"{e['risk_score']:.0f}",
            "FX Risk": e["fx_volatility"],
            "Legal Risk": e["legal_risk"]
        } for e in filtered])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Detail view
        st.markdown("### 📋 Employee Detail")
        emp_options = [f"{e['employee_id']} - {e['name']}" for e in filtered]
        if emp_options:
            selected = st.selectbox("Select employee", emp_options)
            emp_id = selected.split(" - ")[0]
            emp = next((e for e in filtered if e["employee_id"] == emp_id), None)
            
            if emp:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Liability Breakdown**")
                    st.write(f"- Notice ({emp['notice_days']} days): {emp['notice_cost']:,.0f} {emp['currency']}")
                    st.write(f"- Severance: {emp['severance']:,.0f} {emp['currency']}")
                    st.write(f"- Statutory Bonuses: {emp['bonuses']:,.0f} {emp['currency']}")
                    st.write(f"- Vacation Accrual: {emp['vacation']:,.0f} {emp['currency']}")
                    st.write(f"- **Total (Local):** {emp['total_local']:,.0f} {emp['currency']}")
                    st.write(f"- **Total (USD):** ${emp['total_usd']:,.0f}")
                
                with col2:
                    st.markdown("**Risk Factors**")
                    st.write(f"- Risk Score: **{emp['risk_score']:.0f}/100**")
                    st.write(f"- FX Volatility: **{emp['fx_volatility']}**")
                    st.write(f"- Legal Risk: **{emp['legal_risk']}**")
                    st.write(f"- Tenure: **{emp['tenure_years']:.1f} years**")
    
    # TAB 3: Country Details
    with tab3:
        st.markdown("### 🌍 Country Analysis")
        
        selected_code = st.selectbox(
            "Select Country",
            list(COUNTRY_RULES.keys()),
            format_func=lambda x: COUNTRY_RULES[x]["name"]
        )
        
        country = COUNTRY_RULES[selected_code]
        country_data = portfolio["by_country"].get(selected_code, {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Employees", country_data.get("employee_count", 0))
        with col2:
            st.metric("Total Liability", f"${country_data.get('total_usd', 0):,.0f}")
        with col3:
            st.metric("% of Portfolio", f"{country_data.get('percent', 0):.1f}%")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Notice Period Rules**")
            st.json(country.get("notice_period", {}))
        with col2:
            st.markdown("**Severance Rules**")
            st.json(country.get("severance", {}))
        
        st.markdown("**Statutory Bonuses**")
        st.json(country.get("statutory_bonuses", {}))
        
        st.markdown(f"**Legal Risk Rating:** {country.get('legal_risk', 'medium').title()}")
    
    # TAB 4: Rules Reference
    with tab4:
        st.markdown("### 📋 Country Rules Reference")
        st.markdown("Severance and notice period rules by country:")
        
        rules_summary = []
        for code, country in COUNTRY_RULES.items():
            rules_summary.append({
                "Country": country["name"],
                "Currency": country["currency"],
                "Legal Risk": country.get("legal_risk", "medium").title(),
                "Has 13th Month": "✅" if country.get("statutory_bonuses", {}).get("13th_month") else "❌"
            })
        
        st.dataframe(pd.DataFrame(rules_summary), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 💱 FX Rates & Volatility")
        
        fx_df = pd.DataFrame([{
            "Currency": curr,
            "Rate (per USD)": f"{rate:.2f}",
            "30-Day Volatility": f"{FX_VOLATILITY.get(curr, 0)*100:.1f}%",
            "Rating": get_volatility_rating(curr)
        } for curr, rate in FX_RATES.items() if curr != "USD"])
        
        st.dataframe(fx_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
