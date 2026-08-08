# Superstore Business Intelligence

A multi-page Streamlit application for descriptive, diagnostic, predictive,
forecasting, and AI-assisted analysis of the Sample Superstore dataset.

## Data and analysis workflow

1. `utils/data_loader.py` loads and caches the CSV.
2. `utils/data_cleaning.py` standardizes and validates transaction fields.
3. `utils/feature_engineering.py` derives dates, margins, discount bands, and
   shipping metrics.
4. `utils/filters.py` applies the shared dashboard filters.
5. `utils/analytics.py` produces trusted, reusable evidence tables.
6. `utils/insight_engine.py` turns deterministic evidence into governed reports.
7. `utils/ai_analyst.py` answers factual questions with Python and routes only
   interpretive questions to Gemini with Python-calculated evidence.

The AI model does not calculate business figures. It interprets evidence built
by Python and must report material data limitations.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .streamlit\secrets.example.toml .streamlit\secrets.toml
streamlit run app.py
```

Add a valid key to `.streamlit/secrets.toml` to enable Gemini-assisted answers.
Python-based answers and dashboards do not require an API key.

## Verification

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py utils pages
```

## Inventory-analysis limitation

The source data contains historical transactions, not inventory operations.
Inventory rankings therefore combine demand, repeat orders, recent demand, and
profit as a transparent proxy. Final allocations require on-hand stock,
stockouts, lead times, purchase and carrying costs, and service-level targets.
