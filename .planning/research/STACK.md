# Stack Research

**Domain:** Streamlit petroleum engineering / oil production DCA forecasting web app
**Researched:** 2026-05-08
**Confidence:** HIGH (core stack), MEDIUM (HuggingFace deployment path — confirmed from official changelog)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Runtime | Required by pandas 3.x, scipy 1.17, numpy 2.x — all now require 3.11 minimum. Align with this to avoid dependency conflicts. |
| Streamlit | 1.52.0 | App framework | Latest stable as of December 2025. Use pinned version in requirements.txt. The reactive execution model is ideal for slider-driven chart updates without manual event wiring. |
| Plotly | 6.0+ (6.7.0 current) | Interactive charts | The only charting library that gives dark-themed, zoomable, projector-ready charts with zero JS. Use `template="plotly_dark"` with `theme=None` in `st.plotly_chart()` to bypass Streamlit's theme override and get true dark backgrounds. |
| pandas | 2.2.x (pin to 2.2.3) | Data wrangling | pandas 3.x requires Python 3.11 and drops some legacy APIs. For this project (simple CSV, date parsing, resampling) pandas 2.2.3 is the safer pinned choice — latest 2.x with Copy-on-Write enabled, no breaking changes. If comfortable on Python 3.11, 3.0.2 is also fine. |
| NumPy | 1.26.x (or 2.x if pinning pandas 3.x) | Numerical arrays | scipy 1.17 is compatible with numpy 1.x and 2.x. Pin to 1.26.4 alongside pandas 2.2.3 for widest compatibility; or numpy 2.x alongside pandas 3.x. |
| SciPy | 1.17.1 | Arps curve fitting | `scipy.optimize.curve_fit` is the industry-standard tool for nonlinear least squares in Python. Use it directly for all three Arps models. Straightforward, no extra dependencies, well-documented, universally understood by engineers. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lmfit | 1.3.4 | Enhanced curve fitting with bounded parameters and uncertainty reporting | Use INSTEAD of bare `curve_fit` if you want confidence intervals on qi/Di/b, or if the optimizer struggles with initial conditions. Wraps scipy under the hood so no algorithmic difference — just better parameter control and richer fit reports. |
| openpyxl | 3.1.x | Excel export of results | Only needed if you add a "Download as Excel" button. Not required for MVP. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `.streamlit/config.toml` | Force dark theme app-wide | Set `[theme] base = "dark"` to ensure consistent appearance regardless of user OS setting. Required for projector demos where auto light/dark can surprise you. |
| `packages.txt` | System-level apt-get packages for Docker | Leave empty for this app — no binary system deps beyond Python needed. Keep the file present (zero bytes) for Docker template compatibility. |

---

## Installation

```bash
# requirements.txt for HuggingFace Spaces Docker deployment
streamlit==1.52.0
plotly==6.0.0
pandas==2.2.3
numpy==1.26.4
scipy==1.17.1
# Optional: uncomment if you want richer fit uncertainty reporting
# lmfit==1.3.4
```

**Note on pinning:** Always pin exact versions in requirements.txt when deploying to HuggingFace Spaces Docker. Unpinned packages rebuild to the latest each deployment and will silently break apps when major versions drop.

---

## HuggingFace Spaces Deployment — Critical Details

### SDK Change (April 30, 2025)

The native Streamlit SDK for HuggingFace Spaces was **deprecated on April 30, 2025**. New Streamlit apps must use the **Docker SDK** with the Streamlit Docker template. This is confirmed in the [official HuggingFace Spaces changelog](https://huggingface.co/docs/hub/en/spaces-changelog).

**What this means in practice:**
- You cannot use `sdk: streamlit` in your README.md anymore for new Spaces
- You must use `sdk: docker` and provide a `Dockerfile`
- The runtime behavior of the Streamlit app is identical — only the hosting wrapper changes

### Required File Structure

```
your-space/
├── README.md            # HuggingFace Space metadata YAML header
├── Dockerfile           # Docker build instructions
├── requirements.txt     # Python dependencies (pip installs these)
├── packages.txt         # System apt-get packages (leave empty)
├── app.py               # Streamlit entry point (must be named app.py)
├── .streamlit/
│   └── config.toml      # Dark theme config
└── data/
    └── Final PF-12 and Injection.csv
```

### README.md YAML Block

```yaml
---
title: Volve DCA Forecasting App
emoji: 🛢
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 8501
---
```

Note: `app_port: 8501` — Streamlit's default port. Do NOT use 7860 (that is Gradio's default). The Dockerfile exposes 8501 and the README must match.

### Dockerfile (from official SpacesExamples/streamlit-docker-example)

```dockerfile
FROM python:3.11

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
COPY ./packages.txt /app/packages.txt

RUN apt-get update && xargs -r -a /app/packages.txt apt-get install -y && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir -r /app/requirements.txt

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user
ENV PATH=$HOME/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

EXPOSE 8501

CMD streamlit run app.py \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.fileWatcherType none
```

Change the base image from `python:3.8.9` (as in the official template) to `python:3.11` to match dependency requirements.

---

## Streamlit Patterns for This App

### Dark Theme Setup

`.streamlit/config.toml`:
```toml
[theme]
base = "dark"
primaryColor = "#FF6B35"      # accent for highlights
backgroundColor = "#0E1117"   # main dark background
secondaryBackgroundColor = "#1E2228"
textColor = "#FAFAFA"
```

### Plotly Dark Charts — Bypass Streamlit Theme Override

Use `theme=None` in `st.plotly_chart()` to prevent Streamlit from overriding your Plotly template. Then set `template="plotly_dark"` on the figure itself.

```python
fig = go.Figure()
fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, theme=None, width="stretch")
```

**Why `theme=None`:** Streamlit only supports two chart themes: `"streamlit"` (default, overrides your Plotly template) or `None` (passes through your Plotly template). For true `plotly_dark`, you must use `theme=None`.

**Why `width="stretch"`:** The `use_container_width` parameter is deprecated and will be removed after 2025-12-31. Use `width="stretch"` instead.

### Slider + Live Chart Update Pattern

Streamlit reruns the full script on any widget change. The pattern for responsive sliders driving chart updates:

```python
# Define sliders in sidebar
qi = st.sidebar.slider("qi (initial rate, STB/day)", 100, 5000, 1200)
di = st.sidebar.slider("Di (annual decline rate)", 0.01, 2.0, 0.5, step=0.01)
b  = st.sidebar.slider("b (hyperbolic exponent)", 0.0, 1.0, 0.5, step=0.05)

# Compute and render — runs automatically on slider change
forecast = compute_arps(qi, di, b, n_months)
st.plotly_chart(build_forecast_fig(forecast), theme=None, width="stretch")
```

No callbacks or session_state needed for this linear pattern. Streamlit's top-to-bottom rerun handles it. Only use `st.session_state` if you need to persist auto-fit results across multiple user interactions (e.g., store the curve_fit output so sliders start at fitted values).

**2025 note:** `st.slider` was optimized in 2025 to not rerun until the user releases the slider thumb — this prevents chart thrashing during drag.

### Arps Curve Fitting with scipy.optimize.curve_fit

```python
from scipy.optimize import curve_fit
import numpy as np

def hyperbolic_decline(t, qi, di, b):
    return qi / (1 + b * di * t) ** (1 / b)

def exponential_decline(t, qi, di):
    return qi * np.exp(-di * t)

def harmonic_decline(t, qi, di):
    return qi / (1 + di * t)

# Fit: t in days (or months), q in STB/day
popt, pcov = curve_fit(
    hyperbolic_decline,
    t_data,
    q_data,
    p0=[q_data.max(), 0.5, 0.5],  # initial guess: qi, Di, b
    bounds=([0, 0, 0], [np.inf, 5.0, 1.0]),  # physical bounds
    maxfev=10000
)
qi_fit, di_fit, b_fit = popt
```

The `bounds` parameter is essential for Arps — without it, the optimizer can return negative Di or b > 1 which are physically meaningless.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `scipy.optimize.curve_fit` | `lmfit` | Use lmfit if you need confidence interval bands on the forecast, or if the optimizer fails to converge without explicit parameter bounds management. lmfit's parameter bounding is more ergonomic than scipy's tuple interface. |
| Plotly with `theme=None` | Altair / Matplotlib | Only if you need static images for export. Plotly is the only choice for an interactive, projector-friendly dark chart in Streamlit. |
| pandas 2.2.3 (pinned) | pandas 3.0.x | Use 3.0.x only if Python 3.11+ is confirmed and you want Copy-on-Write enabled by default. For this app's simple CSV operations, 2.2.3 is stable and safe. |
| Docker SDK | Streamlit SDK | Streamlit SDK is deprecated as of April 30, 2025. There is no "when to use alternative" — Docker is the only path for new Spaces. |
| `width="stretch"` in plotly_chart | `use_container_width=True` | `use_container_width` is removed after 2025-12-31. Do not use it. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `sdk: streamlit` in README.md | Deprecated April 30, 2025. HuggingFace will not create new Spaces with this SDK. | `sdk: docker` with Streamlit Docker template |
| `use_container_width=True` | Deprecated, removed after 2025-12-31 | `width="stretch"` in `st.plotly_chart()` |
| Streamlit theme override for Plotly dark | `theme="streamlit"` (the default) overrides your `plotly_dark` template and applies Streamlit's color system instead | `st.plotly_chart(fig, theme=None)` |
| ML forecasting (LSTM, XGBoost) | Out of scope per PROJECT.md; adds torch/sklearn deps that balloon Docker image size and build time on HuggingFace free tier | Arps DCA with scipy |
| `plotly` without version pin | Plotly 6.x introduced breaking changes vs 5.x in figure serialization | Pin `plotly==6.0.0` or higher, explicitly in requirements.txt |
| `python:3.8` or `python:3.9` in Dockerfile | scipy 1.17 and numpy 2.x require Python 3.11+. Using old Python forces you onto older (insecure) library versions. | `FROM python:3.11` |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `streamlit==1.52.0` | `plotly>=5.x`, `pandas>=1.x`, Python 3.8+ | Streamlit itself has broad compatibility; the floor is set by scipy/numpy |
| `scipy==1.17.1` | `numpy>=1.23, <3`, Python >=3.11 | Requires Python 3.11+. This is the binding constraint for the base Docker image. |
| `pandas==2.2.3` | `numpy>=1.22.4`, Python 3.9-3.12 | 2.2.x still supports Python 3.9+ if needed; safe pairing with numpy 1.26.4 |
| `pandas==3.0.2` | `numpy>=1.26.4`, Python >=3.11 | If going full 3.11+ stack, 3.0.x is fine but has some API removals vs 2.x |
| `plotly==6.7.0` | `numpy>=1.x`, no Streamlit version constraint | Plotly 6.x dropped some deprecated `graph_objs` aliases present in 5.x; test any legacy code |
| `numpy==1.26.4` | `pandas==2.2.3`, `scipy==1.17.x` | Safe "lowest common denominator" pin for the full stack |

**Recommended pin set (copy-paste ready):**
```
streamlit==1.52.0
plotly==6.0.0
pandas==2.2.3
numpy==1.26.4
scipy==1.17.1
```

---

## Sources

- [HuggingFace Spaces Changelog](https://huggingface.co/docs/hub/en/spaces-changelog) — Streamlit SDK deprecation confirmed April 30, 2025 (HIGH confidence)
- [HuggingFace Spaces: Streamlit Docs](https://huggingface.co/docs/hub/en/spaces-sdks-streamlit) — `app.py` entry point, `requirements.txt` format, port 8501 (HIGH confidence)
- [HuggingFace Docker Spaces Docs](https://huggingface.co/docs/hub/en/spaces-sdks-docker) — Dockerfile structure, user permissions, port config (HIGH confidence)
- [SpacesExamples/streamlit-docker-example](https://huggingface.co/spaces/SpacesExamples/streamlit-docker-example) — Official Dockerfile reference (HIGH confidence)
- [Streamlit PyPI](https://pypi.org/project/streamlit/) — Version 1.57.0 current (April 2026); 1.52.0 is December 2025 stable (HIGH confidence)
- [Streamlit 2025 Release Notes](https://docs.streamlit.io/develop/quick-reference/release-notes/2025) — Slider optimization, width parameter, datetime_input (HIGH confidence)
- [st.plotly_chart API reference](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart) — `theme=None`, `width="stretch"`, `use_container_width` deprecation (HIGH confidence)
- [Plotly PyPI](https://pypi.org/project/plotly/) — Version 6.7.0 current (HIGH confidence)
- [pandas PyPI](https://pypi.org/project/pandas/) — Version 3.0.2 current (HIGH confidence)
- [numpy PyPI](https://pypi.org/project/numpy/) — Version 2.4.4 current (HIGH confidence)
- [scipy PyPI](https://pypi.org/project/scipy/) — Version 1.17.1 current (HIGH confidence)
- [scipy.optimize.curve_fit docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html) — Bounds, p0, covariance (HIGH confidence)
- [lmfit PyPI](https://pypi.org/project/lmfit/) — Version 1.3.4 (July 2025) (HIGH confidence)
- [lmfit docs](https://lmfit.github.io/lmfit-py/) — Confidence intervals, parameter bounds vs scipy (MEDIUM confidence)
- [Plotly Templates](https://plotly.com/python/templates/) — `plotly_dark` template reference (HIGH confidence)

---

*Stack research for: Streamlit petroleum DCA app / HuggingFace Spaces Docker deployment*
*Researched: 2026-05-08*
