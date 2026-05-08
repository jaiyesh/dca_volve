# Roadmap: Volve Oil Production Analysis & DCA Forecasting App

## Overview

A single-phase full build that delivers a complete, deployable Streamlit app: data pipeline, Arps DCA math, dark Plotly charts, interactive UI (data overview, production explorer, DCA forecast with live sliders), and a Docker-based HuggingFace Spaces deployment. All 12 v1 requirements ship together.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Full Build** - Build and deploy the complete Volve DCA app in one pass (completed 2026-05-08)

## Phase Details

### Phase 1: Full Build
**Goal**: A petroleum engineer can open the live HuggingFace Spaces URL, explore Volve production data, auto-fit an Arps decline curve, tune parameters interactively, and read an EUR forecast — all in one dark-themed app
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DCA-01, DCA-02, DCA-03, DCA-04, FORE-01, FORE-02, FORE-03, DEPLOY-01, DEPLOY-02
**Success Criteria** (what must be TRUE):
  1. User opens the app URL and sees a Data Overview page with the Volve dataset summary stats, date range (Sept 2007 – Sept 2016), and a raw data table with shut-in rows already filtered out
  2. User navigates to the Production Explorer page and sees interactive dark Plotly time-series charts for oil/gas/water volumes, wellhead pressure, choke size, and water cut — all charts use theme=None and are projector-readable
  3. User selects a date range on the DCA Forecast page, clicks Auto-Fit, and sees an Arps curve (exponential/hyperbolic/harmonic) overlaid on the historical production scatter with R-squared and RMSE metrics displayed
  4. User moves the qi, Di, or b sliders and the fitted curve and EUR estimate update live without re-triggering the optimizer
  5. App is live on HuggingFace Spaces via Docker SDK (sdk: docker, port 8501), loads within 60 seconds, and shows no SDK-deprecation or port errors
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — Data pipeline: utils/data.py (load_data, filter_by_date, get_sidebar_kpis)
- [ ] 01-02-PLAN.md — DCA math core: utils/dca.py (Arps equations, curve_fit wrapper, EUR, forecast, LaTeX)
- [ ] 01-03-PLAN.md — Deployment config: Dockerfile, requirements.txt, README.md, config.toml
- [ ] 01-04-PLAN.md — Chart factory + simple pages: utils/charts.py, Data Overview, Production Explorer
- [ ] 01-05-PLAN.md — DCA Forecast page + app.py router + human verification

## Progress

**Execution Order:**
Phases execute in numeric order: 1

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Full Build | 5/5 | Complete   | 2026-05-08 |
