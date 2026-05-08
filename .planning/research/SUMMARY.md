# Project Research Summary

**Project:** Volve DCA Forecasting App — Streamlit webinar demo
**Domain:** Petroleum engineering / oil production decline curve analysis (DCA) — interactive teaching tool
**Researched:** 2026-05-08
**Confidence:** HIGH

## Executive Summary

This is a teaching-oriented Streamlit web app that walks petroleum engineers (and students) through Arps decline curve analysis using the publicly available Volve field dataset (well 15/9-F-12). Research confirms that the standard industry approach to DCA is empirical Arps fitting — exponential (b=0), hyperbolic (0<b<1), and harmonic (b=1) — using scipy.optimize.curve_fit with domain-informed initial guesses and physical bounds. The app's competitive differentiation is not feature parity with commercial tools (whitson+, ResInsight) but the pedagogical layer: live-updating Arps equations, plain-English model explanations, and slider-driven sensitivity that makes DCA intuition tangible to an audience in a projector room.

The recommended approach is a three-page Streamlit multi-page app (Data Overview, Production Explorer, DCA Forecast) with a clean utils/ layer (data.py, dca.py, charts.py) that keeps all DCA math and chart construction as pure Python, wired to the UI only in the page scripts. Deployment target is HuggingFace Spaces using the Docker SDK — the native Streamlit SDK was deprecated April 30, 2025 and cannot be used for new Spaces. The app pins Python 3.11, Streamlit 1.52.0, Plotly 6.x, pandas 2.2.3, numpy 1.26.4, and scipy 1.17.1 in requirements.txt to guarantee reproducible builds.

The dominant risks are concentrated in two areas: (1) DCA math correctness — the harmonic singularity at b=1, wrong cumulative formulas per model type, and optimizer convergence failure from poor initial guesses are all silent bugs that produce plausible-looking but wrong results, and (2) Streamlit + HuggingFace integration — the deprecated Streamlit SDK, port 8501 vs 7860 confusion, the theme=None requirement for Plotly dark charts, and the slider/session_state double-binding exception. Both risk areas must be resolved before any UI is wired up, not discovered during a live demo.

---

## Key Findings

### Recommended Stack

The binding constraint is scipy 1.17.1, which requires Python 3.11+. This sets the Docker base image to FROM python:3.11. HuggingFace Spaces no longer accepts sdk: streamlit in README.md for new Spaces (deprecated April 30, 2025); all new deployments must use sdk: docker with a Dockerfile that exposes port 8501. The recommended pin set is stable, widely tested, and avoids the breaking changes in pandas 3.x and plotly 6.x that could silently corrupt an app on rebuild.

**Core technologies:**
- Python 3.11: Runtime — required by scipy 1.17.1 and numpy 2.x; sets the Dockerfile base image
- Streamlit 1.52.0: App framework — reactive rerun model eliminates manual event wiring for slider-driven charts; pin this exact version to avoid surprise breakage on HF Spaces rebuild
- Plotly 6.x (pin 6.0.0): Interactive charts — the only choice for dark-themed, zoomable, projector-ready charts; must use theme=None in st.plotly_chart() to prevent Streamlit default theme from overriding plotly_dark
- pandas 2.2.3: Data wrangling — safest pin for this app's simple CSV/date/resample operations; Copy-on-Write enabled, no breaking changes vs 2.x API
- numpy 1.26.4: Numerical arrays — lowest-common-denominator pin compatible with pandas 2.2.3 and scipy 1.17.1
- scipy 1.17.1: Arps curve fitting — scipy.optimize.curve_fit with method='trf', physical bounds, and domain-informed p0 is the industry-standard tool; use lmfit 1.3.4 optionally if confidence interval bands on parameters are needed

**Critical version note:** Use width="stretch" instead of use_container_width=True in st.plotly_chart() — the latter is removed after 2025-12-31. Use sdk: docker and app_port: 8501 in README.md YAML — not sdk: streamlit.

### Expected Features

The 15 P1 features form the complete MVP for the webinar demo. The feature dependency chain is strict: data must be loaded and filtered before DCA fitting, auto-fit must run before sliders are initialized, and EUR requires both an abandonment rate input and the correct cumulative formula for the active model type. P2 features (semi-log toggle, cumulative Np chart, on-stream normalization toggle, live Arps equation display) add high teaching value at low implementation cost and should follow immediately once the P1 core is stable.

**Must have (table stakes — P1):**
- Raw data table + summary statistics (date range, row count, P10/P50/P90) — first QC step engineers perform
- Time-series charts: oil, gas, water volumes, wellhead pressure (AVG_WHP_P), water cut — the foundational production story
- Date-range selector for DCA analysis window — teaches "choose stabilized decline, not transient flow"
- All three Arps models (exponential, hyperbolic, harmonic) with radio selector and plain-English description
- Auto-fit via scipy.optimize.curve_fit with domain-informed p0 and physical bounds — one-click starting point
- Manual sliders for qi, Di, b — live chart update; sliders initialized from auto-fit results via session_state
- Forecast chart: historical scatter + fitted curve + dashed forecast line — the core deliverable
- EUR (Sm3) with abandonment rate input and forecast horizon slider
- Goodness-of-fit: R-squared and RMSE displayed alongside fitted parameters
- Dark Plotly theme throughout with theme=None — projector-ready

**Should have (differentiators — P2, add when P1 core is stable):**
- Semi-log y-axis toggle — exponential decline is a straight line on semi-log; powerful teaching visual
- Cumulative production (Np vs time) chart — visual validation of EUR; area fill shows remaining reserves
- On-stream hours normalization toggle — removes shut-in noise from decline trend; standard practice
- Live Arps equation display (st.latex updating with slider values) — makes the math tangible for the audience
- Highlighted fit window shading on main chart (Plotly vrect) — shows what data drove the fit

**Defer (v2+):**
- GOR vs cumulative oil diagnostic plot — reservoir drive mechanism analysis; beyond webinar scope
- Water injection overlay (F-4, F-5 injectors) — good reservoir story, adds chart complexity
- DCA parameter CSV export — useful for reuse; not needed for live demo
- Multi-model comparison overlay — shows all three Arps fits simultaneously; second-pass feature

**Deliberately excluded (anti-features):**
- ML-based forecasting (XGBoost, LSTM) — different conceptual framework, balloons Docker image size
- Multi-well comparison — dataset has one production well; faking it adds no value
- Custom CSV upload — column mapping UI distracts from the Volve dataset story
- P10/P50/P90 probabilistic forecasts — dilutes the core DCA teaching moment
- b > 1 super-hyperbolic — Volve is conventional; constraining b to [0, 1] is correct and pedagogically cleaner

### Architecture Approach

The app uses Streamlit multi-page architecture (st.navigation + pages/ directory) with strict separation between pure-Python utilities (utils/) and Streamlit page scripts (pages/). No st.* calls appear inside utils — this keeps DCA math and chart factories independently testable. The data layer loads once via @st.cache_data and is shared across all sessions; all filtering and derivations happen in normal script flow per user. DCA parameters persist via st.session_state with key-only binding pattern (never value= + key= simultaneously on sliders). Build order follows the dependency graph: static assets then utils/data.py then utils/dca.py then utils/charts.py then pages then app.py router.

**Major components:**
1. utils/data.py — CSV load (cached), date parsing with explicit format, shut-in filtering (ON_STREAM_HRS > 0), derived columns (water cut, normalized rate)
2. utils/dca.py — Three separate Arps q(t) functions, three separate cumulative Np(t) functions, scipy.optimize.curve_fit wrapper with bounds and domain p0, EUR calculator integrating to abandonment rate
3. utils/charts.py — Plotly dark figure factory; consistent DARK_LAYOUT dict with explicit bgcolor, font color, gridcolor applied to every figure; pages call chart builders, not raw go.Figure()
4. pages/1_Data_Overview.py — Raw data table, date range assertion, summary statistics; simplest page; validates app structure
5. pages/2_Production_Explorer.py — Time-series charts for oil/gas/water/pressure/water cut; wires data.py + charts.py
6. pages/3_DCA_Forecast.py — DCA analysis window selector, auto-fit button, slider panel, forecast chart, EUR display; most complex page; wires all three utils; owns all session_state
7. app.py — Thin router only; st.navigation pointing at all three pages; sidebar chrome; zero business logic

### Critical Pitfalls

1. **Harmonic b=1 singularity producing infinite EUR** — Implement three separate, explicitly dispatched functions (exponential, hyperbolic, harmonic). Never use a single Arps function with b as a free parameter across all three modes. Guard with abs(b - 1.0) < 0.01. Always integrate EUR to an economic-limit rate, not infinite time. Test this before any UI is wired.

2. **Wrong cumulative production formula per model type** — Each Arps model has a distinct analytically derived cumulative Np formula. Using the exponential formula for all three understates EUR for hyperbolic wells. Validate EUR against hand-calculated values before connecting to UI.

3. **Optimizer convergence failure from poor initial guesses** — Default p0=None (all-ones) in curve_fit places the starting point nowhere near physically realistic Arps values. Always set domain-informed p0: qi_0 = data.iloc[0], Di_0 = 0.01, b_0 = 0.5. Set strict physical bounds and use method='trf'. Catch OptimizeWarning and RuntimeError and surface them in the UI.

4. **Shut-in zeros corrupting DCA fit** — The Volve dataset contains approximately 20-40% zero-production rows. Filter ON_STREAM_HRS > 0 and apply a minimum production threshold before passing data to the fitting function.

5. **Plotly dark theme silently overridden by Streamlit** — Always pass theme=None to st.plotly_chart(). Explicitly set paper_bgcolor, plot_bgcolor, font_color, gridcolor in fig.update_layout(). Test on a dark-background display during development.

6. **HuggingFace Spaces SDK deprecation and port mismatch** — Use sdk: docker with Dockerfile exposing port 8501. Do not set [server] port in .streamlit/config.toml. Use absolute file paths via Path(__file__).parent / "data" for CSV loading.

7. **Slider/session_state double-binding exception** — Use key= parameter only on st.slider(). Initialize session_state key before widget renders with a guard. Auto-fit writes fitted values directly to st.session_state before the slider renders, not inside an on_change callback.

---

## Implications for Roadmap

Based on combined research, the build order is strongly constrained by dependency and risk. DCA math correctness bugs are silent and devastating in a live demo — they must be caught before any UI is built. The architecture utils/pages separation means each layer can be validated independently before the next is wired up.

### Phase 1: Foundation and Data Pipeline

**Rationale:** All other phases depend on clean, correctly parsed data. The shut-in filtering pitfall and date parsing pitfall both live here. Catching them before building any UI means every subsequent phase works on a verified data layer. This phase is pure Python — no Streamlit.

**Delivers:** Verified data pipeline — CSV loads, dates parse correctly with assertion, shut-in rows are filtered, derived columns (water cut, on-stream normalized rate) are computed, and @st.cache_data is wired correctly.

**Addresses:** Raw data foundation for all features; prevents cache mutation pitfall.

**Avoids:** Shut-in zeros corrupting DCA fit (Pitfall 3), silent date parsing errors (Pitfall 9), cache mutation leaking state across users (Pitfall 10), relative file path failures on HF Spaces.

**Key tasks:** Implement utils/data.py with load_data(), explicit format= date parsing, filter_by_date(), ON_STREAM_HRS filter, derived column computations. Assert date bounds: min().year == 2007, max().year == 2016. Verify two-tab cache isolation.

### Phase 2: DCA Math Core

**Rationale:** This is the highest-risk phase and has zero Streamlit dependency. Validating Arps equations, EUR formulas, and optimizer behavior before wiring any UI means webinar-day bugs are caught weeks in advance, not on stage. The harmonic singularity and wrong cumulative formula pitfalls both live here.

**Delivers:** Fully tested utils/dca.py — three separate q(t) functions, three separate Np(t) cumulative functions, curve_fit wrapper with domain p0 and physical bounds, EUR function integrating to economic limit rate. Validate in a notebook with at least three date ranges from the Volve dataset.

**Addresses:** Auto-fit (qi, Di, b); all three Arps models; EUR display; goodness-of-fit (R-squared, RMSE).

**Avoids:** Harmonic b=1 singularity (Pitfall 1), wrong EUR cumulative formula (Pitfall 8), optimizer convergence failure from default p0 (Pitfall 2).

**Key tasks:** Implement and unit-test each Arps function independently. Confirm EUR changes when b changes. Confirm EUR does not return inf when b=1.0. Validate hand-calculated EUR against function output.

### Phase 3: Chart Factory and Dark Theme

**Rationale:** All three pages depend on the Plotly dark figure factory. Building and validating it before any page is wired ensures every chart is correct — the Plotly theme override pitfall is caught once, here, not rediscovered page by page.

**Delivers:** Verified utils/charts.py — build_production_chart() and build_dca_chart() with DARK_LAYOUT applied, tested with theme=None in Streamlit locally. Includes .streamlit/config.toml with base = "dark".

**Addresses:** Dark professional Plotly theme throughout; projector-ready presentation.

**Avoids:** Plotly dark template silently overridden by Streamlit (Pitfall 5). Establishes the reusable dark theme helper used by all subsequent pages.

### Phase 4: Deployment Setup

**Rationale:** Configure HuggingFace Spaces before page code is written. This eliminates port/SDK/entry-point pitfalls as variables during development — the deployment target is validated on Day 1 with a placeholder app, not discovered broken at delivery.

**Delivers:** Verified HF Spaces Docker deployment — Dockerfile (FROM python:3.11, port 8501), README.md with sdk: docker and app_port: 8501, requirements.txt with all versions pinned, packages.txt (empty), app.py placeholder. App loads on HF Spaces within 60 seconds of cold start.

**Addresses:** Deployment reliability; pre-webinar cold-start checklist.

**Avoids:** HF Spaces port misconfiguration (Pitfall 6), HF Spaces auto-sleep cold start during webinar (Pitfall 7), deprecated Streamlit SDK, unpinned dependency nondeterminism.

### Phase 5: Data Overview and Production Explorer Pages

**Rationale:** The two simpler pages (no session state complexity, no DCA math) are built first. They exercise the full data → chart pipeline end-to-end in a deployed Streamlit context and establish the multi-page routing pattern before the complex DCA page.

**Delivers:** pages/1_Data_Overview.py (raw data table, date range display, summary stats with named percentiles) and pages/2_Production_Explorer.py (time-series charts: oil/gas/water/wellhead pressure/water cut). Both deployed and confirmed working on HF Spaces.

**Addresses:** Raw data table + date range, time-series charts, wellhead pressure and choke, water cut — all P1 table-stakes features.

**Avoids:** Single-file app anti-pattern; Streamlit calls inside utils anti-pattern.

### Phase 6: DCA Forecast Page — Core Interactive

**Rationale:** This is the most complex page. It requires all previous phases to be complete and correct. The session state schema must be designed before any widget is coded — the slider/session_state conflict pitfall is design-time, not runtime.

**Delivers:** pages/3_DCA_Forecast.py — DCA analysis window selector, model radio selector with plain-English descriptions, Auto-fit button, manual sliders (key-only binding), forecast chart, EUR display (Sm3) with abandonment rate input, R-squared and RMSE metrics. Deployed and demoed end-to-end.

**Addresses:** All remaining P1 features: date-range selector, auto-fit, model selector, manual sliders, forecast chart, EUR, goodness-of-fit.

**Avoids:** Slider/session_state double-binding exception (Pitfall 4), re-fitting on every slider move (Architecture Anti-Pattern 2), forecast axis in days-since-start instead of calendar dates, EUR units in bbl instead of Sm3.

**Key tasks:** Design session_state schema before writing any widgets. Implement auto-fit as button-triggered only. Use key-only slider binding with pre-render initialization guards. Convert forecast time axis to calendar dates. Validate Sm3 units throughout. Two-tab cache safety test.

### Phase 7: P2 Enhancements and Pedagogical Polish

**Rationale:** Once the P1 demo works end-to-end on HF Spaces, add the pedagogical polish features. These are all low-complexity additions that require the P1 core to be stable. Sequence: semi-log toggle (lowest effort, highest teaching impact) then live Arps equation display then cumulative Np chart then on-stream normalization toggle.

**Delivers:** Semi-log y-axis toggle; live Arps equation display updating with sliders (st.latex); cumulative production (Np vs time) chart with area fill; on-stream hours normalization toggle with visible excluded-row count; fit window highlighted shading (Plotly vrect).

**Addresses:** All P2 features from FEATURES.md.

### Phase Ordering Rationale

- Phases 1-2 (data + math) must precede all UI work — silent correctness bugs in DCA math discovered after the UI is built require reworking two layers simultaneously
- Phase 3 (chart factory) before pages — Plotly dark theme issue is caught once, not per-page
- Phase 4 (deployment) before page development — port and SDK issues must not be surprises at delivery time
- Phase 5 (simple pages) before Phase 6 (DCA page) — validates multi-page routing and dark chart pipeline in a low-complexity environment
- Phase 7 (P2 enhancements) is additive polish on a stable foundation — never interleaved with core feature development

### Research Flags

Phases needing deeper investigation during implementation:

- **Phase 2 (DCA Math Core):** The Volve dataset actual decline period must be inspected before p0 defaults are set. Identify the clean decline window (estimated 2008-2012 from Volve literature) and confirm curve_fit converges on that range.
- **Phase 6 (DCA Forecast Page):** Slider range bounds (min/max for qi, Di) should be data-driven from the loaded dataset, not hardcoded. May need iteration on the session_state auto-fit → slider pre-population pattern.

Phases with standard well-documented patterns (skip additional research):

- **Phase 1 (Data Pipeline):** Standard pandas CSV load and filter pattern; fully documented in PITFALLS.md with explicit code.
- **Phase 3 (Chart Factory):** Standard Plotly dark template pattern; fully documented in STACK.md and PITFALLS.md.
- **Phase 4 (Deployment):** HF Spaces Docker SDK is fully documented; Dockerfile available from SpacesExamples.
- **Phase 5 (Simple Pages):** Standard Streamlit multi-page pattern; no novel integration.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations sourced from official HuggingFace, Streamlit, PyPI, and scipy docs. SDK deprecation date confirmed from official HF changelog. Version pins validated for cross-compatibility. |
| Features | HIGH | DCA feature set validated against whitson+, ResInsight, IHS Harmony, and CEDengineering course material. Arps (1945) is canonical; table-stakes features are well-established across all industry references. |
| Architecture | HIGH | Streamlit multi-page, caching, and session_state patterns sourced from official Streamlit docs. utils/pages separation is a well-established community pattern. DCA flow with scipy.curve_fit confirmed from multiple implementations. |
| Pitfalls | HIGH / MEDIUM | DCA math singularities (harmonic b=1, wrong Np formula) are analytically verifiable. Streamlit/HF pitfalls sourced from official docs and tracked GitHub issues. Volve dataset zero-row percentage (20-40%) comes from a Kaggle EDA — directionally HIGH confidence, exact percentage may vary. |

**Overall confidence:** HIGH

### Gaps to Address

- **Volve dataset actual decline period:** The clean decline window (without workovers or injection response distortion) needs to be confirmed by inspecting the actual data. The DCA date-range selector exists to let users pick this window, but Phase 2 testing should use the known best range.
- **Volve date format confirmation:** The DATEPRD column may use DD.MM.YYYY or YYYY-MM-DD. Inspect the actual CSV file before implementing the date parser to confirm the exact format string.
- **lmfit vs curve_fit decision:** Defer to Phase 2 once optimizer convergence behavior is tested on the actual Volve dataset. If curve_fit struggles, switch to lmfit at that point.
- **Sm3 vs bbl units:** The Volve dataset is Norwegian North Sea; volumes are in Sm3/day. Confirm units by inspecting the CSV header before building the DCA page. All EUR displays and axis labels must say Sm3, not bbl.

---

## Sources

### Primary (HIGH confidence)
- HuggingFace Spaces Changelog — SDK deprecation April 30, 2025: https://huggingface.co/docs/hub/en/spaces-changelog
- HuggingFace Spaces Streamlit SDK docs: https://huggingface.co/docs/hub/en/spaces-sdks-streamlit
- HuggingFace Docker Spaces docs: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- SpacesExamples/streamlit-docker-example (official Dockerfile): https://huggingface.co/spaces/SpacesExamples/streamlit-docker-example
- Streamlit 2025 Release Notes: https://docs.streamlit.io/develop/quick-reference/release-notes/2025
- st.plotly_chart API (theme=None, width=stretch): https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
- Streamlit session state docs: https://docs.streamlit.io/develop/concepts/architecture/session-state
- Streamlit caching docs: https://docs.streamlit.io/develop/concepts/architecture/caching
- Streamlit multi-page docs: https://docs.streamlit.io/develop/concepts/multipage-apps/overview
- scipy.optimize.curve_fit docs: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html
- Plotly templates docs: https://plotly.com/python/templates/
- whitson+ DCA manual: https://manual.whitson.com/modules/well-performance/decline-curve-analysis/
- IHS Harmony Decline Analysis Theory: https://www.ihsenergy.ca/support/documentation_ca/Harmony/content/html_files/reference_material/analysis_method_theory/decline_theory.htm
- PSU PNG 301 Harmonic Decline: https://www.e-education.psu.edu/png301/node/865
- ResInsight DCA docs: https://resinsight.org/plot-window/declinecurveanalysis/index.html
- CEDengineering DCA PDH course: https://www.cedengineering.com/userfiles/Forecasting%20Oil%20and%20Gas%20Using%20Decline%20Curves.pdf

### Secondary (MEDIUM confidence)
- SciPy issue #19180 (TRF method fails when p0 equals bound): https://github.com/scipy/scipy/issues/19180
- Streamlit issue #3925 (session state with sliders): https://github.com/streamlit/streamlit/issues/3925
- Streamlit issue #4178 (Plotly theme override): https://github.com/streamlit/streamlit/issues/4178
- Volve production data EDA (~40% zero rows): https://www.kaggle.com/code/imranulhaquenoor/volve-field-production-data-analysis-eda
- TechRando DCA with scipy curve_fit: https://techrando.com/2019/07/03/how-to-automate-decline-curve-analysis-dca-in-python-using-scipys-optimize-curve_fit-function/
- lmfit docs: https://lmfit.github.io/lmfit-py/

---
*Research completed: 2026-05-08*
*Ready for roadmap: yes*
