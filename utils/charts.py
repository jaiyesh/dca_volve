"""
Plotly dark chart factory — pure Plotly, no Streamlit dependency.

Exports:
  DARK_LAYOUT            — base layout dict for dark-themed figures
  build_timeseries_chart — single-series time-series figure
  build_dual_axis_chart  — dual y-axis figure (solid + dashed)
"""
import plotly.graph_objects as go
import pandas as pd

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0E1117",
    plot_bgcolor="#0E1117",
    font=dict(color="#FAFAFA", size=13),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#FAFAFA")),
    margin=dict(l=60, r=40, t=50, b=50),
    xaxis=dict(
        gridcolor="#2A2A3A",
        tickfont=dict(color="#CCCCCC"),
        title_font=dict(color="#FAFAFA"),
    ),
    yaxis=dict(
        gridcolor="#2A2A3A",
        tickfont=dict(color="#CCCCCC"),
        title_font=dict(color="#FAFAFA"),
    ),
)


def build_timeseries_chart(
    df: pd.DataFrame,
    y_col: str,
    title: str,
    y_label: str,
    color: str = "#FF6B35",
    mode: str = "lines",
) -> go.Figure:
    """Single-series time-series chart with dark layout."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["DATEPRD"],
            y=df[y_col],
            name=y_col,
            mode=mode,
            line=dict(color=color, width=1.5),
        )
    )
    layout = {**DARK_LAYOUT}
    fig.update_layout(
        title=dict(text=title, font=dict(color="#FAFAFA", size=15)),
        xaxis_title="Date",
        yaxis_title=y_label,
        showlegend=False,
        **{k: v for k, v in layout.items() if k not in ("template",)},
    )
    fig.update_layout(template="plotly_dark")
    return fig


def build_dual_axis_chart(
    df: pd.DataFrame,
    y1_col: str,
    y1_label: str,
    y1_color: str,
    y2_col: str,
    y2_label: str,
    y2_color: str,
    title: str,
) -> go.Figure:
    """Dual y-axis chart: y1 on left (solid), y2 on right (dashed)."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["DATEPRD"],
            y=df[y1_col],
            name=y1_label,
            mode="lines",
            line=dict(color=y1_color, width=1.5),
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["DATEPRD"],
            y=df[y2_col],
            name=y2_label,
            mode="lines",
            line=dict(color=y2_color, width=1.5, dash="dash"),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color="#FAFAFA", size=15)),
        template="plotly_dark",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="#FAFAFA", size=13),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#FAFAFA")),
        margin=dict(l=60, r=80, t=50, b=50),
        xaxis=dict(
            title="Date",
            gridcolor="#2A2A3A",
            tickfont=dict(color="#CCCCCC"),
        ),
        yaxis=dict(
            title=dict(text=y1_label, font=dict(color=y1_color)),
            gridcolor="#2A2A3A",
            tickfont=dict(color="#CCCCCC"),
        ),
        yaxis2=dict(
            title=dict(text=y2_label, font=dict(color=y2_color)),
            overlaying="y",
            side="right",
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(color="#CCCCCC"),
        ),
    )
    return fig


def build_dca_chart(
    df_all: pd.DataFrame,
    df_fit_window: pd.DataFrame,
    df_forecast: pd.DataFrame,
) -> go.Figure:
    """
    DCA chart combining:
    - Historical scatter (all producing data, grey dots, small)
    - Fit window data (orange dots, slightly larger, to show what was fitted)
    - Fitted + forecast curve (cyan dashed line from forecast df)
    df_all: full producing DataFrame with DATEPRD + BORE_OIL_VOL
    df_fit_window: date-filtered DataFrame (user's selected fitting range)
    df_forecast: output of forecast_arps() — columns: date, q
    """
    fig = go.Figure()

    # All historical data (grey background scatter)
    fig.add_trace(
        go.Scatter(
            x=df_all["DATEPRD"],
            y=df_all["BORE_OIL_VOL"],
            name="Historical",
            mode="markers",
            marker=dict(color="#666666", size=3, opacity=0.6),
        )
    )

    # Fit window data (orange, slightly larger)
    if df_fit_window is not None and len(df_fit_window) > 0:
        fig.add_trace(
            go.Scatter(
                x=df_fit_window["DATEPRD"],
                y=df_fit_window["BORE_OIL_VOL"],
                name="Fit Window",
                mode="markers",
                marker=dict(color="#FF6B35", size=5),
            )
        )

    # Fitted + forecast curve (cyan dashed)
    if df_forecast is not None and len(df_forecast) > 0:
        fig.add_trace(
            go.Scatter(
                x=df_forecast["date"],
                y=df_forecast["q"],
                name="Arps Forecast",
                mode="lines",
                line=dict(color="#00D4FF", width=2, dash="dash"),
            )
        )

    fig.update_layout(
        title=dict(text="DCA Forecast — Well 15/9-F-12", font=dict(color="#FAFAFA", size=15)),
        template="plotly_dark",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="#FAFAFA", size=13),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#FAFAFA")),
        margin=dict(l=60, r=40, t=50, b=50),
        xaxis=dict(
            title="Date",
            gridcolor="#2A2A3A",
            tickfont=dict(color="#CCCCCC"),
        ),
        yaxis=dict(
            title="Oil Rate (Sm³/day)",
            gridcolor="#2A2A3A",
            tickfont=dict(color="#CCCCCC"),
        ),
    )
    return fig
