# Volve Oil Production Analysis & Forecasting App

## What This Is

A Streamlit web application for oil production analysis and decline curve analysis (DCA) using the Volve field dataset (well 15/9-F-12, daily data 2007–2016). Built for a webinar demo to teach petroleum engineers and students how to explore production data and apply Arps decline curve models interactively. Deployed on HuggingFace Spaces.

## Core Value

An engineer can load the Volve dataset, visually explore production trends, fit a decline curve with one click, fine-tune parameters interactively, and walk away with an EUR forecast — all in one app, live in a webinar.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] App displays data overview: raw table, date range, summary statistics
- [ ] Time-series charts of oil/gas/water volumes, wellhead pressure, choke size, water cut
- [ ] DCA fitting: auto-fit Arps model (exponential, hyperbolic, harmonic) to user-selected date range
- [ ] Manual fine-tuning: qi, Di, b sliders update the fitted curve live
- [ ] Forecast view: project production N months/years forward, show EUR estimate
- [ ] Dark professional theme using Plotly charts
- [ ] Deployable to HuggingFace Spaces (requirements.txt, app.py entry point)

### Out of Scope

- ML-based forecasting (XGBoost, LSTM) — deferred, DCA is the focus for v1
- Multi-well comparison — dataset has one well (15/9-F-12)
- Real-time data ingestion — static CSV only
- User authentication — public demo app

## Context

- Dataset: `Final PF-12 and Injection.csv` — 3,305 daily rows, Sept 2007 – Sept 2016
- Single well: 15/9-F-12 (Volve field, Norwegian North Sea, Equinor open dataset)
- Key columns: DATEPRD, BORE_OIL_VOL, BORE_GAS_VOL, BORE_WAT_VOL, AVG_DOWNHOLE_PRESSURE, AVG_WHP_P, AVG_CHOKE_SIZE_P, DP_CHOKE_SIZE, ON_STREAM_HRS, Water Injection (F-4, F-5)
- Deployment target: HuggingFace Spaces (Streamlit SDK)
- Audience: petroleum engineers / students in a live webinar setting

## Constraints

- **Tech Stack**: Streamlit — required for HuggingFace Spaces deployment
- **Charts**: Plotly — dark theme, interactive, projector-friendly
- **Data**: Single static CSV file already in repo — no external data fetching needed
- **DCA**: Arps decline curve equations (exponential, hyperbolic, harmonic) — standard petroleum engineering approach

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DCA over ML forecasting | Webinar audience is petroleum engineers; Arps DCA is the industry standard and teachable | — Pending |
| Plotly over Altair/Matplotlib | Interactive + dark theme out of the box, better for live demos | — Pending |
| HuggingFace Spaces deployment | User's chosen platform; Streamlit SDK supported natively | — Pending |
| Auto-fit + manual tuning | Best of both: shows the math works, then lets audience tweak parameters to understand sensitivity | — Pending |

---
*Last updated: 2026-05-08 after initialization*
