import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="EcoLens App",
    page_icon="🌲",
    layout="wide"
)

st.sidebar.title("🔍EcoLens")
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Analytics", "About" , "Greenscore counter"]
)


if page == "Home":
    st.title("🌱 Welcome to EcoLens")
    st.write("An app that guides users to choose eco-friendly products and make sustainable purchases")

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

    st.write("Built by **The Quantum Crew** for TISB Hacks")

    st.subheader("👥 Team")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### Pihu Gupta")
        st.caption("Backend & APIs\nBuilt the product database and logic")

    with col2:
        st.markdown("### Saanvi Khetan")
        st.caption("ML Engineer\nGreenwashing detection model")

    with col3:
        st.markdown("### Sinita Ray")
        st.caption("Frontend & UX\nDesigned app interface and flows")

    with col4:
        st.markdown("### Nivedha Sundar")
        st.caption("Product Lead\nStrategy, features, and deployment")

    st.divider()

    st.subheader("✨ Features")
    st.write("""
    - Greenwashing detector  
    - Product scanner  
    - Green score  
    - Actionable recommendations  
    """)            st.metric("Eco Score (0–100)", eco)
