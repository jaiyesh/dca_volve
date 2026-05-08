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
