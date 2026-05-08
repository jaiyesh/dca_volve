import streamlit as st
from utils.data import load_data, get_sidebar_kpis, DISPLAY_COLUMNS

st.set_page_config(page_title="Data Overview — Volve DCA", layout="wide")

df = load_data()
kpis = get_sidebar_kpis(df)

# ── Sidebar: persistent dataset context ────────────────────────────────────────
with st.sidebar:
    st.markdown("### Volve DCA Dashboard")
    st.caption("Well: **15/9-F-12**")
    st.caption(f"Period: {kpis['date_start']} – {kpis['date_end']}")
    st.metric("Total Oil", f"{kpis['total_oil_mmsm3']:.3f} MSm³")
    st.metric("Peak Rate", f"{kpis['peak_rate']:,} Sm³/day")
    st.metric("On-stream Days", f"{kpis['on_stream_days']:,}")

# ── Main content ───────────────────────────────────────────────────────────────
st.title("Data Overview")
st.caption(f"Volve field well 15/9-F-12 · {kpis['date_start']} – {kpis['date_end']} · Producing days only (ON_STREAM_HRS > 0)")

# KPI cards row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Oil Produced", f"{kpis['total_oil_mmsm3']:.3f} MSm³")
c2.metric("Peak Oil Rate", f"{kpis['peak_rate']:,} Sm³/day", help=f"On {kpis['peak_date']}")
c3.metric("On-stream Days", f"{kpis['on_stream_days']:,}")

# Water cut at end of field life (last 30 producing days)
last_30 = df.tail(30)
final_wc = last_30["WATER_CUT"].mean()
c4.metric("Water Cut (final 30 days)", f"{final_wc:.1%}")

st.divider()

# Filtered data table
st.subheader("Production Data Table")
st.caption("Filtered to producing days (ON_STREAM_HRS > 0). Showing key columns.")

display_df = df[DISPLAY_COLUMNS].copy()
display_df["DATEPRD"] = display_df["DATEPRD"].dt.strftime("%d %b %Y")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=450,
    column_config={
        "DATEPRD": st.column_config.TextColumn("Date"),
        "BORE_OIL_VOL": st.column_config.NumberColumn("Oil (Sm³/day)", format="%.1f"),
        "BORE_GAS_VOL": st.column_config.NumberColumn("Gas (Sm³/day)", format="%.1f"),
        "BORE_WAT_VOL": st.column_config.NumberColumn("Water (Sm³/day)", format="%.1f"),
        "AVG_WHP_P": st.column_config.NumberColumn("WHP (bar)", format="%.1f"),
        "AVG_CHOKE_SIZE_P": st.column_config.NumberColumn("Choke (%)", format="%.1f"),
        "ON_STREAM_HRS": st.column_config.NumberColumn("On-stream Hrs", format="%.1f"),
    },
)
st.caption(f"Showing {len(display_df):,} rows (shut-in days excluded)")
