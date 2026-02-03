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
    ["Home", "Analytics", "About"]
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









#CALCULATIONS
import pandas as pd

# -----------------------------
# Step 0: Define file paths
# -----------------------------
PRODUCT_CSV = "products.csv"    # your cleaned product CSV
MATERIAL_CSV = "material.csv"    # your material impact CSV

# -----------------------------
# Step 1: Read CSV files
# -----------------------------
products_df = pd.read_csv(PRODUCT_CSV)
materials_df = pd.read_csv(MATERIAL_CSV)

# Convert material impact dataframe to dictionary for faster lookup
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
    
    # Loop over possible 3 materials
    for j in range(1, 4):
        material_col = f'material_{j}'
        weight_col = f'weight_{j}_g'
        material = product.get(material_col)
        weight_g = product.get(weight_col)
        
        if pd.isna(material) or pd.isna(weight_g):
            continue  # skip empty materials
        
        weight_kg = weight_g / 1000  # convert g -> kg
        
        impact = material_impact_dict.get(material)
        if impact:
            total_carbon += weight_kg * impact['carbon']
            total_water += weight_kg * impact['water']
            total_energy += weight_kg * impact['energy']
            total_waste += weight_kg * impact['waste']
        else:
            print(f"Warning: Material '{material}' not found in impact table")
    
    # Assign totals to dataframe
    products_df.at[i, 'total_carbon_kg'] = total_carbon
    products_df.at[i, 'total_water_L'] = total_water
    products_df.at[i, 'total_energy_MJ'] = total_energy
    products_df.at[i, 'total_waste_score'] = total_waste

# -----------------------------
# Step 4: Normalize metrics for eco score (0-1)
# -----------------------------
carbon_max = products_df['total_carbon_kg'].max()
water_max = products_df['total_water_L'].max()
energy_max = products_df['total_energy_MJ'].max()
waste_max = products_df['total_waste_score'].max()

products_df['carbon_norm'] = products_df['total_carbon_kg'] / carbon_max
products_df['water_norm'] = products_df['total_water_L'] / water_max
products_df['energy_norm'] = products_df['total_energy_MJ'] / energy_max
products_df['waste_norm'] = products_df['total_waste_score'] / waste_max

# -----------------------------
# Step 5: Compute final eco score (flipped so higher = better)
# -----------------------------
# Adjustable weights
w_carbon = 0.4
w_water = 0.3
w_energy = 0.2
w_waste = 0.1

products_df['eco_score'] = (
    (1 - products_df['carbon_norm']) * w_carbon +
    (1 - products_df['water_norm']) * w_water +
    (1 - products_df['energy_norm']) * w_energy +
    (1 - products_df['waste_norm']) * w_waste
)

# Convert to 0-100 scale
products_df['eco_score'] = products_df['eco_score'] * 100

# -----------------------------
# Step 6: Output results with units
# -----------------------------
output_columns = [
    'name', 'category',
    'total_carbon_kg', 'total_water_L', 'total_energy_MJ', 'total_waste_score',
    'eco_score'
]

summary_df = products_df[output_columns]

# Rename columns to include units
summary_df = summary_df.rename(columns={
    'total_carbon_kg': 'Carbon (kg CO2e)',
    'total_water_L': 'Water (L)',
    'total_energy_MJ': 'Energy (MJ)',
    'total_waste_score': 'Waste Score',
    'eco_score': 'Eco Score (0-100, higher=better)'
})

# Optional: round numeric values for cleaner demo display
summary_df = summary_df.round({
    'Carbon (kg CO2e)': 3,
    'Water (L)': 2,
    'Energy (MJ)': 2,
    'Waste Score': 3,
    'Eco Score (0-100, higher=better)': 1
})

# Save summary CSV
summary_df.to_csv("cosmetic_products_eco_scores.csv", index=False)

# Print table
print(summary_df)

# -----------------------------
# Step 7: Interactive product lookup
# -----------------------------
product_name = input("Enter product name: ").strip()

selected_product = summary_df[summary_df['name'].str.lower() == product_name.lower()]

if selected_product.empty:
    print(f"Product '{product_name}' not found in the database.")
else:
    print("\nEnvironmental impact metrics for:", product_name)
    print(selected_product.to_string(index=False))
