# Requirements: Volve Oil Production Analysis & DCA Forecasting App

**Defined:** 2026-05-08
**Core Value:** An engineer can load the Volve dataset, explore production trends, fit a decline curve, tune parameters interactively, and get an EUR forecast — all in one dark-themed Streamlit app deployable to HuggingFace Spaces.

## v1 Requirements

### Data

- [ ] **DATA-01**: App loads and parses Volve CSV, filters shut-in days using ON_STREAM_HRS > 0
- [ ] **DATA-02**: Data overview page displays summary statistics, date range, and raw data table
- [ ] **DATA-03**: Production explorer shows time-series charts of oil/gas/water volumes, WHP, choke size, and water cut

### DCA Fitting

- [ ] **DCA-01**: User selects date range for DCA fitting via date pickers
- [ ] **DCA-02**: App auto-fits Arps model (exponential/hyperbolic/harmonic) via scipy curve_fit with b constrained to [0, 1]
- [ ] **DCA-03**: User can manually tune qi, Di, b via sliders with live curve update
- [ ] **DCA-04**: Fitted curve overlaid on historical production chart

### Forecast

- [ ] **FORE-01**: User sets forecast horizon (months) and abandonment rate
- [ ] **FORE-02**: App computes and displays EUR estimate
- [ ] **FORE-03**: Forecast chart shows historical data + projected decline curve

### Deployment

- [ ] **DEPLOY-01**: App packaged with Dockerfile targeting port 8501 for HuggingFace Spaces (Docker SDK — native Streamlit SDK deprecated Apr 30 2025)
- [ ] **DEPLOY-02**: Dark Plotly theme applied consistently via st.plotly_chart(theme=None)

## v2 Requirements

### Advanced Analytics

- **ADV-01**: ML-based forecasting (XGBoost/LSTM) for comparison with DCA
- **ADV-02**: Probabilistic forecasting (P10/P50/P90)
- **ADV-03**: Economic evaluation (NPV, breakeven)
- **ADV-04**: Multi-well comparison

## Out of Scope

| Feature | Reason |
|---------|--------|
| ML forecasting | DCA is the focus for v1 webinar demo |
| Multi-well | Dataset has single well (15/9-F-12) |
| Real-time data ingestion | Static CSV only |
| Probabilistic bands | Adds complexity; b=[0,1] bounds sufficient for teaching |
| Economic evaluation | Out of webinar scope |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DCA-01 | Phase 1 | Pending |
| DCA-02 | Phase 1 | Pending |
| DCA-03 | Phase 1 | Pending |
| DCA-04 | Phase 1 | Pending |
| FORE-01 | Phase 1 | Pending |
| FORE-02 | Phase 1 | Pending |
| FORE-03 | Phase 1 | Pending |
| DEPLOY-01 | Phase 1 | Pending |
| DEPLOY-02 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-08*
*Last updated: 2026-05-08 after initial definition*
