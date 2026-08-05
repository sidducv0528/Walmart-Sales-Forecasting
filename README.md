<div align="center">

<img src="assets/banner/walmart-sales-forecasting-banner.png" alt="Walmart Sales Forecasting — Data Analysis + Machine Learning, predicting next 12 weeks of sales" width="100%">

# 🛒 Walmart Sales Forecasting

**Predicting the next 12 weeks of sales for 45 Walmart stores with seasonal time-series modeling — deployed as a live, interactive dashboard.**

[![Live App](https://img.shields.io/badge/🚀_Live_App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://walmart-sales-forecasting-stores.streamlit.app/)
[![Video Walkthrough](https://img.shields.io/badge/▶_Watch_Demo-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/UXW4FTEN994)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Statsmodels](https://img.shields.io/badge/statsmodels-SARIMA-2C7FB8)
![Pandas](https://img.shields.io/badge/pandas-data%20wrangling-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-visualizations-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/status-deployed-brightgreen)

</div>

> First load can take a few seconds — Streamlit Community Cloud's free tier
> spins containers down after inactivity.

---

## 📖 Table of Contents

- [Overview](#-project-overview)
- [Key Insights](#-key-business-insights-from-eda)
- [Forecasting Approach](#-forecasting-approach)
- [Results](#-results-across-all-45-stores-12-week-holdout)
- [Dashboard Pages](#️-dashboard-pages)
- [Preview](#-preview)
- [Dataset](#-dataset)
- [Repository Structure](#️-repository-structure)
- [Why Precomputed Forecasts](#️-why-precomputed-forecasts)
- [Tech Stack](#️-tech-stack)
- [Run Locally](#️-run-locally)
- [Documentation](#-documentation)
- [Contact](#-contact)

---

## 📌 Project Overview

Walmart operates 45 stores across different regions, each with its own sales
pattern, holiday sensitivity, and economic environment. This project answers
two questions for every single store:

1. **What drove sales historically?** — an exploratory analysis of holiday
   effects, seasonality, temperature, CPI, fuel price, and unemployment.
2. **What will sales look like in the next 12 weeks?** — a per-store time
   series forecast, rigorously validated against a held-out test window
   before being trusted for the actual future.

The end result is deployed as a **6-page interactive dashboard**, so the
analysis isn't locked inside a notebook — anyone can pick a store and see
its forecast, accuracy, and business context in seconds.

## 🧠 Key Business Insights (from EDA)

| Insight | What it means for the business |
|---|---|
| 📈 **Seasonality dominates.** Sales peak sharply in Nov–Dec around Thanksgiving and Christmas. | Inventory and staffing should ramp up ahead of the holiday season. |
| 📉 **Macro indicators are weak predictors overall.** Unemployment, CPI, and temperature each correlate weakly with sales chain-wide. | A handful of stores *are* noticeably more sensitive to unemployment or CPI — planning should be store-specific, not one-size-fits-all. |
| ✅ **Outliers were kept, not removed.** High-sales spikes line up with holiday weeks — real demand, not data errors. | Removing them would have erased the exact seasonal signal the model relies on. |
| 🏪 **Performance varies widely store to store.** | Confirms the need for 45 independent models rather than one global forecast. |

## 🔮 Forecasting Approach

Each store's weekly sales are modeled **independently** with:

```
SARIMAX(order=(1,1,1), seasonal_order=(1,1,1,52))
```

**Why 52 as the seasonal period?** Weekly data with a yearly cycle needs a
52-week seasonal term to capture the holiday-driven annual pattern.

**Why SARIMA and not true SARIMAX?** The dataset provides exogenous features
(`Holiday_Flag`, `CPI`, `Fuel_Price`, `Unemployment`), but they're
deliberately **not** passed into the model as regressors:

- The `(1,1,1,52)` seasonal term already captures the Nov/Dec holiday spike
  directly, making a separate `Holiday_Flag` regressor largely redundant.
- CPI and unemployment are slow-moving macro indicators — they shift
  month-to-month, not week-to-week, so they add little to a 12-week-ahead
  forecast, and the correlation analysis in the notebook backs this up.

So while the `statsmodels` `SARIMAX` class is used (it supports exogenous
inputs), no exogenous variables are actually passed in — functionally, this
is a **seasonal ARIMA (SARIMA)** model per store.

**Validation methodology:** for every store, the last 12 weeks are held out
as a test set, the model is trained on everything before that, and its
forecast is compared against the actual held-out values (MAE / RMSE / MAPE).
Once validated, a second model is trained on the *complete* history per
store to produce the genuine 12-week-ahead forecast into the future.

## 🎯 Results across all 45 stores (12-week holdout)

<div align="center">

| Metric | Mean | Median | Best store | Worst store |
|:---:|:---:|:---:|:---:|:---:|
| **MAPE** | 3.66% | 2.84% | 🥇 1.64% (Store 37) | 14.15% (Store 35) |
| **MAE** | $36,197 | $31,134 | $7,377 | $123,234 |
| **RMSE** | $44,000 | $35,651 | $9,594 | $127,205 |

</div>

Most stores forecast within **~2–4% MAPE**; a small number of higher-variance
stores (like Store 35) are harder to predict and are flagged as such on the
"All Stores Forecast" dashboard page, so planners know exactly where to
apply a wider margin of error.

## 🖥️ Dashboard Pages

| Page | What it shows |
|---|---|
| 🏠 **Home** | KPI overview, sales trends, holiday split, top 10 stores |
| 📊 **EDA Dashboard** | Correlation analysis, seasonality, best vs. worst store |
| 🏪 **Store Analysis** | Per-store deep dive — rank, holiday lift, economic sensitivity |
| 🔮 **Sales Forecasting** | 12-week forecast per store, actual vs. predicted, CSV export |
| 📋 **All Stores Forecast** | Model accuracy across all 45 stores, sorted by MAPE |
| ℹ️ **About Project** | Project summary and methodology |

## 📸 Preview

| Home | EDA Dashboard |
|---|---|
| ![Home](assets/screenshots/About%20Project.png) | ![EDA](assets/screenshots/Walmart-EDA.png) |

| Store Analysis | Sales Forecasting |
|---|---|
| ![Store Analysis](assets/screenshots/Walmart-Store%20Analysis.png) | ![Forecast](assets/screenshots/Walmart-sales-forecast.png) |

| All Stores Forecast |
|:---:|
| ![All Stores](assets/screenshots/Walmart%20-%20all%20stores%20forecast.png) |

## 📂 Dataset

Weekly sales for 45 Walmart stores, **Feb 2010 – Oct 2012** (6,435 rows).

| Column | Description |
|---|---|
| `Store` | Store number (1–45) |
| `Date` | Week (Friday-ending) |
| `Weekly_Sales` | Sales for that store that week |
| `Holiday_Flag` | 1 if the week contains a major holiday |
| `Temperature` | Regional temperature |
| `Fuel_Price` | Regional fuel price |
| `CPI` | Consumer Price Index |
| `Unemployment` | Regional unemployment rate |

Raw and cleaned copies live in [`data/raw`](data/raw) and
[`walmart_deploy/walmart_cleaned.csv`](walmart_deploy/walmart_cleaned.csv).

## 🗂️ Repository Structure

```
Walmart-Sales-Forecasting/
├── notebooks/
│   └── _Walmart_Capstone_Project..ipynb   # full EDA + modeling notebook
├── scripts/
│   └── precompute.py                      # fits SARIMA for all 45 stores, writes forecast CSVs
├── walmart_deploy/                        # deployed Streamlit app
│   ├── app.py                             # 6-page dashboard
│   ├── requirements.txt
│   ├── Walmart_DataSet.csv                # source data
│   ├── walmart_cleaned.csv                # cleaned data used by the app
│   ├── forecast_next_12_weeks.csv         # precomputed forecasts (all stores)
│   ├── model_evaluation_metrics.csv       # MAE / RMSE / MAPE per store
│   └── actual_vs_predicted_holdout.csv    # holdout actual vs. predicted
├── data/raw/                              # copies of the raw + output CSVs
├── documentation/                         # written report, methodology, workflow diagram, slides
├── assets/
│   ├── banner/                            # README hero banner
│   └── screenshots/                       # dashboard screenshots
├── Demo/README.md                         # live app + video walkthrough details
└── README.md
```

## ⚙️ Why Precomputed Forecasts?

Fitting a weekly-seasonal SARIMA (period 52) for all 45 stores takes roughly
**7 minutes total**. Doing that on every Streamlit rerun would make the app
unusably slow and would time out on Streamlit Community Cloud's free tier.
Instead, `scripts/precompute.py` runs the modeling once offline and writes
out the forecast, evaluation, and holdout-comparison CSVs — the app just
loads and displays them, with `@st.cache_data` keeping it fast across
sessions.

To refresh with new data: replace `Walmart_DataSet.csv`, rerun
`python3 precompute.py` (~7 min), commit the four regenerated CSVs, and push
— the app picks up the new data automatically on next load.

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| **Modeling** | `statsmodels` (SARIMAX), `scikit-learn` (evaluation metrics), `pandas`, `numpy` |
| **Dashboard** | `streamlit`, `streamlit-option-menu`, `plotly` |
| **Analysis** | Jupyter Notebook |
| **Deployment** | Streamlit Community Cloud |

## ▶️ Run Locally

```bash
git clone https://github.com/sidducv0528/Walmart-Sales-Forecasting.git
cd Walmart-Sales-Forecasting/walmart_deploy
pip install -r requirements.txt
streamlit run app.py
```

To regenerate the forecast CSVs yourself instead of using the ones already
in the repo:

```bash
cd walmart_deploy
pip install statsmodels scikit-learn
python3 ../scripts/precompute.py
```

## 📄 Documentation

- 📘 [`Walmart_Project_Report.pdf`](documentation/Walmart_Project_Report.pdf) — full written report
- 🔬 [`Methodology.pdf`](documentation/Methodology.pdf) — modeling and evaluation methodology, in depth
- 🧭 [`Project_Workflow.pdf`](documentation/Project_Workflow.pdf) — end-to-end pipeline diagram
- 🖼️ [`Walmart_Presentation.pptx`](documentation/Walmart_Presentation.pptx) — slide deck version
- 🎬 [`Demo/README.md`](Demo/README.md) — live app + video walkthrough, page by page

## 📬 Contact

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-sidducv0528-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sidducv0528)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-siddu--data-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/siddu-data/)
[![Email](https://img.shields.io/badge/Email-sidducv0528%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:sidducv0528@gmail.com)

</div>

---

<div align="center">
<sub>⭐ If this project helped you, consider starring the repo!</sub>
</div>
