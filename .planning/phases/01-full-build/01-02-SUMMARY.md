---
phase: 01-full-build
plan: 02
subsystem: math
tags: [scipy, numpy, pandas, arps, dca, decline-curve-analysis, curve_fit, eur]

# Dependency graph
requires: []
provides:
  - exponential_q, hyperbolic_q, harmonic_q Arps rate functions
  - fit_arps() scipy curve_fit wrapper with domain-informed p0/bounds
  - calculate_eur() with harmonic guard (never returns inf/nan)
  - forecast_arps() with calendar-date DatetimeIndex x-axis
  - get_latex_equation() LaTeX strings for all three Arps model types
affects:
  - 01-full-build (plans 03-05 — DCA Forecast page, sidebar, HF deployment)

# Tech tracking
tech-stack:
  added: [scipy==1.17.1, pandas==3.0.2]
  patterns:
    - TDD RED/GREEN: write failing tests then minimal passing implementation
    - Harmonic guard pattern: abs(b-1.0) < 0.01 dispatches to harmonic to prevent singularity
    - p0 strictly inside bounds (qi_0 = q[0]*0.9) per scipy issue #19180
    - method='trf' required whenever curve_fit bounds are active
    - Zero st.* imports in math layer; display errors surface to caller

key-files:
  created:
    - utils/__init__.py
    - utils/dca.py
    - tests/test_dca.py
  modified: []

key-decisions:
  - "Three separate q(t) functions (not one universal with b parameter) — harmonic is a mathematical singularity, not just b=1"
  - "Harmonic guard abs(b-1.0)<0.01 applied in both calculate_eur() and forecast_arps() — prevents (1-b) denominator zero"
  - "EUR integrates to economic abandonment time (finite t_aband) not to infinity — guarantees finite result regardless of model"
  - "p0 uses q[0]*0.9 not q[0] exactly — scipy curve_fit fails when p0 equals bound per issue #19180"
  - "fit_arps() raises ValueError on convergence failure; caller owns st.error display"
  - "scipy and pandas installed as missing runtime dependencies (Rule 3 auto-fix)"

patterns-established:
  - "Rate-function separation: exponential_q/hyperbolic_q/harmonic_q are three distinct pure functions"
  - "Singularity guards: check b proximity before branching to prevent inf/nan"
  - "Calendar date forecasts: pd.to_datetime(t0) + pd.to_timedelta(t_arr, unit='D')"

requirements-completed: [DCA-01, DCA-02, DCA-03, DCA-04, FORE-01, FORE-02, FORE-03]

# Metrics
duration: 2min
completed: 2026-05-08
---

# Phase 1 Plan 02: DCA Math Core Summary

**Arps decline curve math core with scipy curve_fit wrapper, harmonic-guarded EUR (never inf), calendar-date forecasts, and LaTeX equation display for exponential, hyperbolic, and harmonic models**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-08T14:27:01Z
- **Completed:** 2026-05-08T14:29:00Z
- **Tasks:** 1 (with TDD RED + GREEN commits)
- **Files modified:** 3

## Accomplishments

- Three separate Arps q(t) functions (exponential_q, hyperbolic_q, harmonic_q) with analytically correct formulas
- scipy curve_fit wrapper (fit_arps) with domain-informed p0 strictly inside bounds, method='trf', and maxfev=10000
- calculate_eur() with harmonic guard at abs(b-1.0)<0.01 preventing infinite EUR at b≈1; verified: EUR_hyp=193,675 Sm3 > EUR_exp=99,900 Sm3 (physically correct)
- forecast_arps() returning calendar-date DatetimeIndex (not integer day offsets) truncated at economic limit
- get_latex_equation() producing LaTeX strings for all three model types for use with st.latex()
- All 12 TDD assertions pass; fit R2=1.0 on synthetic exponential data

## Task Commits

Each task was committed atomically:

1. **RED - Failing tests** - `b42ecac` (test)
2. **GREEN - DCA implementation** - `9f8ad25` (feat)

_TDD task: test commit (RED) followed by implementation commit (GREEN)_

## Files Created/Modified

- `utils/__init__.py` - Package marker
- `utils/dca.py` - Complete Arps DCA math core (259 lines, zero st.* imports)
- `tests/test_dca.py` - 12 TDD assertions covering all exported functions

## Decisions Made

- Three separate q(t) functions chosen over a universal b-parameterized function — harmonic is a mathematical singularity (b=1 makes (1-b)=0), not a degenerate case
- Harmonic guard abs(b-1.0)<0.01 applied in both calculate_eur() and forecast_arps() for consistency
- EUR uses analytical t_aband solution (solves q(t)=q_aband for t) rather than numerical integration — exact and faster
- p0 uses q[0]*0.9 per scipy issue #19180 — p0 at exact boundary silently fails convergence
- ValueError raised on fit failure; st.error display delegated to the page layer

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing scipy and pandas runtime dependencies**
- **Found during:** Task 1 verification (GREEN phase)
- **Issue:** scipy and pandas not installed in the Python environment; import would fail
- **Fix:** Ran `pip3 install scipy pandas` — scipy 1.17.1 and pandas 3.0.2 installed
- **Files modified:** system Python environment
- **Verification:** `python3 -c "import scipy, pandas"` succeeds; all 12 assertions pass
- **Committed in:** Dependency install only; no source file changes

---

**Total deviations:** 1 auto-fixed (1 blocking dependency)
**Impact on plan:** Essential — scipy is the only method to run curve_fit. No scope creep.

## Issues Encountered

None — plan executed cleanly after dependency installation.

## User Setup Required

None - no external service configuration required. scipy and pandas are standard scientific Python libraries.

## Next Phase Readiness

- utils/dca.py is ready for import by the DCA Forecast page (plan 03)
- utils/__init__.py package marker enables `from utils.dca import ...`
- No st.* calls in the math layer — pages own display logic
- Blocker from STATE.md resolved: harmonic singularity guard confirmed working (b=0.99 gives finite EUR=193,675 Sm3)

---
*Phase: 01-full-build*
*Completed: 2026-05-08*
