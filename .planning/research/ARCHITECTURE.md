# Architecture Research

**Domain:** Streamlit data science app — petroleum engineering / DCA forecasting
**Researched:** 2026-05-08
**Confidence:** HIGH (Streamlit docs, HuggingFace Spaces docs, SciPy patterns all current)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      HuggingFace Spaces                          │
│                     (Streamlit SDK, port 8501)                   │
├─────────────────────────────────────────────────────────────────┤
│                         app.py (entry point)                     │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│   │ pages/        │  │ pages/        │  │ pages/            │   │
│   │ 1_overview.py │  │ 2_explore.py  │  │ 3_dca.py          │   │
│   └──────┬────────┘  └──────┬────────┘  └────────┬──────────┘   │
│          │                  │                     │              │
├──────────┴──────────────────┴─────────────────────┴─────────────┤
│                       utils/ (shared modules)                    │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │ data.py      │  │ dca.py       │  │ charts.py            │  │
│   │ (load/clean) │  │ (Arps math)  │  │ (Plotly dark figs)   │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                       Static assets                              │
│   ┌────────────────────┐   ┌───────────────────────────────┐    │
│   │ data/              │   │ .streamlit/config.toml        │    │
│   │ Final PF-12...csv  │   │ (dark theme configuration)    │    │
│   └────────────────────┘   └───────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `app.py` | Entry point, sidebar nav, page routing via `st.navigation` | All pages via `st.Page` |
| `pages/1_overview.py` | Raw data table, date range, summary stats | `utils/data.py` |
| `pages/2_explore.py` | Time-series charts: oil/gas/water/WHP/choke/WC | `utils/data.py`, `utils/charts.py` |
| `pages/3_dca.py` | Date-range selector, auto-fit, slider tuning, EUR forecast | `utils/dca.py`, `utils/charts.py`, `st.session_state` |
| `utils/data.py` | CSV loading (cached), cleaning, filtering by date range | Called by all pages |
| `utils/dca.py` | Arps equations, `scipy.optimize.curve_fit` wrapper, EUR calc | Called by `pages/3_dca.py` |
| `utils/charts.py` | Plotly figure factory with `plotly_dark` template applied | Called by explore and DCA pages |
| `data/` | Static CSV file — source of truth, never modified | Read by `utils/data.py` |
| `.streamlit/config.toml` | Dark theme, font, layout settings | Streamlit runtime |
| `requirements.txt` | Dependency pinning for HF Spaces runtime | HuggingFace Spaces build |

## Recommended Project Structure

```
.
├── app.py                          # Entry point — nav routing only, no business logic
├── requirements.txt                # streamlit, pandas, plotly, scipy, numpy
├── README.md                       # HF Spaces YAML config block + description
├── .streamlit/
│   └── config.toml                 # Dark theme, port=8501 (do NOT override port)
├── pages/
│   ├── 1_Data_Overview.py          # Table + summary stats
│   ├── 2_Production_Explorer.py    # Time-series charts
│   └── 3_DCA_Forecast.py          # DCA fitting + forecast
├── utils/
│   ├── __init__.py
│   ├── data.py                     # load_data() with @st.cache_data
│   ├── dca.py                      # Arps equations + fit() + forecast() + eur()
│   └── charts.py                   # build_production_chart(), build_dca_chart()
└── data/
    └── Final PF-12 and Injection.csv
```

### Structure Rationale

- **`app.py` as pure router:** When using `st.navigation`, the entry point becomes a frame around all pages. Keep it thin — sidebar logo, navigation list, nothing else. This matches official Streamlit multi-page guidance.
- **`pages/` with numeric prefixes:** Filenames like `1_Data_Overview.py` automatically set display order and sidebar label. Pages are independent scripts; they share state only through `st.session_state` and cached functions.
- **`utils/` as pure Python:** No `st.*` calls inside `utils/`. These are testable pure functions. Streamlit calls happen only in `pages/` and `app.py`. This is the single most important structural discipline.
- **`utils/dca.py` separate from pages:** DCA math (Arps equations, `curve_fit` wrapper, EUR integration) must live outside Streamlit. This makes it independently testable and means the DCA page is just wiring sliders to function calls.
- **`utils/charts.py` centralized:** All `go.Figure` construction with `template="plotly_dark"` in one place. Pages call chart builders, not raw Plotly. This ensures visual consistency across pages.

## Architectural Patterns

### Pattern 1: Cache Data Loading at Module Boundary

**What:** Wrap the CSV loader in `@st.cache_data`. All pages call this single cached function. The cache is shared across sessions (all users get the same DataFrame from disk) and survives reruns.

**When to use:** Any function that reads from disk, runs a network request, or does expensive transformation. For this app: the CSV load, any date-range pre-filtering that's expensive.

**Trade-offs:** Cache is shared across all sessions by default. For a static CSV this is ideal — load once, serve forever. If the data were mutable, you'd need per-session caching instead.

**Example:**
```python
# utils/data.py
import pandas as pd
import streamlit as st

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/Final PF-12 and Injection.csv", parse_dates=["DATEPRD"])
    df = df.sort_values("DATEPRD").reset_index(drop=True)
    df = df[df["BORE_OIL_VOL"] > 0]  # filter shut-in days
    return df

def filter_by_date(df: pd.DataFrame, start, end) -> pd.DataFrame:
    return df[(df["DATEPRD"] >= start) & (df["DATEPRD"] <= end)]
```

The DCA fitting result (scipy output) is also a candidate for `@st.cache_data` — hash on the date range selection so re-fitting only fires when the range actually changes.

### Pattern 2: Session State for DCA Parameter Persistence

**What:** DCA parameters (qi, Di, b, model type, date range) are stored in `st.session_state`. When the auto-fit button runs, it writes fitted values into session state. Sliders read from session state as their initial value, so manual tuning persists across reruns.

**When to use:** Any user-adjustable parameter that must survive reruns. Every slider with `key=` is automatically a session state entry. The explicit `if key not in st.session_state` initialization guard prevents overwriting on subsequent reruns.

**Trade-offs:** Session state is per-user-session (not shared). This is correct for interactive parameter tuning — each user tunes their own curve. The guard pattern must run before widget definitions.

**Example:**
```python
# pages/3_DCA_Forecast.py (initialization block at top)
import streamlit as st
from utils.dca import fit_arps, forecast_arps, calculate_eur
from utils.data import load_data, filter_by_date

# Initialize session state with defaults before any widget
defaults = {"qi": 500.0, "Di": 0.05, "b": 0.5, "model": "hyperbolic", "fitted": False}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

df = load_data()

# Auto-fit button writes into session state
if st.button("Auto-fit Arps"):
    df_fit = filter_by_date(df, st.session_state.start_date, st.session_state.end_date)
    params = fit_arps(df_fit["DATEPRD"], df_fit["BORE_OIL_VOL"], model=st.session_state.model)
    st.session_state.qi = params["qi"]
    st.session_state.Di = params["Di"]
    st.session_state.b  = params["b"]
    st.session_state.fitted = True

# Sliders read from session state — key= links widget to session state automatically
qi = st.slider("qi (initial rate, bbl/d)", 10.0, 5000.0, key="qi")
Di = st.slider("Di (nominal decline, 1/day)", 0.001, 0.5, key="Di", format="%.4f")
b  = st.slider("b (hyperbolic exponent)", 0.0, 2.0, key="b", step=0.05)
```

### Pattern 3: Plotly Dark Figure Factory

**What:** All chart construction goes through `utils/charts.py`. Functions return `go.Figure` objects with `plotly_dark` template and consistent axis/font settings pre-applied. Pages call `st.plotly_chart(fig, use_container_width=True, theme=None)` — `theme=None` disables Streamlit's default theme override and lets `plotly_dark` render as-is.

**When to use:** Every chart in the app. Do not call `go.Figure()` directly inside page scripts.

**Trade-offs:** Streamlit 1.16+ overrides Plotly template with its own theme unless you pass `theme=None`. Always use `theme=None` for dark projector-friendly charts.

**Example:**
```python
# utils/charts.py
import plotly.graph_objects as go

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#fafafa", size=13),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=60, r=20, t=40, b=50),
)

def build_production_chart(df, columns: list[str], title: str) -> go.Figure:
    fig = go.Figure()
    for col in columns:
        fig.add_trace(go.Scatter(x=df["DATEPRD"], y=df[col], name=col, mode="lines"))
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Volume (bbl/d)", **DARK_LAYOUT)
    return fig

def build_dca_chart(df_actual, t_forecast, q_forecast, params: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_actual["DATEPRD"], y=df_actual["BORE_OIL_VOL"],
                             name="Actual", mode="markers", marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=t_forecast, y=q_forecast, name="Arps Forecast", mode="lines"))
    fig.update_layout(title="DCA Forecast", xaxis_title="Date", yaxis_title="Oil Rate (bbl/d)",
                      **DARK_LAYOUT)
    return fig
```

In each page:
```python
st.plotly_chart(fig, use_container_width=True, theme=None)  # theme=None is critical
```

## Data Flow

### Application Startup Flow

```
HuggingFace Spaces starts app.py
    ↓
st.navigation([Page1, Page2, Page3]) renders sidebar
    ↓
User selects page → page script executes top-to-bottom
    ↓
load_data() called → st.cache_data returns DataFrame (cached after first run)
    ↓
Widgets render with st.session_state values (or defaults on first run)
```

### DCA Interactive Flow

```
User selects date range (date_input widgets)
    ↓ session_state.start_date / end_date updated
User clicks "Auto-fit Arps"
    ↓
filter_by_date(df, start, end) → filtered DataFrame
    ↓
fit_arps(t, q, model) [utils/dca.py]
    ↓ scipy.optimize.curve_fit → (qi, Di, b)
    ↓ writes to st.session_state.qi / Di / b
Streamlit reruns → sliders initialize at fitted values
    ↓
User moves slider (qi / Di / b)
    ↓ session_state.{key} updated, rerun triggered
forecast_arps(qi, Di, b, t_future) [utils/dca.py]
    ↓ returns q_forecast array
calculate_eur(q_forecast, t_future) [utils/dca.py]
    ↓ returns EUR scalar
build_dca_chart(df_actual, t_forecast, q_forecast) [utils/charts.py]
    ↓ returns go.Figure
st.plotly_chart(fig, theme=None) → user sees updated chart
```

### State Management

```
st.session_state (per-user)
    ├── qi, Di, b           ← DCA params (written by auto-fit, read by sliders)
    ├── model               ← "exponential" | "hyperbolic" | "harmonic"
    ├── start_date, end_date ← fitting window
    ├── forecast_months     ← projection horizon
    └── fitted              ← bool flag (True after first auto-fit)

@st.cache_data (shared across all users)
    └── load_data() result  ← full DataFrame, loaded once from CSV
```

## HuggingFace Spaces Requirements

**Required files (non-negotiable):**
- `app.py` — must be named exactly `app.py`
- `requirements.txt` — lists all pip dependencies
- `README.md` — must contain YAML front-matter with `sdk: streamlit`

**Required YAML block in README.md:**
```yaml
---
title: Volve DCA Forecasting
emoji: 🛢️
colorFrom: blue
colorTo: gray
sdk: streamlit
sdk_version: "1.35.0"   # pin to a supported version
app_file: app.py
pinned: false
---
```

**Critical constraint:** Do NOT set a custom port in `.streamlit/config.toml`. Only port 8501 is allowed. If `config.toml` exists, it must not override `server.port`.

**Optional:**
- `packages.txt` for Debian-level system dependencies (not needed for this app)
- `.streamlit/config.toml` for theme settings only

## Anti-Patterns

### Anti-Pattern 1: Streamlit Calls Inside utils/

**What people do:** Call `st.write()`, `st.error()`, `st.spinner()` inside `utils/dca.py` or `utils/data.py` because it feels convenient.

**Why it's wrong:** Creates an invisible coupling between business logic and the Streamlit runtime. The utils can no longer be imported in tests, scripts, or notebooks without a Streamlit context. It also makes it impossible to reuse DCA logic in a non-Streamlit setting.

**Do this instead:** Return values and errors from utils. Let the page script handle all `st.*` calls. Use Python exceptions for errors — catch them in the page and display with `st.error()`.

### Anti-Pattern 2: Re-Fitting DCA on Every Slider Move

**What people do:** Call `scipy.optimize.curve_fit` inside the slider's render path, so every millimeter of slider movement triggers a full optimization.

**Why it's wrong:** `curve_fit` takes 50–500ms. Sliders cause continuous reruns while dragging. This makes the app feel frozen on any machine.

**Do this instead:** Separate auto-fit (button-triggered, writes to session state) from manual tuning (sliders read session state and call fast forward-model only — no optimization). Forward Arps calculation for a slider change is microseconds; `curve_fit` should only fire on button click.

### Anti-Pattern 3: Overriding Plotly Template Then Calling st.plotly_chart Without theme=None

**What people do:** Set `template="plotly_dark"` in the figure, then call `st.plotly_chart(fig)` without `theme=None`.

**Why it's wrong:** Streamlit 1.16+ silently replaces the Plotly template with its own "streamlit" theme. The dark template is ignored. Charts render with Streamlit's default colors (which are light-mode), breaking the projector-friendly design.

**Do this instead:** Always pass `theme=None` to `st.plotly_chart()` when you want native Plotly template control.

### Anti-Pattern 4: Single-File App Beyond ~200 Lines

**What people do:** Put all DCA logic, data loading, and charting in one `app.py` because it starts small.

**Why it's wrong:** A webinar demo app grows. By the time you add the explore page, DCA sliders, EUR panel, and forecast chart, a single file becomes unnavigable. Debugging a slider interaction requires scrolling through hundreds of lines of mixed math and UI code.

**Do this instead:** Start with the pages/ + utils/ split from day one. It adds less than 5 minutes of setup and pays back immediately.

## Scaling Considerations

This is a single-user demo / small-group webinar app. Scaling is not a concern. The only relevant operational consideration is:

| Concern | Approach |
|---------|----------|
| Cold start time on HF Spaces | CSV load is fast (<1s for 3K rows). `@st.cache_data` ensures it only loads once per container lifetime. No issue. |
| Slider lag during DCA tuning | Solved by separating auto-fit (button) from forward-model (slider). Forward Arps is O(N) arithmetic, not optimization. |
| Multiple webinar attendees loading simultaneously | HF Spaces runs one container. Each browser tab gets its own session state. `@st.cache_data` on `load_data()` means the CSV is loaded once and shared. Effectively zero overhead for concurrent viewers. |

## Build Order

Build in this dependency order — each layer depends on the one before it:

1. **Static assets + config** (`data/csv`, `.streamlit/config.toml`, `README.md`) — no dependencies, do first
2. **`utils/data.py`** — pure pandas, no Streamlit dependency; verifies CSV column names and data quality
3. **`utils/dca.py`** — pure scipy/numpy, no Streamlit; implement and unit-test Arps equations independently
4. **`utils/charts.py`** — pure Plotly; implement dark figure factory; verify figures render correctly in a notebook before wiring to Streamlit
5. **`pages/1_Data_Overview.py`** — wires `utils/data.py` to Streamlit table + stats; simplest page, good for validating the app structure
6. **`pages/2_Production_Explorer.py`** — wires `utils/data.py` + `utils/charts.py`; validates dark chart pipeline
7. **`pages/3_DCA_Forecast.py`** — wires all three utils; implements session state pattern; most complex page, build last
8. **`app.py`** — thin router; add `st.navigation` pointing at all three pages; add sidebar chrome

## Sources

- Streamlit multi-page docs (official): https://docs.streamlit.io/develop/concepts/multipage-apps/overview
- Streamlit caching docs (official): https://docs.streamlit.io/develop/concepts/architecture/caching
- Streamlit session state docs (official): https://docs.streamlit.io/develop/concepts/architecture/session-state
- Streamlit plotly_chart API (official): https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
- Plotly templates docs (official): https://plotly.com/python/templates/
- HuggingFace Spaces Streamlit SDK (official): https://huggingface.co/docs/hub/en/spaces-sdks-streamlit
- DCA with scipy.curve_fit (MEDIUM confidence, community): https://techrando.com/2019/07/03/how-to-automate-decline-curve-analysis-dca-in-python-using-scipys-optimize-curve_fit-function/
- Streamlit project structure discussion (MEDIUM confidence, community): https://discuss.streamlit.io/t/streamlit-project-folder-structure-for-medium-sized-apps/5272

---
*Architecture research for: Streamlit petroleum engineering DCA app on HuggingFace Spaces*
*Researched: 2026-05-08*
