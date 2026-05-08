# Phase 1: Full Build - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the complete Streamlit app: Data Overview page, Production Explorer page, DCA Forecast page, and Docker deployment for HuggingFace Spaces. All 12 v1 requirements ship in this single phase.

</domain>

<decisions>
## Implementation Decisions

### App Navigation & Structure
- Streamlit multi-page app using `pages/` directory (not tabs, not sidebar radio)
- 3 pages: Data Overview | Production Explorer | DCA Forecast
- App title: **"Volve DCA Dashboard"**
- Sidebar (visible on all pages): page navigation + dataset info (well name, date range, total production stats)
- Page structure: `app.py` as router entry point, `pages/1_Data_Overview.py`, `pages/2_Production_Explorer.py`, `pages/3_DCA_Forecast.py`

### DCA Page Layout
- Controls in **left sidebar** (st.sidebar), chart takes full page width — maximizes chart size on projector
- Sidebar contains: date range pickers, model selector (Exponential / Hyperbolic / Harmonic), Auto-Fit button, qi/Di/b sliders, EUR metric
- Fitting triggered by **explicit "Auto-Fit" button** (not auto on date change) — clear cause-and-effect for webinar demo
- Forecast projection on the **same chart** as historical scatter + fitted curve (one unified chart, extended rightward)
- Production units: **Sm³/day** (native CSV units, no conversion)

### Fitting Feedback Display
- After auto-fit: show **R² + RMSE** as st.metric cards above the chart
- Fitted parameters (qi, Di, b) written to session_state; sliders **pre-filled** with fitted values — user sees numbers and can immediately tune
- **Live Arps equation** displayed using st.latex() with current parameter values substituted in — key teaching moment
- EUR displayed as a **large st.metric** showing value in MSm³ (million Sm³), prominent and projector-readable
- Harmonic singularity guard: abs(b - 1.0) < 0.01 → clamp EUR, show warning

### Data Overview Content
- Summary KPIs: total oil produced (MSm³), peak oil rate (Sm³/day) + date, current/final rate, on-stream days, water cut at end of field life
- Raw data table: filtered to producing days only (ON_STREAM_HRS > 0), paginated, key columns shown (DATEPRD, BORE_OIL_VOL, BORE_GAS_VOL, BORE_WAT_VOL, AVG_WHP_P, AVG_CHOKE_SIZE_P, ON_STREAM_HRS)

### Production Explorer Charts
- 4 charts, stacked vertically (full width, one per row):
  1. Oil rate vs time (BORE_OIL_VOL)
  2. Gas rate vs time (BORE_GAS_VOL)
  3. Water cut vs time (derived: WAT_VOL / (OIL_VOL + WAT_VOL))
  4. WHP & choke size vs time (dual-axis or subplots)
- All charts: dark Plotly theme, `st.plotly_chart(fig, theme=None, use_container_width=True)`

### Dark Theme & Deployment
- All Plotly charts use `plotly_dark` template + `theme=None` in st.plotly_chart()
- Docker deployment: Dockerfile targeting port 8501, HF Spaces README with `sdk: docker, app_port: 8501`
- Date parsing: `pd.to_datetime(format='%d-%b-%y')` — confirmed from actual CSV (format: `01-Sep-07`)

### Claude's Discretion
- Exact color palette within plotly_dark (accent colors for oil/gas/water lines)
- Slider step sizes and default ranges for qi/Di/b
- Exact Arps equation LaTeX formatting
- Loading spinner text
- Column order in data table

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — greenfield project

### Established Patterns
- Data file: `Final PF-12 and Injection.csv` at repo root — load with `pd.read_csv()`, parse DATEPRD with `format='%d-%b-%y'`
- Filter producing days: `df[df['ON_STREAM_HRS'] > 0]`
- DCA math: `scipy.optimize.curve_fit` with bounds for b in [0, 1]

### Integration Points
- `utils/data.py` → loaded by all 3 pages
- `utils/dca.py` → loaded by DCA Forecast page only
- `utils/charts.py` → loaded by Explorer and DCA pages
- All st.* calls live in page files only — utils are pure Python/Plotly

</code_context>

<specifics>
## Specific Ideas

- Sidebar shows dataset context at all times so webinar audience always knows what data they're looking at
- Explicit Auto-Fit button (not auto-trigger) so presenter can explain what's about to happen before clicking
- st.latex() for live equation display — strongest teaching moment in the app
- Forecast extends rightward on same chart — "one chart tells the whole story"

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-full-build*
*Context gathered: 2026-05-08*
