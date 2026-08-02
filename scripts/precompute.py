import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
import time

warnings.filterwarnings("ignore")

df = pd.read_csv("Walmart_DataSet.csv")
df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
df = df.sort_values(["Store", "Date"]).reset_index(drop=True)

forecast_results = []
evaluation_results = []
comparison_all = []

t0 = time.time()
for store in sorted(df["Store"].unique()):
    store_df = df[df["Store"] == store].copy().sort_values("Date")
    sales = store_df.set_index("Date")["Weekly_Sales"]
    sales = sales.asfreq("W-FRI")  # ensure regular weekly freq for SARIMAX

    train = sales[:-12]
    test = sales[-12:]

    # --- Evaluation model (trained on train, tested on held-out last 12 weeks) ---
    eval_model = SARIMAX(
        train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 52),
        enforce_stationarity=False, enforce_invertibility=False,
    )
    eval_result = eval_model.fit(disp=False)
    predictions = eval_result.forecast(steps=12)

    mae = mean_absolute_error(test, predictions)
    rmse = np.sqrt(mean_squared_error(test, predictions))
    mape = np.mean(np.abs((test - predictions) / test)) * 100

    evaluation_results.append({
        "Store": store, "MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE (%)": round(mape, 2)
    })

    comparison_all.append(pd.DataFrame({
        "Store": store,
        "Date": test.index,
        "Actual_Sales": test.values,
        "Predicted_Sales": predictions.values,
    }))

    # --- Full model (trained on ALL data) for genuine future forecast ---
    full_model = SARIMAX(
        sales, order=(1, 1, 1), seasonal_order=(1, 1, 1, 52),
        enforce_stationarity=False, enforce_invertibility=False,
    )
    full_result = full_model.fit(disp=False)
    forecast = full_result.forecast(steps=12)

    future_dates = pd.date_range(start=sales.index.max() + pd.Timedelta(weeks=1), periods=12, freq="W-FRI")
    forecast_results.append(pd.DataFrame({
        "Store": store, "Date": future_dates, "Forecasted_Sales": forecast.values
    }))

    print(f"Store {store:2d} done | MAPE {mape:5.2f}% | elapsed {time.time()-t0:5.1f}s")

forecast_df = pd.concat(forecast_results, ignore_index=True)
evaluation_df = pd.DataFrame(evaluation_results)
comparison_df = pd.concat(comparison_all, ignore_index=True)

forecast_df.to_csv("forecast_next_12_weeks.csv", index=False)
evaluation_df.to_csv("model_evaluation_metrics.csv", index=False)
comparison_df.to_csv("actual_vs_predicted_holdout.csv", index=False)

# Also stash the cleaned historical data for the app
df.to_csv("walmart_cleaned.csv", index=False)

print("\nTotal time:", round(time.time() - t0, 1), "s")
print("\nEvaluation summary:")
print(evaluation_df.describe())
