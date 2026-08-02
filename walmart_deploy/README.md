# Walmart Store Sales Forecasting — Deployment

Streamlit app forecasting the next 12 weeks of weekly sales for all 45 Walmart stores,
using SARIMAX(1,1,1)(1,1,1,52).

## Files
- `app.py` — the Streamlit app (3 pages: Store Forecast, Model Performance Overview, About)
- `requirements.txt` — dependencies for Streamlit Cloud
- `walmart_cleaned.csv` — cleaned historical data (Date parsed, sorted)
- `forecast_next_12_weeks.csv` — precomputed 12-week-ahead forecast, all 45 stores
- `model_evaluation_metrics.csv` — MAE/RMSE/MAPE per store (last 12 weeks held out)
- `actual_vs_predicted_holdout.csv` — actual vs predicted values for the held-out test weeks
- `precompute.py` — script that generated the four CSVs above (rerun this if you get new data)

## Why precomputed CSVs instead of fitting SARIMAX live in the app
Fitting a weekly-seasonal SARIMAX (period=52) for 45 stores takes ~7 minutes total.
Doing that on every Streamlit rerun would make the app unusably slow and would time
out on Streamlit Community Cloud's free tier. Forecasts are computed once offline via
`precompute.py`, and the app just loads and displays the results — instant load,
`@st.cache_data` keeps it that way across sessions.

## Deploy to Streamlit Community Cloud
1. Push this whole folder to a GitHub repo (e.g. a new repo `walmart-sales-forecast`
   under github.com/sidducv0528).
2. Go to https://share.streamlit.io → "New app" → pick the repo → main file: `app.py`.
3. Deploy. First load takes ~30-60s, then it's fast.

## Refreshing the forecast with new data
Replace `Walmart_DataSet.csv`, rerun `python3 precompute.py` (~7 min), commit the four
regenerated CSVs, push. The app picks up new data automatically on next load.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```
