# Pitfalls Research

**Domain:** Streamlit DCA (Decline Curve Analysis) oil production forecasting app — Volve dataset, HuggingFace Spaces deployment
**Researched:** 2026-05-08
**Confidence:** HIGH (DCA math, Streamlit widget behavior, HF deployment) / MEDIUM (Plotly dark theme specifics, data quality)

---

## Critical Pitfalls

### Pitfall 1: Harmonic b=1 Mathematical Singularity — Infinite EUR

**What goes wrong:**
The general Arps hyperbolic equation `q(t) = qi / (1 + b*Di*t)^(1/b)` is mathematically undefined at b=1. When scipy fits a value of b close to 1.0 (or exactly 1.0), cumulative production integration diverges to infinity. EUR computation silently returns `inf` or `nan`, and the forecast chart either crashes with a divide-by-zero or shows an exponentially growing curve that makes no physical sense. This is particularly deceptive because the historical fit can look perfect while the forward projection is garbage.

**Why it happens:**
Developers implement a single hyperbolic function and assume scipy's `curve_fit` will return physically valid parameters. The harmonic case requires a separate closed-form equation (`q(t) = qi / (1 + Di*t)`) because the general form has a 1/b exponent that blows up. Without a branch in the code, b landing on or near 1 from the optimizer silently corrupts all downstream calculations.

**How to avoid:**
- Implement three separate, explicitly dispatched functions: exponential (b=0), harmonic (b=1), and hyperbolic (0<b<1).
- Add a guard: `if abs(b - 1.0) < 0.01: use_harmonic_equations()`.
- For hyperbolic EUR, always integrate to a terminal (economic-limit) rate, not to infinite time. Use `q_min = 1.0` Sm³/day as a hard floor.
- Display EUR as "EUR to economic limit (X Sm³/day)" — never as a bare number without context.

**Warning signs:**
- EUR display shows `inf`, `nan`, or an astronomically large number (>10× cumulative historical production).
- The forecast line trends upward or is completely flat on a log scale.
- `scipy.optimize.curve_fit` returns a b parameter exactly at a bound (0, 1, or 5).

**Phase to address:** DCA fitting implementation phase (core calculation layer), before any UI is wired up.

---

### Pitfall 2: Optimizer Converges on Wrong Local Minimum — Bad DCA Fit

**What goes wrong:**
`scipy.optimize.curve_fit` with default initial guesses (p0=None defaults to all-ones) regularly converges on a local minimum that fits the noise rather than the decline trend, or returns parameters at their bounds (b pinned to 0 or 5, Di pinned to minimum). The resulting curve visually misses the data. In a live webinar this is catastrophic — the auto-fit button produces a nonsensical curve and the presenter must scramble to explain it.

**Why it happens:**
Arps hyperbolic has a highly non-convex loss surface in (qi, Di, b) space. The qi parameter spans orders of magnitude (10–10,000 Sm³/day), Di is small (0.001–0.1 per day), and b is 0–1. Default p0=[1,1,1] places the starting point nowhere near the solution, causing the Levenberg-Marquardt algorithm to wander into a bad basin. Without bounds, the optimizer can also produce negative Di (implying production increases with time) or b>5.

**How to avoid:**
- Always provide a domain-informed `p0`: `qi_0 = data.iloc[0]` (first non-zero value in selected range), `Di_0 = 0.01` (1%/day is a reasonable starting decline), `b_0 = 0.5`.
- Set strict physical bounds: `bounds=([0, 1e-6, 0], [qi_0*2, 1.0, 2.0])`. Di upper bound of 1.0/day prevents unrealistic hypercurvature. b upper bound of 2.0 allows edge cases without permitting infinity.
- Switch optimizer to `method='trf'` (Trust Region Reflective) when bounds are active — it is numerically more stable than the default Levenberg-Marquardt at boundaries.
- Normalize time axis before fitting: `t_norm = t / t.max()`. This keeps all variables in the same order of magnitude and avoids floating point scale issues.
- Catch `scipy.optimize.OptimizeWarning` and `RuntimeError` and surface them in the UI with a clear message rather than silently continuing with bad parameters.

**Warning signs:**
- Fitted parameter b lands exactly at 0 or at the upper bound.
- Fitted Di is negative.
- R² of the fit is below 0.7.
- The fitted curve is obviously steeper or shallower than the data on a linear plot.

**Phase to address:** DCA fitting implementation phase. Test with at least three date ranges from the Volve dataset (early high-rate, mid-life, late low-rate) before building the UI.

---

### Pitfall 3: Zero-Production and Shut-In Periods Corrupting the DCA Fit

**What goes wrong:**
The Volve well 15/9-F-12 dataset contains substantial periods of zero BORE_OIL_VOL — known from analysis of the Volve Kaggle dataset where wells show 20–40% zero-production rows that are not nulls but actual zero values from shut-in periods. Including these zeros in the Arps fitting causes the optimizer to fit a declining curve toward zero much faster than the actual reservoir decline, producing an overly pessimistic forecast and an underestimated EUR. The effect is amplified because early shut-in events weight heavily in least-squares fitting.

**Why it happens:**
Raw CSV data is fed directly to `curve_fit` without filtering. Developers assume all rows represent flowing conditions. Shut-in days (ON_STREAM_HRS = 0, or near zero) look like rapid production drops to the optimizer, not operational interruptions.

**How to avoid:**
- Filter on `ON_STREAM_HRS > 0` before passing data to the fitting function. This column in the Volve dataset reliably identifies active production days.
- Apply a minimum production threshold filter: drop rows where `BORE_OIL_VOL < 1.0` Sm³/day (or user-configurable economic limit).
- Normalize daily volumes: `daily_rate = BORE_OIL_VOL / (ON_STREAM_HRS / 24)` converts volumetric totals to actual flowing rate, removing the distortion of partial production days.
- Offer the user a toggle in the UI: "Exclude shut-in periods" with a visible count of excluded rows.
- In the fit date-range selector, show a chart of raw data so the user can see and avoid selecting a range dominated by shut-ins.

**Warning signs:**
- Fitted `qi` (initial rate) is much lower than the actual peak rate in the selected range.
- The fit date range includes obvious flat-zero sections visible in the production chart.
- R² appears high but the fitted curve passes through the zeros rather than the productive data.

**Phase to address:** Data loading and cleaning phase (must be solved before DCA fitting is implemented).

---

### Pitfall 4: Streamlit Widget–Session State Conflict Causing Slider Resets or Double-Execution

**What goes wrong:**
The three DCA sliders (qi, Di, b) need to be pre-populated with fitted values when auto-fit runs, and then remain independently adjustable. The classic failure mode: after auto-fit writes fitted values to `st.session_state`, the slider widget re-renders with those values but immediately resets to default on the next interaction. Alternatively, setting both `value=st.session_state['qi']` and `key='qi'` in the same `st.slider()` call raises a `StreamlitAPIException` and crashes the app.

A second failure mode: the auto-fit button triggers a full re-run, which re-evaluates the slider widget, which triggers another re-run via the `on_change` callback — creating an infinite render loop that spins the UI until the user refreshes.

**Why it happens:**
Streamlit prohibits setting a widget's value via both the `value` parameter and `st.session_state[key]` simultaneously. Developers instinctively do both, thinking one is a default and the other is a live override. The re-render loop happens when a callback modifies state that causes the widget to re-render, which triggers the callback again.

**How to avoid:**
- Use the `key` parameter exclusively to bind sliders to session state. Never pass both `value=` and `key=` to the same slider. Initialize the key in session state before the widget renders: `if 'qi' not in st.session_state: st.session_state['qi'] = default_value`.
- Update session state from auto-fit using a dedicated callback or by directly setting `st.session_state['qi'] = fitted_qi` before the slider is rendered — not inside an `on_change` callback of the slider itself.
- To avoid render loops: auto-fit should write results to a separate namespace (e.g., `st.session_state['fit_results']`) and the slider reads from it once during initialization only. Do not create circular dependencies between fitted results and slider values.
- Validate: if `min_value` or `max_value` of a slider needs to change (e.g., qi range adapts to data), be aware that changing these bounds resets the slider's value even when a key is assigned — Streamlit explicitly documents this as intended behavior.

**Warning signs:**
- Slider jumps back to default after auto-fit button is clicked.
- App shows a spinner indefinitely after a slider interaction.
- `StreamlitAPIException: Values for st.slider must be set either through the widget or via session_state, not both.` error in logs.
- Repeated "Running..." indicator visible in the top-right corner during slider drag.

**Phase to address:** Interactive fine-tuning phase (slider UI). Design the session state schema before writing any widget code.

---

### Pitfall 5: Streamlit's Default Theme Overriding Plotly's `plotly_dark` Template

**What goes wrong:**
`st.plotly_chart(fig)` with a `plotly_dark` template produces charts that look correct in a standalone Plotly HTML context but broken in Streamlit. Specifically: axis tick labels render in near-invisible dark-grey on dark backgrounds, the plot background reverts to Streamlit's default light grey instead of the dark chart background, and legend text becomes unreadable. On a projector in a dimly lit webinar room this is a presentation disaster.

**Why it happens:**
Since Streamlit 1.16.0, `st.plotly_chart` applies a `theme="streamlit"` override by default that injects Streamlit's color palette into the Plotly figure, overriding `paper_bgcolor`, `plot_bgcolor`, font colors, and grid colors set in the Plotly template. The `plotly_dark` template's color settings are silently discarded.

**How to avoid:**
- Pass `theme=None` to `st.plotly_chart(fig, theme=None)` to disable Streamlit's theme injection and let the Plotly template take full effect.
- Explicitly set all critical color properties in `fig.update_layout()` — never rely on template defaults alone: `paper_bgcolor='#0e1117'`, `plot_bgcolor='#0e1117'`, `font_color='#ffffff'`, `xaxis_gridcolor='#333333'`, `yaxis_gridcolor='#333333'`.
- Set `xaxis_tickfont_color='#cccccc'` and `yaxis_tickfont_color='#cccccc'` explicitly.
- Test the chart on a projector (or simulate with a dark background) during development, not just on a bright monitor.
- For the `.streamlit/config.toml`, set `[theme] base = "dark"` to make the Streamlit chrome match the dark chart aesthetic.

**Warning signs:**
- Chart background is light grey while the chart template is `plotly_dark`.
- Axis labels disappear or appear as very dark text on dark background.
- Legend items are clipped or overlap with the chart area.
- Chart looks correct in a Jupyter notebook but broken in the Streamlit app.

**Phase to address:** Chart and visualization phase (first chart built). Establish a reusable `apply_dark_theme(fig)` helper function and use it for all charts.

---

### Pitfall 6: HuggingFace Spaces Port and Entry Point Misconfiguration

**What goes wrong:**
The app deploys but is inaccessible (504 timeout / blank page) because the Streamlit server is running on the wrong port or the entry point file is named incorrectly. HuggingFace Spaces requires the Streamlit app to listen on port 8501 — any `config.toml` that overrides this (e.g., `[server] port = 7860`) breaks the routing layer. Similarly, HF Spaces expects `app.py` as the entry point by convention; a file named `main.py` or `streamlit_app.py` will not be auto-detected.

**Why it happens:**
Developers copy Docker deployment patterns (port 7860 is the Docker Spaces default) into Streamlit Spaces. The HF documentation is clear about port 8501 but it is easy to miss the warning, especially when adapting from a Docker workflow.

**How to avoid:**
- If a `.streamlit/config.toml` exists, do not set `[server] port`. Let it default to 8501.
- Name the entry file `app.py` at the repository root.
- The `README.md` YAML front-matter must contain `sdk: streamlit` and `app_file: app.py`. Verify this block exists and is syntactically valid (indentation matters in YAML).
- Test that the app runs locally with `streamlit run app.py` before pushing to HF Spaces — this confirms the entry point is correct.

**Warning signs:**
- HF Spaces build log shows "App is running" but the App tab shows a blank page or timeout.
- Build log line shows the server bound to a port other than 8501.
- `sdk_version` in README.md specifies an unsupported Streamlit version (check against HF's supported version list).

**Phase to address:** Deployment configuration phase (set up before first push, not as an afterthought).

---

### Pitfall 7: HuggingFace Spaces Free Tier Auto-Sleep and Cold Start During Webinar

**What goes wrong:**
HF Spaces free tier (CPU Basic: 2 vCPU, 16GB RAM) enters auto-sleep after 48 hours of inactivity. During a live webinar, if the presenter opens the app link for the first time in front of an audience, the cold-start rebuild takes 1–3 minutes, showing a "Building..." spinner. This is a live demo killer.

**Why it happens:**
HF Spaces free tier is designed for occasional demos, not always-on hosting. The auto-sleep is enforced at the platform level and cannot be disabled on the free tier.

**How to avoid:**
- Visit the app URL and interact with it within 30 minutes before the webinar goes live. This keeps it warm.
- Add a lightweight no-op keepalive: document the "wake-up" URL and check it as part of the pre-webinar checklist.
- Cache the CSV load with `@st.cache_data` so that even after a cold restart, the data is loaded once and cached for all subsequent interactions in that session. Without this, every slider move reloads the CSV from disk.
- Consider upgrading to a paid tier (CPU Upgrade: $0.06/hour) for the webinar window if reliability is critical.

**Warning signs:**
- HF Spaces App tab shows "Building..." or a spinning indicator for more than 30 seconds when opening.
- App is unresponsive immediately after wake-up (memory being re-allocated).

**Phase to address:** Deployment and performance phase.

---

### Pitfall 8: EUR Calculation Using Wrong Cumulative Production Formula for the Decline Type

**What goes wrong:**
EUR is computed using the exponential cumulative formula `Np = (qi - q) / Di` even when b ≠ 0, producing a value that is too low (exponential declines faster than hyperbolic). Alternatively, hyperbolic cumulative `Np = (qi^b / ((1-b)*Di)) * (qi^(1-b) - q^(1-b))` is applied but integrated to infinite time instead of to the economic-limit rate, giving an inflated or infinite result. Both errors are invisible to non-petroleum-engineers in a webinar audience, but petroleum engineers in the room will immediately notice.

**Why it happens:**
The three Arps model types have three distinct cumulative production equations. Developers unfamiliar with the derivation copy the exponential formula for all cases, or use a generic numerical integrator (`np.trapz`) on the forecast array — which gives correct results only if the forecast time array extends exactly to the economic limit, not beyond.

**How to avoid:**
- Implement three separate, analytically derived cumulative production functions matching the dispatch pattern for q(t).
- For EUR, always integrate to a defined `q_abandonment` (e.g., 1 Sm³/day or user-configurable economic limit), not to a fixed time horizon. The time to reach `q_abandonment` is derived analytically from the Arps equations, not from a fixed number of months.
- Display EUR unit clearly: "EUR = X,XXX Sm³" (not bbl — the Volve dataset is in Sm³/day). Avoid unit confusion in a Norwegian North Sea context.
- Show cumulative production to date alongside EUR to give engineers a sanity check: EUR should always exceed already-produced cumulative.

**Warning signs:**
- EUR is lower than cumulative historical production (physically impossible).
- EUR does not change when b changes (indicates wrong formula branch is executing).
- EUR shows as `inf` (harmonic without economic limit).
- EUR unit displayed as "bbl" when source data is in Sm³.

**Phase to address:** DCA fitting and forecast phase. Validate EUR against hand-calculated values for a simple test case before connecting to UI.

---

### Pitfall 9: Pandas Date Parsing Silently Producing Wrong Dates for DATEPRD Column

**What goes wrong:**
The Volve CSV DATEPRD column may use a `DD.MM.YYYY` or `YYYY-MM-DD` format. When loaded with `pd.read_csv(..., parse_dates=['DATEPRD'])` without an explicit `format=` argument, pandas uses its inference logic. If the first rows are ambiguous (e.g., `01.02.2008` could be Jan 2nd or Feb 1st), pandas may commit to the wrong format and silently parse the rest of the file incorrectly, shifting all dates by 30+ days. The production time-series chart then shows the decline shifted in time — a subtle bug that looks like a data error, not a code error.

**Why it happens:**
`parse_dates=True` in `read_csv` triggers pandas' autodetect, which uses the first few rows to determine format. The Volve dataset uses European date notation (day-first), but pandas defaults to US notation (month-first) unless told otherwise.

**How to avoid:**
- Use an explicit `format` string: `pd.to_datetime(df['DATEPRD'], format='%d.%m.%Y')` (or the actual format found in the file — inspect it first).
- Alternatively use `dayfirst=True` in `pd.to_datetime()`.
- After parsing, assert sanity: `assert df['DATEPRD'].min().year == 2007` and `assert df['DATEPRD'].max().year == 2016` — these are known bounds for the Volve dataset.
- Sort by DATEPRD after loading (`df.sort_values('DATEPRD', inplace=True)`) since CSV row order is not guaranteed to be chronological.

**Warning signs:**
- Date range shown in data overview tab says something other than "Sept 2007 – Sept 2016".
- Production chart shows a suspicious gap or period reversal.
- Any date in the "month" position exceeds 12 (immediate indicator of day/month swap).

**Phase to address:** Data loading and cleaning phase — validate immediately after first `pd.read_csv` call.

---

### Pitfall 10: `st.cache_data` Cache Shared Across All Users — Mutable State Leaking Between Sessions

**What goes wrong:**
`@st.cache_data` is safe for immutable DataFrames (the CSV load). However, if the cached function returns a mutable object that is then modified by the app (e.g., appending a column, filtering in-place), Streamlit's copy-on-return mechanism is bypassed when the mutation happens inside the cache. One user's filtering operation then corrupts the data seen by subsequent users. In a webinar with many attendees watching the same shared HF Space, this can cause one user's date-range selection to affect everyone else's chart.

**Why it happens:**
`@st.cache_data` returns a deep copy on the first call, but developers sometimes cache intermediate DataFrames (not just the raw CSV) and then mutate them. The copy-on-return protection only applies at the boundary of the cached function return — mutations to the returned object are not protected.

**How to avoid:**
- Cache only the raw CSV load: `@st.cache_data def load_data(): return pd.read_csv(...)`. All filtering, date-range slicing, and column derivations should happen outside the cache in the normal script flow (Streamlit re-runs handle this per-user via session state).
- Never use `inplace=True` on a cached DataFrame.
- Test with two browser tabs open simultaneously: confirm that changing the date range in tab 1 does not affect the chart in tab 2.

**Warning signs:**
- Data in the chart changes unexpectedly when no interaction was performed.
- Column appears in the DataFrame that wasn't in the original CSV.
- Different users see different historical ranges without changing any controls.

**Phase to address:** Data loading phase (from the start) and integration testing before deployment.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single Arps function for all three model types using b as free parameter | Less code, fits any b value | Harmonic singularity crashes or produces inf EUR, wrong cumulative formula applied | Never — always branch on model type |
| `p0=None` (default) for curve_fit | No domain knowledge required | Frequent convergence to wrong local minimum; bad auto-fits in live demo | Never for a demo app — bad first impression |
| `pd.read_csv(..., parse_dates=True)` without explicit format | Simpler code | Silent date parse errors in non-US date formats | Never — always specify format |
| Plotting raw BORE_OIL_VOL without filtering ON_STREAM_HRS | Shows all data | Misleading decline shape dominated by shut-in zeros | Never for DCA fitting; acceptable for raw data overview tab |
| `theme="streamlit"` (default) for st.plotly_chart | No extra code | Dark template overridden, labels invisible | Never when using plotly_dark template |
| Hard-coding the CSV path as a relative path `./data/file.csv` | Works locally | Fails on HF Spaces if working directory differs | Never — use `Path(__file__).parent / "data/file.csv"` |
| No bounds on curve_fit parameters | Simpler code | Negative Di (production increases), b>5, unrealistic forecasts | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| HuggingFace Spaces + Streamlit | Using port 7860 in config.toml (Docker Spaces convention) | Remove port override; let Streamlit default to 8501 |
| HuggingFace Spaces + file paths | `open('data/file.csv')` relative path | `Path(__file__).parent / 'data' / 'file.csv'` absolute path via `__file__` |
| HuggingFace Spaces + requirements.txt | No version pinning → nondeterministic builds | Pin all versions: `scipy==1.13.1`, `streamlit==1.35.0`, `plotly==5.22.0` |
| Streamlit + Plotly dark theme | Default `theme="streamlit"` overrides plotly_dark | Pass `theme=None` to `st.plotly_chart()` |
| Streamlit + session state + sliders | Setting both `value=` and `key=` raises StreamlitAPIException | Use `key=` only; initialize value in session state before widget renders |
| scipy curve_fit + bounded optimization | Initial guess p0 at the bound triggers TRF method bug (scipy issue #19180) | Ensure p0 is strictly inside bounds, not at the boundary |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| CSV reload on every Streamlit re-run | Slider drag causes 500ms+ lag; app feels sluggish | `@st.cache_data` on CSV load function | Immediately on any slider interaction |
| Fitting entire 3305-row dataset instead of selected range | Auto-fit takes 5–10 seconds; spinner blocks UI during webinar | Filter to selected date range before calling curve_fit; typical fitting input is 100–500 rows | Always, but most painful with a live audience |
| Generating forecast arrays with excessive resolution | `np.linspace(0, 3650, 100000)` generates 100K points; Plotly renders sluggishly | Use 365 points for a 10-year forecast (daily is sufficient); Plotly degrades above ~50K points | Above ~10K forecast points in a Plotly trace |
| Plotly figures rebuilt from scratch on every slider move | Chart flickers and re-renders completely; jarring UX | Use `st.plotly_chart` with `key=` to control when the chart component remounts | Every slider interaction |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Auto-fit runs silently with no feedback | Engineer doesn't know if fit converged or failed; may not notice bad result | Show fit quality metrics after auto-fit: R², fitted (qi, Di, b) values, warning if R² < 0.8 |
| Sliders for qi and Di with identical units/scale | Engineers set b correctly but struggle with Di range (very small numbers like 0.005) | Display Di as "% per month" in the label, not as raw per-day decimal; convert internally |
| Forecast x-axis shows days since fit-start instead of calendar dates | Engineers cannot correlate forecast with real events (workover, recompletion) | Convert forecast time axis to calendar dates using the fit-start date |
| EUR shown without economic limit context | Number is meaningless without knowing abandonment rate | Always show "EUR at X Sm³/day economic limit" as the label |
| Log-scale toggle not available on production chart | Decline rate invisible on linear scale when late-time rates are 10× lower than peak | Provide linear/log toggle on y-axis; default to log for the DCA fit view |
| Raw data table shown before any filtering | Petroleum engineers see zero-production rows and ask "why is this showing zeros?" | Show filtered table by default (ON_STREAM_HRS > 0); offer raw view as an expander |

---

## "Looks Done But Isn't" Checklist

- [ ] **Auto-fit result:** Verify R² is computed and displayed — a visually plausible curve can have R²=0.4 if the optimizer converged poorly
- [ ] **EUR calculation:** Verify EUR is computed to economic limit, not infinite time — test that EUR changes when economic limit slider changes
- [ ] **Harmonic case:** Test b=1.0 manually via slider — verify EUR does not show `inf` and the harmonic equation branch is executing
- [ ] **Shut-in filtering:** Verify rows with ON_STREAM_HRS=0 are excluded before DCA fitting — check row count before/after filter
- [ ] **Dark theme:** Open the deployed HF Spaces app in a browser with dark OS theme — verify all axis labels and legend text are readable
- [ ] **Date parsing:** After CSV load, assert `df['DATEPRD'].min().year == 2007` and print the date range in the UI
- [ ] **Forecast units:** Confirm forecast y-axis label says "Sm³/day" not "bbl/day" or unitless
- [ ] **Cache safety:** Open two browser tabs simultaneously, change date range in tab 1, confirm tab 2 is unaffected
- [ ] **HF Spaces port:** Confirm no `[server] port` override in `.streamlit/config.toml`
- [ ] **Cold start:** Kill and restart the HF Space, time how long it takes to be interactive — verify it is under 60 seconds

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Harmonic singularity corrupting EUR | LOW (isolated function) | Add model-type dispatch in cumulative function; add `b != 1` guard; re-run tests |
| Bad local minimum from default p0 | LOW | Add domain-informed p0 and bounds to curve_fit call |
| Plotly dark theme broken on HF Spaces | LOW | Add `theme=None` to st.plotly_chart; add explicit layout colors |
| Slider/session state conflict | MEDIUM | Redesign session state schema; remove `value=` params from slider calls; test each slider independently |
| Wrong date parsing | LOW (isolated in load) | Add explicit `format=` to pd.to_datetime; add assertion on date range |
| EUR uses wrong cumulative formula | MEDIUM | Implement three separate cumulative functions with tests; validate against hand calc |
| HF Spaces port misconfiguration | LOW | Remove port override from config.toml; redeploy |
| Shut-in zeros corrupting fit | LOW | Add ON_STREAM_HRS filter before curve_fit; add row-count display to UI |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Harmonic b=1 singularity + wrong EUR formula | DCA fitting core (before UI) | Unit test: EUR(b=0.99) is finite, EUR(b=1.0) uses harmonic branch, EUR(b=0) uses exponential formula |
| Local minimum / bad auto-fit | DCA fitting core | Fit three known date ranges; confirm R² > 0.85 for the clean Volve decline period |
| Zero-production / shut-in corruption | Data loading and cleaning | Assert: fitting input has zero rows with BORE_OIL_VOL == 0 after filter |
| Slider/session state conflict | Interactive fine-tuning UI | Manual test: click auto-fit, drag each slider, confirm values persist and no double-render |
| Plotly dark theme override | First chart implementation | Visual test on deployed HF Spaces in dark environment |
| HF Spaces port / entry point | Deployment setup (first push) | Confirm App tab loads within 60 seconds of first push |
| HF Spaces auto-sleep cold start | Deployment + pre-webinar checklist | Timed cold-start test; document warm-up procedure |
| CSV date parsing | Data loading phase | Assert date bounds after load; display date range in overview tab |
| Cache mutation leaking state | Data loading + integration test | Two-tab test: independent date range selection |
| EUR unit mismatch (bbl vs Sm³) | Forecast visualization phase | Review every numeric label in the app; confirm "Sm³" throughout |

---

## Sources

- [SciPy curve_fit official docs — bounds and p0 parameters](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html)
- [SciPy issue #19180 — TRF method fails when p0 equals bound](https://github.com/scipy/scipy/issues/19180)
- [whitson+ DCA Manual — harmonic singularity and segment linking](https://manual.whitson.com/modules/well-performance/decline-curve-analysis/)
- [Streamlit Widget Behavior docs — key identity, session state conflicts, callback timing](https://docs.streamlit.io/develop/concepts/architecture/widget-behavior)
- [Streamlit issue #3925 — session state not working correctly with sliders](https://github.com/streamlit/streamlit/issues/3925)
- [Streamlit issue #4178 — Cannot set Plotly theme because Streamlit overrides user values](https://github.com/streamlit/streamlit/issues/4178)
- [HuggingFace Spaces Streamlit SDK docs — port 8501 requirement, sdk_version](https://huggingface.co/docs/hub/en/spaces-sdks-streamlit)
- [Volve production data EDA — 40% zero-production rows observed](https://www.kaggle.com/code/imranulhaquenoor/volve-field-production-data-analysis-eda)
- [ACS Omega — Removing outliers for DCA in shale gas, shut-in handling](https://pubs.acs.org/doi/10.1021/acsomega.2c03238)
- [TechRando — Automating DCA with scipy curve_fit, b value constraints](https://techrando.com/2019/07/03/how-to-automate-decline-curve-analysis-dca-in-python-using-scipys-optimize-curve_fit-function/)
- [PSU PNG 301 — Harmonic Decline (b=1) theory and infinite EUR](https://www.e-education.psu.edu/png301/node/865)
- [Plotly Theming in Python — templates and layout overrides](https://plotly.com/python/templates/)
- [Streamlit discuss — Background color of plotly chart not taken](https://discuss.streamlit.io/t/background-color-of-a-plotly-chart-not-taken/29233)

---
*Pitfalls research for: Streamlit DCA oil production forecasting app (Volve dataset, HuggingFace Spaces)*
*Researched: 2026-05-08*
