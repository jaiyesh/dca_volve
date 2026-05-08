# Feature Research

**Domain:** Oil production analysis and DCA (Decline Curve Analysis) forecasting web app
**Researched:** 2026-05-08
**Confidence:** HIGH (core DCA features verified against whitson+, ResInsight, Fekete/IHS Harmony docs and CEDengineering DCA course material)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features petroleum engineers assume exist. Missing these = product feels broken or amateurish.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Raw data table with column inspection | First thing engineers do: sanity-check the data (units, date range, nulls) | LOW | st.dataframe() with date range + row count header |
| Summary statistics panel | Mean/min/max/P10/P50/P90 for each production column — standard QC step | LOW | st.describe() is insufficient; need named percentiles |
| Time-series line chart: oil, gas, water volumes vs date | The foundational production profile plot every engineer expects | LOW | Must support dual y-axis or subplots; daily + monthly aggregation useful |
| Wellhead pressure and choke size time-series | Engineers diagnose rate changes by correlating them to choke/pressure events | LOW | Available in Volve dataset (AVG_WHP_P, AVG_CHOKE_SIZE_P) |
| Water cut (%) vs time plot | Critical for waterdrive reservoir surveillance; missing this signals the tool is incomplete | LOW | Compute: BORE_WAT_VOL / (BORE_OIL_VOL + BORE_WAT_VOL) |
| All three Arps decline models: exponential (b=0), hyperbolic (0<b<1), harmonic (b=1) | Arps (1945) is THE industry standard — omitting any of the three is a gap engineers will notice immediately | MEDIUM | Exponential most used for conventional oil; hyperbolic most general |
| Date-range selector for DCA fit window | Engineers select the stabilized decline period, not the full production history (early transient flow is excluded) | LOW | st.date_input or slider on time axis |
| Auto-fit (curve optimization) for qi, Di, b | Engineers expect one-click fitting; manual-only is unacceptable as a starting point | MEDIUM | scipy.optimize.curve_fit on Arps hyperbolic; bounds: b in [0,1], Di > 0 |
| Interactive sliders: qi, Di, b manual tuning | Post-autofit adjustment is standard workflow — lets engineers override the optimizer with judgment | LOW | st.slider updates chart live via Streamlit reactivity |
| Forecast production profile chart (fitted + forecast) | The core deliverable: show historical data + fitted curve + extrapolated future production | MEDIUM | Plotly trace overlay: scatter (history) + line (fit) + dashed line (forecast) |
| EUR (Estimated Ultimate Recovery) display | The single most-cited output of any DCA workflow — reserve estimation number | LOW | Integrate area under forecast curve to abandonment rate; display in Mstb or bbl |
| Abandonment rate input (economic limit) | EUR calculation requires a non-zero abandonment rate — without it, harmonic EUR is infinite | LOW | st.number_input; default ~10 stb/day or 1 bbl/day; affects cumulative calculation |
| Forecast horizon control (months/years) | Engineers need to set how far forward to project | LOW | st.slider for forecast months; 12–120 months typical range |
| Dark professional theme | Projector/demo context; dark backgrounds reduce eye strain and look professional | LOW | Plotly template="plotly_dark"; Streamlit page_bg via CSS |
| Goodness-of-fit metric (R², RMSE) | Engineers need to know how well the fitted curve matches history | LOW | Show on DCA panel alongside parameters |

### Differentiators (Competitive Advantage)

Features that set this demo apart in a webinar teaching context. Not expected, but memorable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Live parameter equation display | Show the Arps equation updating numerically as sliders move: q(t) = qi / (1 + b·Di·t)^(1/b) — makes the math tangible | LOW | st.latex() or st.metric() for qi, Di, b, EUR updating in real time |
| Model type selector with plain-English explanation | "Exponential: constant % decline. Hyperbolic: slowing decline (most realistic). Harmonic: declining rate, infinite EUR." — teaches the audience what b means | LOW | Radio buttons + contextual tooltip/caption |
| Cumulative production chart (Np vs time) | Rate-time + cumulative side-by-side is how engineers validate EUR visually | MEDIUM | Second chart below main forecast; area fill to show remaining reserves |
| Semi-log rate vs time plot | On semi-log axes, exponential decline is a straight line — powerful teaching visual; engineers immediately see if decline is exponential | LOW | Toggle button to switch between linear and semi-log y-axis on Plotly |
| GOR (Gas-Oil Ratio) vs cumulative oil plot | Standard diagnostic for reservoir drive mechanism — shows if gas cap is expanding or solution gas evolving | MEDIUM | GOR = BORE_GAS_VOL / BORE_OIL_VOL; plot vs cumulative oil Np |
| On-stream hours filter / normalization | Volve data has ON_STREAM_HRS — rate normalization to 24h/day removes shut-in noise from decline analysis | MEDIUM | Toggle: show raw daily volumes vs normalized rate; makes decline trend cleaner |
| Highlighted fit window on main chart | Shade the selected decline analysis window differently from the full history — helps audience see what data drove the fit | LOW | Plotly vrect() or shape annotation |
| Injection data overlay (F-4, F-5 injectors) | Dataset includes water injection volumes — overlaying injection events explains production response; unique to Volve dataset | MEDIUM | Secondary y-axis or subplot; injection events explain pressure support |
| DCA parameter table export (copy/paste ready) | Engineers want to take numbers away; a clean table of qi, Di, b, EUR, forecast months to copy | LOW | st.dataframe() with styled output or st.download_button for CSV |

### Anti-Features (Complexity Traps — Deliberately Exclude)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multiple well comparison | "Show how this scales to a field" | Dataset has exactly one well; faking multi-well adds zero value and a lot of UI complexity | Use injection well overlay to suggest multi-well awareness without multi-well DCA |
| ML-based forecasting (XGBoost, LSTM) | "AI forecasting is modern" | Completely different codebase, training data requirements, and conceptual framework — undermines the DCA teaching goal; audience came to learn Arps, not ML | Mention as "future work" slide at end of webinar |
| Real-time data ingestion / API connectivity | "Live data would be impressive" | Static CSV is the constraint; any live data layer adds auth, error handling, latency — breaks demo reliability | Load CSV at startup; emphasize that the pattern is identical for live data |
| P10/P50/P90 probabilistic forecasts | "Monte Carlo gives uncertainty bands" | Requires running hundreds of optimizer iterations, statistical framing, and explanation time that dilutes the core DCA teaching moment | Single best-fit curve; mention uncertainty verbally |
| User authentication / session management | "What if multiple people use it?" | Public HuggingFace Spaces demo; adding auth is pure complexity with no audience benefit | Stateless app; all parameters reset on reload (this is a feature for a demo) |
| Custom CSV file upload | "Let me bring my own data" | File upload handling, column mapping UI, validation edge cases — all distract from the pre-loaded Volve dataset which is the demo's story | Hard-code the Volve CSV; show loading code in a collapsed expander for educational value |
| Economic evaluation (NPV, breakeven price) | "Show field economics" | Requires oil price, opex, capex inputs — a whole additional domain; DCA is the focus | Display EUR only; mention that economics are the next step beyond DCA |
| b > 1 "super-hyperbolic" for unconventional | "Shale wells need b > 1" | Volve is a conventional North Sea reservoir; b > 1 produces infinite EUR and confuses audiences unless carefully handled | Constrain b to [0, 1] in the slider; add a tooltip explaining why |
| Fetkovich type curve matching | "Show the physics-based DCA approach" | Requires normalized rate, material balance time calculations — a separate analysis workflow that doubles complexity | Stick to empirical Arps; mention Fetkovich as the theoretical foundation in a comment |

---

## Feature Dependencies

```
[Raw Data Load]
    └──requires──> [All other features]

[Time-Series Charts]
    └──requires──> [Raw Data Load]

[Date Range Selector (DCA window)]
    └──requires──> [Time-Series Charts]
                       └──enables──> [Auto-fit (qi, Di, b)]

[Auto-fit]
    └──requires──> [Date Range Selector]
    └──outputs──>  [qi, Di, b initial values for sliders]

[Manual Sliders (qi, Di, b)]
    └──requires──> [Auto-fit] (sliders initialized from auto-fit output)
    └──updates──>  [Forecast Chart] (live reactivity)
    └──updates──>  [EUR Display]

[EUR Display]
    └──requires──> [Manual Sliders OR Auto-fit parameters]
    └──requires──> [Abandonment Rate Input]
    └──requires──> [Forecast Horizon Control]

[Forecast Chart]
    └──requires──> [Auto-fit OR Manual Sliders]
    └──enhances──> [Cumulative Production Chart (Np vs time)]

[Goodness-of-Fit Metrics (R², RMSE)]
    └──requires──> [Auto-fit] (needs fitted vs actual values)

[Water Cut Plot]
    └──requires──> [Raw Data Load] (derived column: WAT_VOL / (OIL_VOL + WAT_VOL))

[GOR Plot]
    └──requires──> [Raw Data Load] (derived column: GAS_VOL / OIL_VOL)

[On-Stream Hours Normalization]
    └──requires──> [Raw Data Load]
    └──enhances──> [Time-Series Charts] (cleaner decline trend)
    └──enhances──> [Auto-fit] (normalized rates give better fit)

[Semi-Log Toggle]
    └──requires──> [Forecast Chart]
    └──enhances──> [Teaching value] (exponential = straight line visually)

[Live Equation Display]
    └──requires──> [Manual Sliders] (values feed the rendered equation)

[Injection Data Overlay]
    └──requires──> [Time-Series Charts]
    └──requires──> [Raw Data Load] (injection columns: F-4, F-5)
```

### Dependency Notes

- **Auto-fit requires Date Range Selector:** Fitting on the full 9-year history includes early transient flow and operational noise; the date range selection is what makes the fit meaningful. This must come before sliders in the UI layout.
- **Manual Sliders require Auto-fit output:** Sliders initialized from optimizer results give engineers a sensible starting point. Initializing sliders from hardcoded defaults teaches nothing.
- **EUR requires Abandonment Rate:** For harmonic decline (b=1), EUR is mathematically infinite at zero rate. The abandonment rate input is not optional — it is a correctness requirement.
- **On-Stream Hours normalization enhances Auto-fit:** Volve data has many partial-day entries and shut-in periods. Normalizing to stb/day before fitting produces a cleaner exponential/hyperbolic trend and is standard practice.

---

## MVP Definition

### Launch With (v1) — Webinar Demo Scope

- [ ] Raw data table + date range + row count header — establishes trust in the data
- [ ] Time-series charts: oil, gas, water volumes + wellhead pressure + water cut — the production story
- [ ] Date-range selector for DCA analysis window — teaches "choose the stabilized decline period"
- [ ] Auto-fit for all three Arps models (exponential, hyperbolic, harmonic) — one-click starting point
- [ ] Model selector (radio: exponential / hyperbolic / harmonic) with plain-English description
- [ ] Manual sliders: qi, Di, b — live update of fitted curve (the interactive teaching moment)
- [ ] Forecast chart: historical scatter + fitted curve + dashed forecast line — the main deliverable
- [ ] EUR display (Mstb) + abandonment rate input + forecast horizon slider — the reserve number
- [ ] Goodness-of-fit: R² and RMSE displayed alongside parameters
- [ ] Dark Plotly theme throughout — projector-ready

### Add After Validation (v1.x)

- [ ] Semi-log toggle on rate-time chart — add if webinar audience asks "how do I tell it's exponential?"
- [ ] Cumulative production (Np vs time) chart — adds visual validation of EUR; moderate complexity, high teaching value
- [ ] On-stream hours normalization toggle — add if data noise causes fitting artifacts that distract during demo
- [ ] Live Arps equation display (st.latex) — pedagogical polish, very low effort once core is working

### Future Consideration (v2+)

- [ ] GOR vs cumulative oil diagnostic plot — reservoir drive mechanism analysis; correct but beyond webinar scope
- [ ] Injection data overlay (F-4, F-5) — good reservoir story but adds chart complexity
- [ ] DCA parameter CSV export — useful for engineers reusing results; not needed for live demo
- [ ] Multi-model comparison overlay — show all three Arps fits simultaneously for comparison

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Time-series charts (oil/gas/water/pressure/water cut) | HIGH | LOW | P1 |
| All three Arps auto-fit | HIGH | MEDIUM | P1 |
| Manual sliders (qi, Di, b) with live chart update | HIGH | LOW | P1 |
| EUR + abandonment rate + forecast horizon | HIGH | LOW | P1 |
| Forecast chart (history + fit + forecast overlay) | HIGH | MEDIUM | P1 |
| Model selector + plain-English explanation | HIGH | LOW | P1 |
| Date-range selector for fit window | HIGH | LOW | P1 |
| Goodness-of-fit (R², RMSE) | MEDIUM | LOW | P1 |
| Dark professional Plotly theme | MEDIUM | LOW | P1 |
| Raw data table + summary stats | MEDIUM | LOW | P1 |
| Semi-log toggle | MEDIUM | LOW | P2 |
| Cumulative production (Np) chart | MEDIUM | LOW | P2 |
| On-stream hours normalization toggle | MEDIUM | MEDIUM | P2 |
| Live Arps equation display | MEDIUM | LOW | P2 |
| GOR diagnostic plot | LOW | MEDIUM | P3 |
| Injection data overlay | LOW | MEDIUM | P3 |
| Parameter export (CSV download) | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for webinar demo launch
- P2: Should have, add when core is stable
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | whitson+ | ResInsight | Quick Decline | Our Approach |
|---------|----------|------------|---------------|--------------|
| Arps models (exp/hyp/harm) | All three + segments | All three | Implied (hyperbolic focus) | All three, radio selector |
| Auto-fit | Yes, optimizer | Yes | Yes | scipy curve_fit with bounds |
| Manual parameter adjustment | Drag-and-drop on chart | No | No | Streamlit sliders (simpler, more teachable) |
| EUR output | Yes | Yes | Yes | Yes, prominent metric |
| Abandonment rate input | Yes | Implied | Yes | Yes, number_input |
| Rate-time plot | Yes | Yes | Yes | Yes, Plotly |
| Rate-cumulative plot | Yes | Yes | Implied | v1.x |
| Semi-log axes | Yes | Implied | Implied | v1.x toggle |
| GOR / WOR analysis | Yes | No | Implied | v2+ |
| Dark theme | No (light) | No (light) | Unknown | Yes (Plotly dark — differentiator for demo) |
| Multi-well | Yes | Yes | Yes | Deliberately excluded |
| Economics (NPV) | No | No | Yes | Deliberately excluded |
| Export (ARIES, PHDwin) | Yes | No | No | Deliberately excluded |
| Teaching/pedagogical mode | No | No | No | YES — this is the differentiator |

**Key insight:** Commercial tools (whitson+, ResInsight, Quick Decline) optimize for production workflows. This app's differentiator is the *teaching workflow* — live equations, plain-English model descriptions, pedagogical slider sensitivity — none of which commercial tools prioritize.

---

## Sources

- whitson+ DCA manual: https://manual.whitson.com/modules/well-performance/decline-curve-analysis/
- ResInsight DCA documentation: https://resinsight.org/plot-window/declinecurveanalysis/index.html
- CEDengineering "Forecasting Oil and Gas Using Decline Curves" (PDH course PDF): https://www.cedengineering.com/userfiles/Forecasting%20Oil%20and%20Gas%20Using%20Decline%20Curves.pdf
- IHS Harmony Decline Analysis Theory: https://www.ihsenergy.ca/support/documentation_ca/Harmony/content/html_files/reference_material/analysis_method_theory/decline_theory.htm
- Arps DCA practical guide (2024): https://spatial-dev.guru/2024/05/24/arps-decline-curve-analysis-a-practical-guide-for-petroleum-engineers/
- Decline Curve Analysis (Wikipedia): https://en.wikipedia.org/wiki/Decline_curve_analysis
- EUR definition and methods: https://novilabs.com/glossary/eur-estimated-ultimate-recovery/
- WOR forecasting theory (IHS): https://www.ihsenergy.ca/support/documentation_ca/Harmony/content/html_files/reference_material/analysis_method_theory/wor_forecasting_theory.htm
- Rashid Wadani DCA Tool (GitHub): https://github.com/rashidwadani/Decline_Curve_Analysis_Tool
- Selborne Research DCA guide: https://selborneresearch.com/guides/oil-gas/decline-curve-analysis/

---
*Feature research for: Oil Production Analysis & DCA Forecasting (Volve dataset, Streamlit, webinar demo)*
*Researched: 2026-05-08*
