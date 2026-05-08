---
phase: 01-full-build
verified: 2026-05-08T00:00:00Z
status: gaps_found
score: 11/12 must-haves verified
gaps:
  - truth: "All Plotly charts use template=plotly_dark and are rendered with theme=None, width=stretch"
    status: partial
    reason: "pages/3_DCA_Forecast.py line 170 uses use_container_width=True instead of width='stretch' on its st.plotly_chart call. All four charts in Production Explorer correctly use width='stretch', but the central DCA Forecast chart does not."
    artifacts:
      - path: "pages/3_DCA_Forecast.py"
        issue: "Line 170: st.plotly_chart(fig, theme=None, use_container_width=True) — should be width='stretch'"
    missing:
      - "Change use_container_width=True to width='stretch' on line 170 of pages/3_DCA_Forecast.py"
human_verification:
  - test: "Open the live HuggingFace Spaces URL and verify the app loads"
    expected: "App loads within 60 seconds, no SDK-deprecation or port errors, dark-themed UI appears"
    why_human: "Cannot verify live deployment URL or HuggingFace Spaces runtime behavior programmatically"
  - test: "Click Auto-Fit on the DCA Forecast page with the default date range (2009-01-01 to 2012-12-31)"
    expected: "Arps curve overlaid on historical scatter; R2 and RMSE metric cards appear; qi/Di/b sliders pre-fill with fitted values"
    why_human: "Requires a live Streamlit runtime with session_state; cannot test without running app"
  - test: "Drag a parameter slider after Auto-Fit"
    expected: "Chart and EUR update immediately without triggering the scipy optimizer (no spinner visible during drag)"
    why_human: "Slider live-update behavior requires visual observation in a running app"
  - test: "Confirm the DCA Forecast chart renders at full width on the DCA Forecast page"
    expected: "Chart spans the full main content area; no narrow chart due to use_container_width=True vs width='stretch'"
    why_human: "Visual width behavior depends on Streamlit version rendering; use_container_width=True may produce a slightly different layout than width='stretch'"
---

# Phase 1: Full Build Verification Report

**Phase Goal:** A petroleum engineer can open the live HuggingFace Spaces URL, explore Volve production data, auto-fit an Arps decline curve, tune parameters interactively, and read an EUR forecast — all in one dark-themed app
**Verified:** 2026-05-08
**Status:** gaps_found — 1 gap (DEPLOY-02 partial: DCA chart missing width='stretch')
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | load_data() returns 2901 rows with ON_STREAM_HRS > 0 filter | VERIFIED | Runtime test confirmed 2901 rows; CSV has 3305 raw rows, 404 shut-in |
| 2 | DATEPRD parsed as datetime; assert checks pre-filter range includes 2007 | VERIFIED | Pre-filter min year=2007, max year=2016; assert passes; producing range is Feb 2008 – Aug 2016 |
| 3 | WATER_CUT derived column exists and is bounded [0, 1] | VERIFIED | Column present; values range 0.0 – 0.977 (no values outside bounds) |
| 4 | filter_by_date() narrows to given date range | VERIFIED | 350 rows returned for 2009 calendar year |
| 5 | load_data() is decorated with @st.cache_data | VERIFIED | Line 15 of utils/data.py |
| 6 | Arps rate functions return valid rates at t=0 and t=100 | VERIFIED | All three q(0) return qi; harmonic q(100) = 500.0 as expected |
| 7 | calculate_eur() is finite and positive for all model types | VERIFIED | exp=99900, hyp=193675, harm=690776 Sm3; near-harmonic (b=0.99) guard fires correctly |
| 8 | forecast_arps() returns calendar-date x-axis as pd.DatetimeIndex | VERIFIED | Column dtype confirmed datetime64; not integer day offsets |
| 9 | fit_arps() achieves R2 > 0.95 on synthetic exponential data | VERIFIED | R2=1.0 on 300-point synthetic exponential decline |
| 10 | get_latex_equation() returns non-empty LaTeX for all model types | VERIFIED | Non-empty strings returned for exponential, hyperbolic, harmonic |
| 11 | Data Overview and Production Explorer pages are fully wired | VERIFIED | Both import from utils.data; Production Explorer imports from utils.charts; all 4 charts render; correct st.metric KPIs |
| 12 | All Plotly charts use theme=None and width='stretch' | PARTIAL | Production Explorer (4 charts) correct; DCA Forecast chart (line 170) uses use_container_width=True instead of width='stretch' |
| 13 | app.py routes to all 3 pages via st.navigation | VERIFIED | st.navigation with st.Page for all three pages; title='Volve DCA Dashboard' |
| 14 | Dockerfile builds from python:3.11, exposes port 8501 | VERIFIED | FROM python:3.11; EXPOSE 8501; no --server.port in CMD |
| 15 | requirements.txt pins all 5 dependencies to exact versions | VERIFIED | streamlit==1.52.0, plotly==6.0.0, pandas==2.2.3, numpy==1.26.4, scipy==1.17.1 |
| 16 | README.md YAML has sdk: docker and app_port: 8501 | VERIFIED | YAML front-matter confirmed at top of file |
| 17 | .streamlit/config.toml sets dark theme, no server.port | VERIFIED | base = "dark", no [server] section, no port key |
| 18 | Session state initialized before widgets; sliders use key-only binding | VERIFIED | _ss_defaults dict initialized at top of file; dca_qi/Di/b sliders have no value= parameter |
| 19 | Auto-Fit writes to session_state; EUR and LaTeX update on slider move | VERIFIED | fit_result written to st.session_state; calculate_eur and get_latex_equation called on every rerun using current session_state values |
| 20 | No streamlit imports in utils/dca.py or utils/charts.py | VERIFIED | Neither file imports streamlit |

**Score:** 19/20 truths verified (1 partial)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `utils/__init__.py` | Package marker | VERIFIED | Exists, empty (0 bytes) |
| `utils/data.py` | load_data, filter_by_date, get_sidebar_kpis | VERIFIED | All three functions present and tested |
| `utils/dca.py` | 7 Arps functions | VERIFIED | exponential_q, hyperbolic_q, harmonic_q, fit_arps, forecast_arps, calculate_eur, get_latex_equation — all present |
| `utils/charts.py` | DARK_LAYOUT, build_timeseries_chart, build_dual_axis_chart, build_dca_chart | VERIFIED | All 4 exports present; build_dca_chart added in plan 05 |
| `pages/1_Data_Overview.py` | Data Overview page | VERIFIED | 4 st.metric KPIs, filtered table with DISPLAY_COLUMNS |
| `pages/2_Production_Explorer.py` | Production Explorer page | VERIFIED | 4 charts with correct colors; all st.plotly_chart calls use theme=None, width='stretch' |
| `pages/3_DCA_Forecast.py` | DCA Forecast page | PARTIAL | Full functionality present; plotly_chart call on line 170 uses use_container_width=True instead of width='stretch' |
| `app.py` | Multi-page router | VERIFIED | st.navigation with 3 st.Page entries; correct titles |
| `Dockerfile` | Docker build spec | VERIFIED | FROM python:3.11; EXPOSE 8501; non-root user; no --server.port |
| `requirements.txt` | Pinned dependencies | VERIFIED | All 5 packages at exact versions |
| `README.md` | HuggingFace Spaces YAML | VERIFIED | sdk: docker, app_port: 8501, at top of file |
| `.streamlit/config.toml` | Dark theme | VERIFIED | base = "dark"; no [server] section |
| `packages.txt` | System deps placeholder | VERIFIED | Exists, empty (0 bytes) |
| `Final PF-12 and Injection.csv` | Source data | VERIFIED | 360KB, present at repo root |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `utils/data.py` | `Final PF-12 and Injection.csv` | Path(__file__).parent.parent / 'Final PF-12 and Injection.csv' | WIRED | Pattern confirmed: `_CSV_PATH = Path(__file__).parent.parent / "Final PF-12 and Injection.csv"` |
| `utils/data.py` | `st.cache_data` | @st.cache_data decorator on load_data() | WIRED | Decorator on line 15 |
| `utils/dca.py fit_arps()` | `scipy.optimize.curve_fit` | method='trf', bounds, domain-informed p0 | WIRED | method="trf" present; p0 uses qi_guess=q[0]*0.9 |
| `calculate_eur()` | harmonic branch guard | if abs(b - 1.0) < 0.01 | WIRED | Guard present at line 75 of dca.py |
| `pages/1_Data_Overview.py` | `utils/data.load_data()` | from utils.data import load_data, get_sidebar_kpis | WIRED | Import confirmed on line 2 |
| `pages/2_Production_Explorer.py` | `utils/charts` | from utils.charts import build_timeseries_chart, build_dual_axis_chart | WIRED | Import confirmed on line 3 |
| `st.plotly_chart` (Production Explorer) | theme=None, width=stretch | st.plotly_chart(fig, theme=None, width='stretch') | WIRED | All 4 chart calls use correct parameters |
| `st.plotly_chart` (DCA Forecast) | theme=None, width=stretch | st.plotly_chart(fig, theme=None, width='stretch') | PARTIAL | theme=None correct; width uses use_container_width=True instead of width='stretch' |
| Auto-Fit button | st.session_state.qi/Di/b | writes fit_result values to session_state before slider renders | WIRED | Lines 79-90: direct session_state writes on button click |
| st.slider key='dca_qi' | st.session_state['dca_qi'] | key-only binding (no value= parameter) | WIRED | Lines 96-98: sliders for dca_qi, dca_Di, dca_b have no value= argument |
| `forecast_arps()` | `build_dca_chart()` | fit_result_for_chart dict passed to forecast_arps then to build_dca_chart | WIRED | Lines 155-168 in DCA page; calendar-date df_forecast feeds chart |
| `app.py` | `pages/3_DCA_Forecast.py` | st.Page('pages/3_DCA_Forecast.py', title='DCA Forecast') | WIRED | Line 15 of app.py |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| DATA-01 | 01-01-PLAN | Load and parse Volve CSV, filter shut-in days via ON_STREAM_HRS > 0 | SATISFIED | load_data() returns 2901 rows; @st.cache_data; correct format |
| DATA-02 | 01-04-PLAN | Data overview page: summary stats, date range, raw data table | SATISFIED | 4 KPI metrics, 7-column filtered table, sidebar kpis |
| DATA-03 | 01-04-PLAN | Production explorer: time-series charts oil/gas/water/WHP/choke/WC | SATISFIED | 4 charts (3 single-axis + 1 dual-axis) with all required columns |
| DCA-01 | 01-02-PLAN, 01-05-PLAN | User selects date range for DCA fitting via date pickers | SATISFIED | st.date_input widgets for start_date/end_date in DCA page sidebar |
| DCA-02 | 01-02-PLAN, 01-05-PLAN | Auto-fit Arps model via scipy curve_fit with b in [0, 1] | SATISFIED | fit_arps() uses curve_fit with bounds b in [0, 1]; Auto-Fit button wired to fit_arps |
| DCA-03 | 01-05-PLAN | User can manually tune qi, Di, b via sliders with live curve update | SATISFIED | Key-only sliders; forecast/EUR recompute on every rerun from session_state values |
| DCA-04 | 01-05-PLAN | Fitted curve overlaid on historical production chart | SATISFIED | build_dca_chart overlays historical scatter + fit window + forecast curve |
| FORE-01 | 01-05-PLAN | User sets forecast horizon (months) and abandonment rate | SATISFIED | forecast_months slider (12–360) and q_aband slider (0.1–100.0) in sidebar |
| FORE-02 | 01-05-PLAN | App computes and displays EUR estimate | SATISFIED | calculate_eur() called every rerun; displayed as st.metric in sidebar |
| FORE-03 | 01-05-PLAN | Forecast chart shows historical data + projected decline curve | SATISFIED | forecast_arps returns calendar-date DataFrame; overlaid on historical scatter via build_dca_chart |
| DEPLOY-01 | 01-03-PLAN | Dockerfile targeting port 8501 for HuggingFace Spaces Docker SDK | SATISFIED | FROM python:3.11; EXPOSE 8501; README sdk: docker; app_port: 8501 |
| DEPLOY-02 | 01-03-PLAN, 01-04-PLAN, 01-05-PLAN | Dark Plotly theme via st.plotly_chart(theme=None) | PARTIAL | theme=None present on all charts; DCA Forecast chart uses deprecated use_container_width=True instead of width='stretch' |

**Requirements fully satisfied:** 11/12
**Requirements partially satisfied:** 1/12 (DEPLOY-02)
**Requirements blocked:** 0/12
**Orphaned requirements (in REQUIREMENTS.md but not in any plan):** None

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `pages/3_DCA_Forecast.py` | 170 | `use_container_width=True` on st.plotly_chart instead of `width='stretch'` | Warning | use_container_width is deprecated for plotly_chart in Streamlit >= 1.36. In streamlit==1.52.0 (the pinned version), it still functions but emits a deprecation warning. Will be removed after 2025-12-31, so it will break in future Streamlit versions. |
| `utils/data.py` | 28–30 | Comment says "Sept 2007 – Sept 2016" but kpis['date_start'] displays "Feb 2008" | Info | All 2007 rows are shut-in (ON_STREAM_HRS == 0) so they are filtered out. The assert runs pre-filter so it passes. The sidebar and page captions will show "Feb 2008 – Aug 2016". The ROADMAP success criterion mentions "Sept 2007 – Sept 2016" but this refers to the raw dataset range, not the displayed producing range — functionally acceptable. |

No TODO/FIXME/placeholder comments found. No empty return implementations found. No stub functions found.

---

## Human Verification Required

### 1. Live HuggingFace Spaces Deployment

**Test:** Open the HuggingFace Spaces URL for this app in a browser
**Expected:** App loads within 60 seconds, Docker SDK initialized, dark-themed UI shows Data Overview as the landing page, no deprecation or port errors in the Space logs
**Why human:** Cannot programmatically access or test a live HuggingFace Spaces URL

### 2. Auto-Fit End-to-End Flow

**Test:** Navigate to DCA Forecast page; select date range 2009-01-01 to 2012-12-31; choose Hyperbolic model; click Auto-Fit
**Expected:** Arps curve (cyan dashed line) overlays historical scatter (grey dots); R2 and RMSE metric cards appear above chart; qi/Di/b sliders populate with fitted values; LaTeX equation updates with those values
**Why human:** Requires live Streamlit runtime with session_state; cannot verify without running app

### 3. Slider Live-Update Without Re-Fitting

**Test:** After Auto-Fit completes, drag the qi slider to a different value
**Expected:** Chart updates immediately (no loading spinner from curve_fit); EUR metric in sidebar changes; no StreamlitAPIException in terminal
**Why human:** Slider drag behavior and absence of optimizer re-trigger requires visual observation

### 4. DCA Chart Width on DCA Forecast Page

**Test:** On the DCA Forecast page, observe the width of the main chart
**Expected:** Chart spans the full content area (same width as Production Explorer charts)
**Why human:** use_container_width=True vs width='stretch' may produce different visual results; needs visual comparison in browser. If chart appears narrower, the gap should be fixed.

---

## Gaps Summary

**1 gap found — DEPLOY-02 partial**

The DCA Forecast page (`pages/3_DCA_Forecast.py`, line 170) calls `st.plotly_chart(fig, theme=None, use_container_width=True)` instead of the required `st.plotly_chart(fig, theme=None, width="stretch")`.

All other pages (Production Explorer) correctly use `width="stretch"`. This is inconsistent and violates the explicit PLAN 01-04 key link requirement and the PLAN 01-05 success criteria (`width='stretch'`). The `use_container_width` parameter is deprecated for `st.plotly_chart` in Streamlit >= 1.36 and is scheduled for removal after 2025-12-31. With the pinned `streamlit==1.52.0`, the app still functions but the deprecation warning will appear in logs and could break with a future Streamlit upgrade.

**Fix required:** Change line 170 of `pages/3_DCA_Forecast.py` from:
```python
st.plotly_chart(fig, theme=None, use_container_width=True)
```
to:
```python
st.plotly_chart(fig, theme=None, width="stretch")
```

This is a targeted single-line fix.

---

**All other goal-critical components are fully implemented and wired:**
- Data pipeline loads and filters correctly (2901 producing-day rows, WATER_CUT derived, @st.cache_data)
- DCA math core passes all assertions (EUR finite for all models including near-harmonic, R2=1.0 on synthetic data)
- Session state schema correctly prevents double-binding; Auto-Fit pre-fills sliders; EUR recomputes live
- Forecast uses calendar-date x-axis from forecast_arps()
- Deployment config complete (Dockerfile port 8501, requirements.txt pinned, README sdk:docker, dark theme)
- All 13 expected files present

---

_Verified: 2026-05-08_
_Verifier: Claude (gsd-verifier)_
