st.sidebar.warning("RUNNING UPDATED APP.PY")

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="EcoLens App",
    page_icon="🌲",
    layout="wide"
)

st.sidebar.title("🔍EcoLens - UPDATED")
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
    """)

elif page == "Greenscore counter":
    st.title("🌍 GreenScore Counter")
    st.write("Search for a product to view its environmental impact metrics.")

    # -----------------------------
    # Step 0: Define file paths
    # -----------------------------
    PRODUCT_CSV = "product.csv"
    MATERIAL_CSV = "material.csv"

    # -----------------------------
    # Step 1: Read CSV files
    # -----------------------------
    products_df = pd.read_csv(PRODUCT_CSV)
    materials_df = pd.read_csv(MATERIAL_CSV)

    # Convert material impact dataframe to dictionary
    material_impact_dict = {}
    for _, row in materials_df.iterrows():
        material_impact_dict[row['material']] = {
            'carbon': row['carbon_kg_per_kg'],
            'water': row['water_L_per_kg'],
            'energy': row['energy_MJ_per_kg'],
            'waste': row['waste_score']
        }

    # -----------------------------
    # Step 2: Initialize result columns
    # -----------------------------
    products_df['total_carbon_kg'] = 0.0
    products_df['total_water_L'] = 0.0
    products_df['total_energy_MJ'] = 0.0
    products_df['total_waste_score'] = 0.0

    # -----------------------------
    # Step 3: Compute impacts
    # -----------------------------
    for i, product in products_df.iterrows():
        total_carbon = 0
        total_water = 0
        total_energy = 0
        total_waste = 0

        for j in range(1, 4):
            material = product.get(f'material_{j}')
            weight_g = product.get(f'weight_{j}_g')

            if pd.isna(material) or pd.isna(weight_g):
                continue

            weight_kg = weight_g / 1000
            impact = material_impact_dict.get(material)

            if impact:
                total_carbon += weight_kg * impact['carbon']
                total_water += weight_kg * impact['water']
                total_energy += weight_kg * impact['energy']
                total_waste += weight_kg * impact['waste']

        products_df.at[i, 'total_carbon_kg'] = total_carbon
        products_df.at[i, 'total_water_L'] = total_water
        products_df.at[i, 'total_energy_MJ'] = total_energy
        products_df.at[i, 'total_waste_score'] = total_waste

    # -----------------------------
    # Step 4: Normalize
    # -----------------------------
    products_df['carbon_norm'] = products_df['total_carbon_kg'] / products_df['total_carbon_kg'].max()
    products_df['water_norm'] = products_df['total_water_L'] / products_df['total_water_L'].max()
    products_df['energy_norm'] = products_df['total_energy_MJ'] / products_df['total_energy_MJ'].max()
    products_df['waste_norm'] = products_df['total_waste_score'] / products_df['total_waste_score'].max()

    # -----------------------------
    # Step 5: Eco score (0–100, higher = better)
    # -----------------------------
    products_df['eco_score'] = (
        (1 - products_df['carbon_norm']) * 0.4 +
        (1 - products_df['water_norm']) * 0.3 +
        (1 - products_df['energy_norm']) * 0.2 +
        (1 - products_df['waste_norm']) * 0.1
    ) * 100

    # -----------------------------
    # Step 6: Final output table
    # -----------------------------
    summary_df = products_df[[
        'name', 'category',
        'total_carbon_kg', 'total_water_L',
        'total_energy_MJ', 'total_waste_score',
        'eco_score'
    ]].round(2)

    # -----------------------------
    # Step 7: USER INPUT + DISPLAY
    # -----------------------------
    product_input = st.text_input("🔍 Enter product name")

    if product_input:
        result = summary_df[
            summary_df['name'].str.lower() == product_input.lower()
        ]

        if result.empty:
            st.error("Product not found in database.")
        else:
            st.subheader("🌱 Environmental Impact Results")
            st.dataframe(result, use_container_width=True)

            eco = result.iloc[0]['eco_score']
            st.metric("Eco Score (0–100)", eco)
