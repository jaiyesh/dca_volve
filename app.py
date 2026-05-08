import streamlit as st

st.set_page_config(
    page_title="Volve DCA Dashboard",
    page_icon="🛢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Multi-page navigation (Streamlit 1.36+ st.navigation API)
pg = st.navigation(
    [
        st.Page("pages/1_Data_Overview.py", title="Data Overview", icon="📊"),
        st.Page("pages/2_Production_Explorer.py", title="Production Explorer", icon="📈"),
        st.Page("pages/3_DCA_Forecast.py", title="DCA Forecast", icon="🔮"),
    ]
)
pg.run()
