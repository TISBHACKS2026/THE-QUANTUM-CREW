import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Quantum Crew App",
    page_icon="⚛️",
    layout="wide"
)

st.sidebar.title("⚛️ Quantum Crew")
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Analytics", "About"]
)


if page == "Home":
    st.title("🚀 Welcome to Quantum Crew")
    st.write("Hackathon demo app built with Streamlit")

    col1, col2, col3 = st.columns(3)

    col1.metric("Users", "1,204", "+12%")
    col2.metric("Accuracy", "94%", "+2%")
    col3.metric("Latency", "120ms", "-15ms")

    st.success("App is running successfully!")


elif page == "Analytics":
    st.title("📊 Analytics Dashboard")

    data = pd.DataFrame({
        "x": range(50),
        "y": np.random.randn(50).cumsum()
    })

    st.line_chart(data, x="x", y="y")

    st.subheader("Raw Data")
    st.dataframe(data)


elif page == "About":
    st.title("ℹ️ About")
    st.write("""
    Built by **The Quantum Crew** for TIS Hacks.

    Features:
    - Interactive UI
    - Real-time charts
    - Multi-page layout
    - Deployable on Streamlit Cloud
    """)
