# 🎬 Demo

Live app and video walkthrough for the Walmart Sales Forecasting Dashboard.

## 🔗 Live App

**[walmart-sales-forecasting-stores.streamlit.app](https://walmart-sales-forecasting-stores.streamlit.app/)**

Hosted on Streamlit Community Cloud, connected directly to this repository —
redeploys automatically on every push to `main`.

> First load can take a few seconds if the app has been idle (Streamlit
> Cloud's free tier spins containers down after inactivity).

## 📺 Video Walkthrough

[![Watch the demo](https://img.youtube.com/vi/UXW4FTEN994/maxresdefault.jpg)](https://youtu.be/UXW4FTEN994)

**[youtu.be/UXW4FTEN994](https://youtu.be/UXW4FTEN994)**

A walkthrough of the dashboard — navigating all six pages, using the
store/year/holiday filters, and reading the per-store forecast and model
performance results.

## 🖥️ What's Covered in the Demo

| Page | What it shows |
|---|---|
| **Home** | KPI overview, sales trends, holiday split, top 10 stores |
| **EDA Dashboard** | Correlation analysis, seasonality, best vs. worst store |
| **Store Analysis** | Per-store deep dive — rank, holiday lift, economic sensitivity |
| **Sales Forecasting** | 12-week forecast per store, actual vs. predicted, CSV export |
| **All Stores Forecast** | Model accuracy across all 45 stores, sorted by MAPE |
| **About Project** | Project summary and methodology |

## 📸 Screenshots

See [`assets/screenshots/`](../assets/screenshots) for static images of each
page, or the full [Project Report](../docs/Walmart_Project_Report.pdf) for
screenshots embedded alongside written analysis.

## 📄 Related Documentation

- [Walmart_Project_Report.pdf](../docs/Walmart_Project_Report.pdf) — full written report
- [Methodology.pdf](../docs/Methodology.pdf) — modeling and evaluation methodology, in depth
- [Project_Workflow.pdf](../docs/Project_Workflow.pdf) — end-to-end pipeline diagram
- [Walmart_Presentation.pptx](../docs/Walmart_Presentation.pptx) — slide deck version

## ▶️ Run It Yourself

```bash
git clone https://github.com/sidducv0528/Walmart-Sales-Forecasting.git
cd Walmart-Sales-Forecasting/walmart_deploy
pip install -r requirements.txt
streamlit run app.py
```

## 📬 Contact

- **GitHub:** [sidducv0528](https://github.com/sidducv0528)
- **LinkedIn:** [siddu-data](https://linkedin.com/in/siddu-data/)
- **Email:** sidducv0528@gmail.com
