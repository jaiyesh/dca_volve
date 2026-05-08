---
phase: 01-full-build
plan: "01"
subsystem: data
tags: [pandas, streamlit, csv, volve, cache_data]

# Dependency graph
requires: []
provides:
  - load_data() returning 2901 producing-day rows from Volve PF-12 CSV
  - filter_by_date() for date-range subsetting of production DataFrame
  - get_sidebar_kpis() returning well KPIs for sidebar display
  - WATER_CUT derived column bounded [0, 1]
  - utils package initialized
affects: [all subsequent pages relying on utils.data]

# Tech tracking
tech-stack:
  added: [pandas, streamlit (st.cache_data)]
  patterns: [Path(__file__).parent.parent for CSV path, @st.cache_data on data loader, explicit date format string]

key-files:
  created:
    - utils/__init__.py
    - utils/data.py
  modified: []

key-decisions:
  - "Use Path(__file__).parent.parent for CSV path — required for HuggingFace Spaces Docker environment"
  - "Use format='%d-%b-%y' explicitly for DATEPRD parsing — no pandas date inference"
  - "Filter ON_STREAM_HRS > 0 before return; produces 2901 rows from 3305 raw"
  - "All 122 Sept 2007 rows are shut-in (ON_STREAM_HRS=0); min producing year is 2008, not 2007"
  - "WATER_CUT derived as BORE_WAT_VOL / (BORE_OIL_VOL + BORE_WAT_VOL), clipped [0,1]"

patterns-established:
  - "Data loading: use @st.cache_data on load_data() only; no other st.* calls in utils/"
  - "Date filter: return df.loc[mask].copy() — never use inplace=True on cached DataFrames"
  - "CSV path: always use Path(__file__).parent.parent / filename, never relative string paths"

requirements-completed: [DATA-01]

# Metrics
duration: 3min
completed: 2026-05-08
---

# Phase 1 Plan 01: Data Pipeline Summary

**Volve PF-12 CSV pipeline with @st.cache_data, explicit date parsing, shut-in filter, and WATER_CUT derivation returning 2901 verified producing-day rows**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-08T14:26:52Z
- **Completed:** 2026-05-08T14:29:12Z
- **Tasks:** 1
- **Files modified:** 2 created

## Accomplishments
- Created `utils/__init__.py` as empty package marker enabling `from utils.data import ...`
- Created `utils/data.py` with `load_data()`, `filter_by_date()`, `get_sidebar_kpis()` — no st.* calls except `@st.cache_data`
- `load_data()` parses DATEPRD with format `'%d-%b-%y'`, filters to 2901 producing rows, computes WATER_CUT bounded [0,1]
- `get_sidebar_kpis()` confirmed: peak rate 5902 Sm3/day on 08 Jan 2009, total oil 4.614 MSm3

## Task Commits

Each task was committed atomically:

1. **Task 1: Create utils package and data loading module** - `8c914be` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `utils/__init__.py` - Empty package marker
- `utils/data.py` - load_data(), filter_by_date(), get_sidebar_kpis() with verified data pipeline

## Decisions Made
- Used `Path(__file__).parent.parent` for CSV path — required for HuggingFace Spaces Docker environment where working directory is unpredictable
- Explicit `format='%d-%b-%y'` on pd.to_datetime — avoids pandas inference silently misreading ambiguous dates
- Internal assertions in `load_data()` check raw pre-filter date range (2007–2016); returned DataFrame min year is 2008 because all 2007 rows have ON_STREAM_HRS=0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Verification script date assertion corrected**
- **Found during:** Task 1 verification
- **Issue:** The plan's automated verification script asserted `df['DATEPRD'].min().year == 2007` on the post-filter DataFrame. After applying `ON_STREAM_HRS > 0`, all 122 September 2007 rows are removed (all shut-in), making min year 2008.
- **Fix:** The internal `load_data()` assertions correctly check raw pre-filter dates (2007–2016). The function implementation is correct. The verification expectation in the plan was based on a misunderstanding of what the post-filter data looks like. No code change needed — verified with corrected expectation (min producing year = 2008).
- **Files modified:** None (plan's test spec was incorrect, not the implementation)
- **Verification:** All 6 KPI assertions passed including 2901 rows, WATER_CUT [0,1], peak 5902, filter_by_date narrows to 350 rows for 2009
- **Committed in:** 8c914be

---

**Total deviations:** 1 auto-identified (plan spec bug — min year assertion)
**Impact on plan:** Zero scope creep. Implementation is correct per CSV data reality. The must_have truth "min year 2007" refers to raw CSV date range, not post-filter producing range.

## Issues Encountered
- streamlit not installed in test environment — installed via pip3 before verification. Not a code issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `utils.data` module is complete and verified; all downstream pages can import `load_data`, `filter_by_date`, `get_sidebar_kpis`
- WATER_CUT column ready for injection/production ratio plots
- 2901-row producing DataFrame ready for DCA fitting pipeline
- Concern from STATE.md resolved: DATEPRD format confirmed as `DD-Mon-YY` (`%d-%b-%y`)

---
*Phase: 01-full-build*
*Completed: 2026-05-08*
