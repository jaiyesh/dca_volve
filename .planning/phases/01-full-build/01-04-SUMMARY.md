---
phase: 01-full-build
plan: "04"
subsystem: ui
tags: [plotly, streamlit, dark-theme, charts, data-visualization, timeseries, dual-axis]

# Dependency graph
requires:
  - phase: 01-full-build/01-01
    provides: load_data(), get_sidebar_kpis(), DISPLAY_COLUMNS, WATER_CUT column
  - phase: 01-full-build/01-02
    provides: dca.py exists (not used here but part of same wave)

provides:
  - Dark Plotly chart factory (utils/charts.py) with DARK_LAYOUT, build_timeseries_chart, build_dual_axis_chart
  - Data Overview page (pages/1_Data_Overview.py) with 4 KPI cards and DISPLAY_COLUMNS table
  - Production Explorer page (pages/2_Production_Explorer.py) with 4 stacked dark Plotly charts

affects:
  - 01-05 (app.py wiring and DCA page will use same pages/ directory and chart patterns)

# Tech tracking
tech-stack:
  added: [plotly==6.0.0]
  patterns:
    - "Dark chart factory: pure Plotly, no Streamlit — all st.plotly_chart calls in page files only"
    - "st.plotly_chart(fig, theme=None, width='stretch') — prevents Streamlit from overriding plotly_dark"
    - "Sidebar pattern: well name + date range + total oil MSm³ st.metric identical across all pages"
    - "DARK_LAYOUT dict: template=plotly_dark, paper_bgcolor=#0E1117, plot_bgcolor=#0E1117"

key-files:
  created:
    - utils/charts.py
    - pages/1_Data_Overview.py
    - pages/2_Production_Explorer.py
  modified: []

key-decisions:
  - "Plotly 6.0.0 removed titlefont in yaxis — must use title=dict(text=..., font=dict(color=...)) instead"
  - "Data Overview has zero st.plotly_chart calls — uses st.dataframe for production table, st.metric for KPIs"
  - "Production Explorer has exactly 4 st.plotly_chart calls: oil, gas, water cut, WHP+choke (dual axis)"
  - "build_dual_axis_chart uses yaxis2 with overlaying='y', side='right' for choke size on right axis"

patterns-established:
  - "Chart factory pattern: utils/charts.py returns go.Figure objects, pages call st.plotly_chart with theme=None"
  - "Sidebar KPI pattern: get_sidebar_kpis(df) -> dict, then st.metric for each value"

requirements-completed: [DATA-02, DATA-03, DEPLOY-02]

# Metrics
duration: 2min
completed: 2026-05-08
---

# Phase 01 Plan 04: Chart Factory and Visualization Pages Summary

**Plotly 6 dark chart factory (DARK_LAYOUT + dual-axis builder) and two Streamlit pages wiring the full data-to-dark-chart pipeline via theme=None**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-08T14:32:19Z
- **Completed:** 2026-05-08T14:34:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- utils/charts.py: zero-Streamlit Plotly factory with DARK_LAYOUT, build_timeseries_chart(), build_dual_axis_chart()
- pages/1_Data_Overview.py: 4-column st.metric KPI row + filtered DISPLAY_COLUMNS dataframe with sidebar
- pages/2_Production_Explorer.py: 4 stacked dark Plotly charts (oil/gas/water cut/WHP+choke) with sidebar

## Task Commits

Each task was committed atomically:

1. **Task 1: Build Plotly dark figure factory** - `230a933` (feat)
2. **Task 2: Build Data Overview and Production Explorer pages** - `d759c9c` (feat)

**Plan metadata:** (pending — docs commit below)

## Files Created/Modified
- `utils/charts.py` - Dark Plotly figure factory; DARK_LAYOUT, build_timeseries_chart, build_dual_axis_chart
- `pages/1_Data_Overview.py` - Data Overview Streamlit page; KPI cards + DISPLAY_COLUMNS table + sidebar
- `pages/2_Production_Explorer.py` - Production Explorer page; 4 stacked dark Plotly charts + sidebar

## Decisions Made
- Plotly 6.0.0 removed `titlefont` property for yaxis — updated to `title=dict(text=..., font=dict(color=...))` per new API
- Data Overview page intentionally has no `st.plotly_chart` calls — data table page uses `st.dataframe` only
- Sidebar block is structurally identical across both pages (well name, date range, 3 st.metric calls)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Plotly 6.0.0 API breaking change: titlefont removed from yaxis**
- **Found during:** Task 1 (build_dual_axis_chart verification)
- **Issue:** `titlefont=dict(color=...)` was a valid Plotly 5 property; Plotly 6.0.0 removed it entirely, raising `ValueError: Invalid property specified for object of type plotly.graph_objs.layout.YAxis: 'titlefont'`
- **Fix:** Replaced `titlefont=dict(color=y1_color)` with `title=dict(text=y1_label, font=dict(color=y1_color))` for both yaxis and yaxis2
- **Files modified:** utils/charts.py
- **Verification:** `CHARTS OK` printed by automated verify command; len(fig2.data)==2 confirmed
- **Committed in:** 230a933 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix for Plotly 6.0 API change)
**Impact on plan:** Required fix — plan code was written for Plotly 5 API. titlefont is gone in Plotly 6.0.0. Fix preserves all intended visual behavior (axis title colors).

## Issues Encountered
- plotly not installed in local environment (it's in requirements.txt for Docker). Installed with `pip install plotly==6.0.0` to run verification — no code change needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- utils/charts.py is the chart factory for all pages including the DCA Forecast page (Plan 05)
- Both pages are syntactically valid and will be served by Streamlit once app.py is wired (Plan 05)
- Sidebar KPI pattern established — Plan 05 DCA page should use identical sidebar block
- No blockers for Plan 05

---
*Phase: 01-full-build*
*Completed: 2026-05-08*
