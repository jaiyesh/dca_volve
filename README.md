---
title: Volve DCA Dashboard
emoji: 🛢
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 8501
pinned: false
---

# Volve DCA Dashboard

Interactive Decline Curve Analysis (DCA) app for the Volve field well 15/9-F-12 dataset (Norwegian North Sea, 2007–2016).

## Features

- **Data Overview**: Summary statistics, date range, and filtered production table
- **Production Explorer**: Dark time-series charts for oil, gas, water cut, and wellhead pressure
- **DCA Forecast**: Auto-fit Arps decline curves (Exponential / Hyperbolic / Harmonic), interactive parameter sliders, EUR forecast, live equation display

## Tech Stack

- Streamlit 1.52.0 + Plotly 6.0.0 (dark theme)
- scipy.optimize.curve_fit for Arps fitting
- Deployed via HuggingFace Spaces Docker SDK

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
