import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import requests
from PIL import Image
import base64
import io
from rapidfuzz import process, fuzz
from openai import OpenAI

CURATED_ALTERNATIVES = {
    "Shampoo": [
        "Ethique Shampoo Bar",
        "Earth Rhythm Shampoo Bar",
        "Bare Anatomy Concentrated Shampoo"
    ],
    "Cream": [
        "Minimalist Marula Oil Moisturizer",
        "Earth Rhythm Phyto Clear Moisturizer",
        "Plum Green Tea Moisturizer"
    ],
    "Sunscreen": [
        "Raw Beauty Wellness Sunscreen Stick",
        "Minimalist SPF 50 (50g)",
        "Dot & Key Sunscreen Stick"
    ],
    "Body Wash": [
        "Ethique Solid Body Wash Bar",
        "Earth Rhythm Body Wash Bar",
        "Plum BodyLovin Body Wash Bar"
    ],
    "Food": [
        "Dark chocolate (higher cocoa %, less packaging)",
        "Baked snacks instead of fried",
        "Local brand snacks with paper packaging"
    ],
    "Drink": [
        "Returnable glass bottle drinks",
        "Powder concentrates",
        "Water in aluminum cans"
    ]
}


# OPENAI SETUP (GLOBAL)

OpenAIKey = st.secrets["OpenAIKey"]
client = OpenAI(api_key=OpenAIKey)

def get_greener_alternatives(current_product_name, summary_df, max_alternatives=5):

    current = summary_df[summary_df["name"] == current_product_name]

    if current.empty:
        return []

    row = current.iloc[0]
    category = row["category"]
    brand = row["brand"]
    current_score = row["eco_score"]

    # ---------- DATA-DRIVEN ----------
    better = summary_df[
        (summary_df["category"] == category) &
        (summary_df["eco_score"] > current_score) &
        (summary_df["name"] != current_product_name)
    ].sort_values("eco_score", ascending=False)

    results = []

    for _, alt in better.head(max_alternatives).iterrows():
        diff = alt["eco_score"] - current_score
        results.append({
            "name": alt["name"],
            "eco_score": alt["eco_score"],
            "improvement": f"{diff:.0f} points better eco score",
            "score_diff": diff
        })

    return results


def image_to_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def ocr_image(image):
    img_b64 = image_to_base64(image)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Extract ALL visible text from this product packaging."
                },
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{img_b64}"
                }
            ]
        }]
    )

    return response.output_text

def extract_product_name(all_text):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
        From the following packaging text, extract the MOST LIKELY product name.
        Respond ONLY with the product name.

        TEXT:
        {all_text}
        """
    )

    return response.output_text.strip()

def fuzzy_match_product(name, summary_df):
    match, score, _ = process.extractOne(
        name,
        summary_df['name'].tolist(),
        scorer=fuzz.token_sort_ratio
    )
    return match, score

st.set_page_config(page_title=" EcoLens", page_icon="🌱", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* Root variables - Option 5 Palette */
:root {
  --primary-green: #5D8A66;
  --secondary-cream: #F5F1E8;
  --accent-coral: #E8956B;
  --text-dark: #3A4A3A;
  --success-green: #7BA57E;
  --warning-amber: #F4B860;
  --error-red: #D97B6C;
  --card-white: #FFFFFF;
  --border-light: #E0DED8;
  --deep-moss: #4d7554;
}

/* Global Typography */
h1, h2, h3, h4, h5, h6 {
  font-family: 'DM Serif Display', serif !important;
  color: var(--text-dark) !important;
  letter-spacing: -0.02em !important;
}

p, div, span, label, li, input, select {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.block-container { 
  padding-top: 1rem !important; 
  background: var(--secondary-cream);
}

/* Sticky header box */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 999;
  background: linear-gradient(180deg, rgba(58, 74, 58, 0.98) 0%, rgba(45, 60, 45, 0.95) 100%);
  padding: 0.8rem 0 1rem 0;
  border-bottom: 3px solid var(--primary-green);
  box-shadow: 0 8px 24px rgba(93, 138, 102, 0.3);
  backdrop-filter: blur(12px);
}

/* Button styling with earthy feel */
.stButton > button {
  background: linear-gradient(135deg, var(--primary-green) 0%, var(--deep-moss) 100%) !important;
  color: var(--secondary-cream) !important;
  border: none !important;
  border-radius: 16px !important;
  font-weight: 600 !important;
  padding: 14px 32px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  box-shadow: 0 4px 16px rgba(93, 138, 102, 0.25) !important;
  font-size: 15px !important;
  letter-spacing: 0.3px !important;
}

.stButton > button:hover {
  background: linear-gradient(135deg, var(--deep-moss) 0%, var(--primary-green) 100%) !important;
  box-shadow: 0 8px 28px rgba(93, 138, 102, 0.4) !important;
  transform: translateY(-3px) scale(1.02) !important;
}

/* Success messages */
.success {
  background: linear-gradient(135deg, #e8f5e9 0%, var(--secondary-cream) 100%) !important;
  border-left: 5px solid var(--success-green) !important;
  color: var(--text-dark) !important;
  border-radius: 14px !important;
  padding: 18px 22px !important;
}

/* Info messages */
.info {
  background: linear-gradient(135deg, var(--secondary-cream) 0%, #faf8f3 100%) !important;
  border-left: 5px solid var(--primary-green) !important;
  color: var(--text-dark) !important;
  border-radius: 14px !important;
  padding: 18px 22px !important;
}

/* Warning messages */
.warning {
  background: linear-gradient(135deg, #fff4e6 0%, var(--secondary-cream) 100%) !important;
  border-left: 5px solid var(--warning-amber) !important;
  color: #6b4423 !important;
  border-radius: 14px !important;
  padding: 18px 22px !important;
}

/* Organic dividers */
.stDivider {
  margin: 3rem 0 !important;
  border-color: var(--border-light) !important;
  opacity: 0.4;
}

/* Smooth transitions */
* {
  transition: background-color 0.3s ease, color 0.3s ease, transform 0.3s ease !important;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 10px;
}

::-webkit-scrollbar-track {
  background: var(--secondary-cream);
}

::-webkit-scrollbar-thumb {
  background: var(--primary-green);
  border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--deep-moss);
}
</style>
""", unsafe_allow_html=True)



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

# -----------------------------
# FLAGS (BEAUTY + FOOD)
# -----------------------------
ALL_FLAGS = [
    "microplastics",
    "petroleum",
    "silicones",
    "recyclable_packaging",
    "eco_certified",
    "ultra_processed",
    "high_sugar",
    "palm_oil",
    "animal_based"
]

for c in ALL_FLAGS:
    if c not in products_df.columns:
        products_df[c] = 0

products_df[ALL_FLAGS] = products_df[ALL_FLAGS].fillna(0).astype(int)

# =============================
# MATERIAL IMPACT DICTIONARY
# =============================
material_impact_dict = {}
for _, row in materials_df.iterrows():
    material_impact_dict[row['material']] = {
        'carbon': row['carbon_kg_per_kg'],
        'water': row['water_L_per_kg'],
        'energy': row['energy_MJ_per_kg'],
        'waste': row['waste_score']
    }

# =============================
# INITIALIZE RESULTS
# =============================
products_df["total_carbon_kg"] = 0.0
products_df["total_water_L"] = 0.0
products_df["total_energy_MJ"] = 0.0
products_df["total_waste_score"] = 0.0

# =============================
# PACKAGING IMPACT
# =============================
for i, p in products_df.iterrows():
    carbon = water = energy = 0
    waste_vals = []

    for j in range(1, 4):
        mat = p.get(f"material_{j}")
        wt = p.get(f"weight_{j}_g")

        if pd.isna(mat) or pd.isna(wt):
            continue

        imp = material_impact_dict.get(mat)
        if not imp:
            continue

        kg = wt / 1000
        carbon += kg * imp["carbon"]
        water += kg * imp["water"]
        energy += kg * imp["energy"]
        waste_vals.append(imp["waste"])

    products_df.at[i,"total_carbon_kg"] = carbon
    products_df.at[i,"total_water_L"] = water
    products_df.at[i,"total_energy_MJ"] = energy
    products_df.at[i,"total_waste_score"] = np.mean(waste_vals) if waste_vals else 0

# =============================
# NORMALIZATION CAPS
# =============================
products_df["carbon_norm"] = (products_df["total_carbon_kg"] / 0.5).clip(0,1)
products_df["water_norm"]  = (products_df["total_water_L"] / 10).clip(0,1)
products_df["energy_norm"] = (products_df["total_energy_MJ"] / 20).clip(0,1)
products_df["waste_norm"]  = (products_df["total_waste_score"] / 5).clip(0,1)

# =============================
# PACKAGING SCORE (0-100)
# =============================
products_df["packaging_score"] = (
    (1-products_df["carbon_norm"])*0.35 +
    (1-products_df["water_norm"])*0.25 +
    (1-products_df["energy_norm"])*0.25 +
    (1-products_df["waste_norm"])*0.15
)*100

products_df["packaging_score"] = products_df["packaging_score"].round(1)

# =============================
# INGREDIENT SCORE (CATEGORY AWARE)
# =============================

def ingredient_score(row):
    cat = row["category"].lower()

    # Beauty
    if cat in ["cream","shampoo","body wash","sunscreen"]:
        score = 100 - (
            40*row["microplastics"] +
            35*row["petroleum"] +
            25*row["silicones"]
        )

    # Food & Drinks
    else:
        score = 100 - (
            35*row["ultra_processed"] +
            25*row["high_sugar"] +
            20*row["palm_oil"] +
            20*row["animal_based"]
        )

    return max(0, min(100, score))

products_df["ingredient_score"] = products_df.apply(ingredient_score, axis=1)

# =============================
# BONUS SCORE
# =============================
products_df["bonus_score"] = 60 + (
    20*products_df["recyclable_packaging"] +
    20*products_df["eco_certified"]
)

products_df["bonus_score"] = products_df["bonus_score"].clip(0,100)

# =============================
# FINAL ECOSCORE
# =============================
products_df["eco_score"] = (
    0.50*products_df["packaging_score"] +
    0.40*products_df["ingredient_score"] +
    0.10*products_df["bonus_score"]
).round(1)

# =============================
# FINAL SUMMARY
# =============================
summary_df = products_df[[
    "name",
    "brand",
    "category",
    "total_carbon_kg",
    "total_water_L",
    "total_energy_MJ",
    "total_waste_score",
    "packaging_score",
    "ingredient_score",
    "bonus_score",
    "eco_score",
    *ALL_FLAGS
]].copy()



# -------------------------
# Navigation state
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def go(page_name: str):
    st.session_state.page = page_name

# -------------------------
# Sticky header (always visible)
# -------------------------
st.markdown('<div class="sticky-header">', unsafe_allow_html=True)

st.markdown(
    """
    <h1 style="text-align:center; font-size:82px; margin:0; color:#9cb380; text-shadow: 3px 3px 6px rgba(93, 138, 102, 0.4); letter-spacing: -0.03em;">
        EcoLens
    </h1>
    <p style="text-align:center; font-size:19px; color:#c5d4b8; margin-top:8px; margin-bottom:18px; font-weight: 400; letter-spacing: 0.5px;">
        Make smarter, sustainable buying decisions
    </p>
    """,
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns([1,1,1,1])
with c1:
    st.button("GreenScore", use_container_width=True, on_click=go, args=("GreenScore",))
with c2:
    st.button("AI Chatbot", use_container_width=True, on_click=go, args=("Chatbot",))
with c3:
    st.button("Impact Dashboard", use_container_width=True, on_click=go, args=("Impact Dashboard",))
with c4:
    st.button("Your Next Steps", use_container_width=True, on_click=go, args=("NextSteps",))


st.markdown("</div>", unsafe_allow_html=True)
st.write("")  # spacer

# -------------------------
# HOME
# -------------------------
if st.session_state.page == "Home":

    left, right = st.columns([1.2, 1.8], gap="large")

    with left:
        st.markdown("""
            <div style="height:440px; overflow:hidden; border-radius:24px; box-shadow: 0 12px 32px rgba(93, 138, 102, 0.3); position: relative;">
                <img src="https://images.openai.com/static-rsc-3/L_9-L2VXhvFW5NZZvI6VLjA1QxHDiDeV5vyXsgKqM2ycJVtMFds_HEsJfhXYdziNs9fdDa4f0k4koZsaN3gehTxDddohscLt0wYAfwvMxRE?purpose=fullsize"
                     style="width:100%; height:100%; object-fit:cover; filter: brightness(0.95) saturate(1.1);">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(180deg, transparent 0%, rgba(93, 138, 102, 0.1) 100%);"></div>
            </div>
        """, unsafe_allow_html=True)
    
    with right:
        st.markdown(
            """<div style="height:440px; display:flex; flex-direction:column; justify-content:center; padding-left: 20px;">
    <h2 style="font-size:42px; margin-bottom:22px; color:#5D8A66; font-family: 'DM Serif Display', serif; line-height: 1.2;">What is EcoLens?</h2>
    <p style="font-size:20px; line-height:1.8; max-width:620px; color:#3A4A3A; font-weight: 400;">
    EcoLens helps people understand the real environmental impact of the products they buy, so they can make more informed and sustainable choices.
    </p>
    </div>""",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<h2 style="font-size: 36px; margin-bottom: 16px; color: #5D8A66;">The Hidden Cost of Everyday Products</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 17px; line-height: 1.7; color: #3A4A3A;">Every year, the world produces over 400 million tonnes of plastic waste, and nearly half of this comes from single-use packaging like bottles, bags, wrappers, and cartons. Only around 9% of all plastic ever produced has been recycled, while the rest ends up in landfills, incinerators, or in the environment.</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 17px; line-height: 1.7; color: #3A4A3A;">Packaging alone can account for 20-40% of a product\'s total environmental footprint, yet this hidden cost is rarely visible when we shop. Most of the time, consumers only see branding and marketing claims, not the true environmental impact behind a product.</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<h2 style="font-size: 36px; margin-bottom: 16px; color: #5D8A66;">The Problem</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 17px; line-height: 1.7; color: #3A4A3A;">Sustainability labels are vague and poorly regulated, so consumers often rely on marketing language instead of real data. Many of these claims are misleading, allowing greenwashing to go unnoticed. Because people lack the time and expertise to properly assess environmental impact, they make well-intentioned but poor choices. Additionally, there is no standardized way to verify eco-claims, and most existing apps reduce sustainability to simple green or red labels, hiding the real environmental costs of everyday products.</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<h2 style="font-size: 36px; margin-bottom: 16px; color: #5D8A66;">Small Choices, Big Impact</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 17px; line-height: 1.7; color: #3A4A3A;">A single purchase may feel insignificant, but when millions of people repeat small decisions every day, the impact becomes massive. If just 1 million people replaced one single-use plastic bottle per day, over 7,000 tonnes of plastic waste could be prevented each year. EcoLens makes these invisible impacts visible, so your everyday choices can become part of a much bigger change.</p>', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown('<h2 style="font-size: 40px; margin-bottom: 28px; color: #5D8A66; text-align: center;">Key Features</h2>', unsafe_allow_html=True)

    components.html("""
<div style="
    background: linear-gradient(135deg, #5D8A66 0%, #4d7554 100%);
    border-radius:24px;
    padding:50px 42px;
    margin-top:20px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    box-shadow: 0 12px 32px rgba(93, 138, 102, 0.35);
">
  <div style="display:flex; gap:38px; align-items:center;">

    <div style="flex:1.2;">
      <h2 style="margin:0 0 16px 0; font-size:42px; color:#f5f1e8; font-family: 'DM Serif Display', serif; letter-spacing: -0.02em;">
        GreenScore Tracker
      </h2>

      <p style="margin:0 0 18px 0; font-size:19px; line-height:1.8; color:#e8f5e9; font-weight: 400;">
        Scan personal-care products and get a transparent sustainability score with clear reasons.
      </p>

      <ul style="margin:0; padding-left:24px; font-size:18px; line-height:1.9; color:#e8f5e9; font-weight: 400;">
        <li style="margin-bottom: 8px;">Product Scan</li>
        <li style="margin-bottom: 8px;">Score breakdown (ingredients, packaging, claims)</li>
        <li>Better alternatives for your purpose</li>
      </ul>
    </div>

    <div style="flex:1; display:flex; justify-content:flex-end;">
      <div style="
          width:540px;
          height:340px;
          border-radius:20px;
          overflow:hidden;
          box-shadow: 0 14px 40px rgba(0,0,0,0.4);
          background: rgba(245,241,232,0.08);
          border: 3px solid rgba(123,165,126,0.25);
      ">
        <img src="https://www.iberdrola.com/documents/20125/40513/huella-de-carbono-746x419.jpg/f61f98a2-7c51-27f9-31d2-41b1dafe6bf7?t=1738248418273"
             style="width:100%; height:100%; object-fit:cover; filter: brightness(0.92) saturate(1.05);">
      </div>
    </div>

  </div>
</div>
""", height=460)


    
    #-------------------------
    # AI Chatbot
    #-------------------------

    components.html("""
    <div style="
        background: linear-gradient(135deg, #7BA57E 0%, #6b9570 100%);
        border-radius:24px;
        padding:50px 42px;
        margin-top:28px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        box-shadow: 0 12px 32px rgba(93, 138, 102, 0.35);
    ">
      <div style="display:flex; gap:38px; align-items:center;">
    
        <!-- LEFT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-start;">
          <div style="
              width:540px;
              height:340px;
              border-radius:20px;
              overflow:hidden;
              box-shadow: 0 14px 40px rgba(0,0,0,0.4);
              background: rgba(245,241,232,0.08);
              border: 3px solid rgba(123,165,126,0.25);
          ">
            <img src="https://beetroot.co/wp-content/uploads/sites/2/2024/12/Cover_AI-chatbots-in-GreenTech.png"
                 style="width:100%; height:100%; object-fit:cover; filter: brightness(0.92) saturate(1.05);">
          </div>
        </div>
    
        <!-- RIGHT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 16px 0; font-size:42px; color:#f5f1e8; font-family: 'DM Serif Display', serif; letter-spacing: -0.02em;">
            AI Chatbot
          </h2>
    
          <p style="margin:0 0 18px 0; font-size:19px; line-height:1.8; color:#e8f5e9; font-weight: 400;">
            Ask questions in plain English and get smart, personalized sustainability advice instantly.
          </p>
    
          <ul style="margin:0; padding-left:24px; font-size:18px; line-height:1.9; color:#e8f5e9; font-weight: 400;">
            <li style="margin-bottom: 8px;">Ask about ingredients and claims</li>
            <li style="margin-bottom: 8px;">Get product recommendations</li>
            <li>Tips for safer / sustainable swaps</li>
          </ul>
        </div>
    
      </div>
    </div>
    """, height=460)

    #---------------------
    # Impact Score
    #---------------------
  
    components.html("""
    <div style="
        background: linear-gradient(135deg, #5D8A66 0%, #4d7554 100%);
        border-radius:24px;
        padding:50px 42px;
        margin-top:28px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        box-shadow: 0 12px 32px rgba(93, 138, 102, 0.35);
    ">
      <div style="display:flex; gap:38px; align-items:center;">
    
        <!-- LEFT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 16px 0; font-size:42px; color:#f5f1e8; font-family: 'DM Serif Display', serif; letter-spacing: -0.02em;">
            Impact Score
          </h2>
    
          <p style="margin:0 0 18px 0; font-size:19px; line-height:1.8; color:#e8f5e9; font-weight: 400;">
            See the real environmental impact of every purchase in clear, easy-to-understand metrics.
          </p>
    
          <ul style="margin:0; padding-left:24px; font-size:18px; line-height:1.9; color:#e8f5e9; font-weight: 400;">
            <li style="margin-bottom: 8px;">Trends in Purchases</li>
            <li style="margin-bottom: 8px;">Impact Log</li>
            <li style="margin-bottom: 8px;">Compare products side-by-side</li>
            <li>Visualize your eco progress over time</li>
          </ul>
        </div>
    
        <!-- RIGHT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-end;">
          <div style="
              width:540px;
              height:340px;
              border-radius:20px;
              overflow:hidden;
              box-shadow: 0 14px 40px rgba(0,0,0,0.4);
              background: rgba(245,241,232,0.08);
              border: 3px solid rgba(123,165,126,0.25);
          ">
            <img src="https://greenscoreapp.com/wp-content/uploads/2024/09/Empowering-Sustainability-Through-Innovation-image2-Green-Score.webp"
                 style="width:100%; height:100%; object-fit:cover; filter: brightness(0.92) saturate(1.05);">
          </div>
        </div>
    
      </div>
    </div>
    """, height=460)

    #-------------------------
    # Your Next Steps
    #-------------------------

    components.html("""
    <div style="
        background: linear-gradient(135deg, #7BA57E 0%, #6b9570 100%);
        border-radius:24px;
        padding:50px 42px;
        margin-top:28px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        box-shadow: 0 12px 32px rgba(93, 138, 102, 0.35);
    ">
      <div style="display:flex; gap:38px; align-items:center;">
    
        <!-- LEFT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-start;">
          <div style="
              width:540px;
              height:340px;
              border-radius:20px;
              overflow:hidden;
              box-shadow: 0 14px 40px rgba(0,0,0,0.4);
              background: rgba(245,241,232,0.08);
              border: 3px solid rgba(123,165,126,0.25);
          ">
            <img src="https://www.shutterstock.com/image-photo/desk-displays-esg-metrics-sustainable-260nw-2672441077.jpg"
                 style="width:100%; height:100%; object-fit:cover; filter: brightness(0.92) saturate(1.05);">
          </div>
        </div>
    
        <!-- RIGHT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 16px 0; font-size:42px; color:#f5f1e8; font-family: 'DM Serif Display', serif; letter-spacing: -0.02em;">
            Your Next Steps
          </h2>
    
          <p style="margin:0 0 18px 0; font-size:19px; line-height:1.8; color:#e8f5e9; font-weight: 400;">
            Clear, practical steps you can take to meaningfully reduce your environmental impact.
          </p>
    
          <ul style="margin:0; padding-left:24px; font-size:18px; line-height:1.9; color:#e8f5e9; font-weight: 400;">
            <li style="margin-bottom: 8px;">Better Alternatives</li>
            <li style="margin-bottom: 8px;">Eco-friendly suggestions</li>
            <li>Microhabits</li>
          </ul>
        </div>
    
      </div>
    </div>
    """, height=460)

# -------------------------
# GREEN SCORE PAGE
# -------------------------
elif st.session_state.page == "GreenScore":
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.markdown('<h1 style="font-size: 48px; margin-bottom: 8px; color: #5D8A66;">GreenScore</h1>', unsafe_allow_html=True)
    
    # Check if user clicked an alternative product
    if "impact_history" not in st.session_state:
        st.session_state.impact_history = pd.DataFrame(columns=[
            "Product", "Category", "Eco Score",
            "Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"
        ])
    if "logged_keys" not in st.session_state:
        st.session_state.logged_keys = set()
    
    # -----------------------------
    # Step 7: USER INPUT + DISPLAY
    # -----------------------------
    st.markdown('<h3 style="font-size: 24px; margin-top: 24px; margin-bottom: 16px; color: #3A4A3A;">Scan Product</h3>', unsafe_allow_html=True)
    
    image_file = st.camera_input("Take a photo of the product")
    
    if image_file is None:
        st.session_state.ocr_processed = False
    
    if image_file and not st.session_state.get("ocr_processed", False):
        image = Image.open(image_file)
    
        with st.spinner("Reading packaging text..."):
            all_text = ocr_image(image)
    
        with st.spinner("Identifying product..."):
            detected_name = extract_product_name(all_text)
            matched_name, confidence = fuzzy_match_product(detected_name, summary_df)
    
        st.success(f"Detected: {matched_name}")
        st.session_state.selected_product = matched_name
    
        #Mark OCR as done
        st.session_state.ocr_processed = True
    
        #Reset selectbox so it updates
        if "product_selectbox" in st.session_state:
            del st.session_state["product_selectbox"]
    
        
        st.rerun()

    
    # -----------------------------
    # PRODUCT SEARCH (SINGLE SOURCE OF TRUTH)
    # -----------------------------
    product_options = sorted(summary_df["name"].unique())
    preselected_product = None
    
    # Priority:
    # 1. Alternative click
    # 2. Previously selected product
    if "selected_alternative" in st.session_state:
        preselected_product = st.session_state.selected_alternative
    elif "selected_product" in st.session_state:
        preselected_product = st.session_state.selected_product
    
    # -----------------------------
    # SINGLE SELECTBOX (NO DOUBLE CLICK)
    # -----------------------------
    if preselected_product in product_options:
        product_input = st.selectbox(
            "🔍 Search for a product",
            options=product_options,
            index=product_options.index(preselected_product),
            key="product_selectbox",
            placeholder="Start typing to search..."
        )
    else:
        product_input = st.selectbox(
            "🔍 Search for a product",
            options=product_options,
            index=None,
            key="product_selectbox",
            placeholder="Start typing to search..."
        )
    
    # -----------------------------
    # CLEAN UP ONE-TIME FLAGS
    # -----------------------------
    if "selected_alternative" in st.session_state:
        del st.session_state["selected_alternative"]
    
    # -----------------------------
    # PERSIST SELECTION (IMMEDIATE)
    # -----------------------------
    if product_input:
        st.session_state.selected_product = product_input
    
    # -----------------------------
    # DISPLAY SELECTED PRODUCT
    # -----------------------------
    if "selected_product" in st.session_state:
        product_name = st.session_state.selected_product
        result = summary_df[summary_df["name"] == product_name]
    
        if result.empty:
            st.error("Product not found in database.")
        else:
            r = result.iloc[0]
            st.divider()


            
            # ---------- ECO SCORE WITH RADIAL DESIGN ----------
            st.markdown("### Eco Score")
            
            score_col1, score_col2 = st.columns([2, 3])
            
            with score_col1:
                # Radial score display
                score_value = r['eco_score']
                
                # Determine color and badge based on score
                if score_value >= 80:
                    badge_color = "#5D8A66"
                    badge_text = "Excellent"
                    emoji = "🌟"
                    ring_color = "#7BA57E"
                elif score_value >= 60:
                    badge_color = "#7BA57E"
                    badge_text = "Good"
                    emoji = "👍"
                    ring_color = "#9cb380"
                elif score_value >= 40:
                    badge_color = "#F4B860"
                    badge_text = "Moderate"
                    emoji = "⚠️"
                    ring_color = "#F4B860"
                else:
                    badge_color = "#D97B6C"
                    badge_text = "Needs Improvement"
                    emoji = "❗"
                    ring_color = "#D97B6C"
                
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {badge_color} 0%, {ring_color} 100%);
                        border-radius: 50%;
                        width: 240px;
                        height: 240px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 12px 40px rgba(93, 138, 102, 0.4);
                        margin: 20px auto;
                        position: relative;
                        border: 8px solid rgba(245, 241, 232, 0.3);
                    ">
                        <div style="
                            position: absolute;
                            top: -12px;
                            right: -12px;
                            background: #F5F1E8;
                            border-radius: 50%;
                            width: 56px;
                            height: 56px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                            font-size: 28px;
                        ">
                            {emoji}
                        </div>
                        <h1 style='color: #F5F1E8; margin: 0; font-size: 72px; font-weight: 700; text-shadow: 2px 2px 8px rgba(0,0,0,0.2);'>{score_value}</h1>
                        <p style='color: rgba(245, 241, 232, 0.9); margin: 8px 0 0 0; font-size: 18px; font-weight: 500;'>out of 100</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with score_col2:
                st.markdown(f"""
                    <div style="padding: 30px 0;">
                        <div style="
                            background: linear-gradient(135deg, {badge_color}15 0%, {badge_color}08 100%);
                            color: {badge_color};
                            padding: 20px 32px;
                            border-radius: 18px;
                            display: inline-block;
                            font-size: 28px;
                            font-weight: 700;
                            margin-bottom: 24px;
                            box-shadow: 0 6px 20px {badge_color}25;
                            border: 2px solid {badge_color}40;
                            font-family: 'DM Serif Display', serif;
                        ">
                            {badge_text}
                        </div>
                        <p style="color: #3A4A3A; margin-top: 16px; line-height: 1.8; font-size: 17px; font-weight: 400;">
                            This score reflects the overall environmental impact across carbon, water, energy, and waste metrics. It considers packaging materials, ingredient sustainability, and eco-certifications.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Enhanced progress bar
            st.markdown(f"""
                <div style="margin: 32px 0;">
                    <div style="
                        background: rgba(93, 138, 102, 0.12);
                        border-radius: 16px;
                        height: 18px;
                        overflow: hidden;
                        box-shadow: inset 0 2px 6px rgba(0,0,0,0.08);
                    ">
                        <div style="
                            background: linear-gradient(90deg, {ring_color} 0%, {badge_color} 100%);
                            width: {score_value}%;
                            height: 100%;
                            border-radius: 16px;
                            transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
                            box-shadow: 0 0 12px {badge_color}60;
                        "></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
            st.divider()
    
            # ---------- ENHANCED METRICS ----------
            st.markdown("### Environmental Impact Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
    
            metrics_data = [
                {
                    "icon": "🌫",
                    "title": "Carbon Footprint",
                    "value": f"{r['total_carbon_kg']:.2f}",
                    "unit": "kg CO₂e",
                    "color": "#E8956B",
                    "bg_gradient": "linear-gradient(135deg, #FFF4E6 0%, #F5F1E8 100%)"
                },
                {
                    "icon": "💧",
                    "title": "Water Usage",
                    "value": f"{r['total_water_L']:.1f}",
                    "unit": "Liters",
                    "color": "#5D8A66",
                    "bg_gradient": "linear-gradient(135deg, #E8F5E9 0%, #F5F1E8 100%)"
                },
                {
                    "icon": "⚡",
                    "title": "Energy Use",
                    "value": f"{r['total_energy_MJ']:.1f}",
                    "unit": "MJ",
                    "color": "#F4B860",
                    "bg_gradient": "linear-gradient(135deg, #FFF9E6 0%, #F5F1E8 100%)"
                },
                {
                    "icon": "🗑",
                    "title": "Waste Impact",
                    "value": f"{r['total_waste_score']:.1f}",
                    "unit": "Score",
                    "color": "#7BA57E",
                    "bg_gradient": "linear-gradient(135deg, #F5F1E8 0%, #FAF8F3 100%)"
                }
            ]
            
            for col, data in zip([col1, col2, col3, col4], metrics_data):
                with col:
                    st.markdown(f"""
                        <div style="
                            background: {data['bg_gradient']};
                            border-left: 5px solid {data['color']};
                            border-radius: 16px;
                            padding: 24px 18px;
                            text-align: center;
                            box-shadow: 0 6px 18px rgba(93, 138, 102, 0.12);
                            transition: transform 0.3s ease, box-shadow 0.3s ease;
                            cursor: pointer;
                        " onmouseover="this.style.transform='translateY(-6px)'; this.style.boxShadow='0 12px 28px rgba(93, 138, 102, 0.2)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 18px rgba(93, 138, 102, 0.12)';">
                            <div style="font-size: 2.4em; margin-bottom: 12px;">{data['icon']}</div>
                            <div style="color: {data['color']}; font-size: 0.88em; margin-bottom: 8px; font-weight: 600; letter-spacing: 0.3px;">{data['title']}</div>
                            <div style="color: #3A4A3A; font-size: 2em; font-weight: 700; font-family: 'DM Serif Display', serif;">{data['value']}</div>
                            <div style="color: {data['color']}; font-size: 0.78em; margin-top: 4px; font-weight: 500;">{data['unit']}</div>
                        </div>
                    """, unsafe_allow_html=True)

            # ---------- INGREDIENT FLAGS (enhanced design) ----------
            st.markdown("### Ingredient Flags")
            
            flag_defs = [
                {
                    "key": "microplastics",
                    "title": "Microplastics",
                    "emoji": "🧬",
                    "present": int(r["microplastics"]) == 1,
                    "why": "Microplastics can persist in waterways and harm aquatic life when washed down drains."
                },
                {
                    "key": "silicones",
                    "title": "Silicones",
                    "emoji": "🧴",
                    "present": int(r["silicones"]) == 1,
                    "why": "Some silicones are persistent and can contribute to long-lasting pollution in the environment."
                },
                {
                    "key": "petroleum",
                    "title": "Petroleum-derived",
                    "emoji": "🛢️",
                    "present": int(r["petroleum"]) == 1,
                    "why": "Petroleum-based ingredients come from fossil fuels, increasing reliance on non-renewable resources."
                },
            ]
            
            present_flags = [f for f in flag_defs if f["present"]]
            
            if present_flags:
                cols = st.columns(len(present_flags))
                for col, flag in zip(cols, present_flags):
                    with col:
                        st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, #FFF4E6 0%, #F5F1E8 100%);
                                border-left: 5px solid #E8956B;
                                border-radius: 16px;
                                padding: 22px 18px;
                                box-shadow: 0 6px 18px rgba(232, 149, 107, 0.15);
                                min-height: 165px;
                                transition: transform 0.3s ease;
                            " onmouseover="this.style.transform='translateY(-4px)';" onmouseout="this.style.transform='translateY(0)';">
                                <div style="font-size: 2.2em; margin-bottom: 10px;">{flag["emoji"]}</div>
                                <div style="font-weight: 700; font-size: 1.08em; color: #3A4A3A; margin-bottom: 4px;">{flag["title"]}</div>
                                <div style="color: #E8956B; font-size: 0.85em; font-weight: 600; margin-bottom: 12px;">⚠️ Present</div>
                                <div style="margin-top: 12px; font-size: 0.9em; line-height: 1.5; color: #3A4A3A;">
                                    {flag["why"]}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #E8F5E9 0%, #F5F1E8 100%);
                        border-left: 5px solid #7BA57E;
                        border-radius: 16px;
                        padding: 20px 24px;
                        box-shadow: 0 6px 18px rgba(123, 165, 126, 0.15);
                    ">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 2em;">✅</span>
                            <span style="color: #3A4A3A; font-size: 1.05em; font-weight: 500;">No ingredient red flags detected for this product (based on our database).</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
            st.markdown("<br>", unsafe_allow_html=True)

            
            st.subheader("🛒 Purchase Logging")
            
            if st.button("✅ Log this product as purchased", use_container_width=True):
                log_key = f"{product_input}_{r['eco_score']}"
            
                if log_key not in st.session_state.logged_keys:
                    st.session_state.impact_history.loc[len(st.session_state.impact_history)] = {
                        "Product": product_input,
                        "Category": r["category"],
                        "Eco Score": r["eco_score"],
                        "Carbon (kg)": r["total_carbon_kg"],
                        "Water (L)": r["total_water_L"],
                        "Energy (MJ)": r["total_energy_MJ"],
                        "Waste Score": r["total_waste_score"]
                    }
                    st.session_state.logged_keys.add(log_key)
                    st.success("🎉 Product logged! Your Impact Dashboard has been updated.")
                else:
                    st.info("This product is already logged as purchased.")


            
            #-------------------------------------
            # Greener Alternatives
            #-------------------------------------
            
            st.subheader("Greener Alternatives")
            st.caption("Click any product to view its full eco score")
            
            alternatives = get_greener_alternatives(product_input, summary_df, max_alternatives=5)
            
            # ✅ CASE 1: NO greener alternatives
            if not alternatives:
                st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #E8F5E9 0%, #F5F1E8 100%);
                        border-left: 5px solid #7BA57E;
                        border-radius: 16px;
                        padding: 24px 28px;
                        box-shadow: 0 6px 18px rgba(123, 165, 126, 0.15);
                    ">
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <span style="font-size: 2.4em;">🎉</span>
                            <div>
                                <div style="color: #3A4A3A; font-size: 1.15em; font-weight: 600; margin-bottom: 4px;">Great choice!</div>
                                <div style="color: #5D8A66; font-size: 0.95em;">This is already one of the greenest options in its category.</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # ✅ CASE 2: Greener alternatives exist
            else:
                for alt in alternatives:
            
                        st.markdown(
                            f"""
                            <div style="
                                background: linear-gradient(135deg, #E8F5E9 0%, #F5F1E8 100%);
                                border-left: 6px solid #5D8A66;
                                border-radius: 18px;
                                padding: 22px 24px;
                                margin-bottom: 16px;
                                box-shadow: 0 6px 20px rgba(93, 138, 102, 0.18);
                                transition: all 0.3s ease;
                            " onmouseover="this.style.transform='translateX(6px)'; this.style.boxShadow='0 8px 28px rgba(93, 138, 102, 0.25)';" onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 6px 20px rgba(93, 138, 102, 0.18)';">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="color:#3A4A3A; font-size:18px; font-weight: 700;">{alt['name']}</strong><br>
                                        <span style="color:#5D8A66; font-size:15px; font-weight: 500;"> {alt['improvement']}</span>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color:#5D8A66; font-size:32px; font-weight:800; font-family: 'DM Serif Display', serif;">
                                            {alt['eco_score']}
                                        </div>
                                        <div style="color:#7BA57E; font-size:13px; font-weight: 600;">
                                            +{alt['score_diff']:.1f} points
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


            # =============================
            # AI PRODUCT CHATBOT (enhanced)
            # =============================
            st.divider()
            st.markdown('<h3 style="font-size: 28px; margin-top: 20px; margin-bottom: 12px; color: #5D8A66;">AI Insight: Explore This Product</h3>', unsafe_allow_html=True)

            st.caption(
                "Ask in-depth questions about this product's ingredients, impacts, and "
                "how to make better purchase choices."
            )

            from openai import OpenAI
            client = OpenAI(api_key=st.secrets["OpenAIKey"])

            # -----------------------------
            # INIT / RESET PRODUCT CHAT MEMORY
            # -----------------------------
            if (
                "product_ai_messages" not in st.session_state
                or st.session_state.get("product_chat_product") != product_input
            ):
                st.session_state.product_chat_product = product_input
                
                # Use the actual selected product data (r) instead of hardcoded first product
                st.session_state.product_ai_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a product-focused sustainability assistant.\n\n"
                            "You help users understand a SINGLE product in depth.\n\n"
                            "You may answer questions about:\n"
                            "- why this product scores the way it does\n"
                            "- ingredient and material impacts\n"
                            "- microplastics, silicones, petroleum, etc.\n"
                            "- what makes this product better or worse than alternatives\n"
                            "- what to look for when buying a greener option next time\n\n"
                            "Rules:\n"
                            "- Focus only on purchase-related advice\n"
                            "- No lifestyle tips\n"
                            "- Be specific to THIS product\n"
                            "- Do not invent data\n\n"
                            f"PRODUCT CONTEXT:\n"
                            f"Name: {r['name']}\n"
                            f"Category: {r['category']}\n"
                            f"Eco Score: {r['eco_score']} / 100\n"
                            f"Carbon: {r['total_carbon_kg']} kg CO₂e\n"
                            f"Water: {r['total_water_L']} L\n"
                            f"Energy: {r['total_energy_MJ']} MJ\n"
                            f"Waste Score: {r['total_waste_score']}\n"
                            f"Microplastics: {bool(int(r['microplastics']))}\n"
                            f"Silicones: {bool(int(r['silicones']))}\n"
                            f"Petroleum-derived: {bool(int(r['petroleum']))}"
                        ),
                    }
                ]

            # -----------------------------
            # DISPLAY CHAT
            # -----------------------------
            for msg in st.session_state.product_ai_messages[1:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # -----------------------------
            # USER QUESTION INPUT
            # -----------------------------
            product_question = st.chat_input(
                "Ask about ingredients, impacts, or better alternatives for this product…"
            )

            if product_question:
                st.session_state.product_ai_messages.append(
                    {"role": "user", "content": product_question}
                )

                with st.chat_message("user"):
                    st.markdown(product_question)

                # -----------------------------
                # AI RESPONSE
                # -----------------------------
                with st.chat_message("assistant"):
                    with st.spinner("Thinking about this product… 🌍"):
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            temperature=0.4,
                            messages=st.session_state.product_ai_messages,
                        )

                        ai_reply = response.choices[0].message.content
                        st.markdown(ai_reply)

                st.session_state.product_ai_messages.append(
                    {"role": "assistant", "content": ai_reply}
                )


            

# -------------------------
# CHATBOT PAGE
# -------------------------

elif st.session_state.page == "Chatbot":
    import streamlit as st
    from openai import OpenAI
    # -----------------------------
    # INIT OPENAI CLIENT
    # -----------------------------
    client = OpenAI(api_key=st.secrets["OpenAIKey"])
    # -----------------------------
    # PAGE SETUP
    # -----------------------------
    st.markdown('<h1 style="font-size: 48px; margin-bottom: 8px; color: #5D8A66;">Eco Assistant</h1>', unsafe_allow_html=True)
    st.caption("Ask me about sustainability, eco scores, or greener choices")
    # -----------------------------
    # CHAT MEMORY
    # -----------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful sustainability assistant focused ONLY on environmental and sustainability topics. "
                    "You ONLY answer questions related to:\n"
                    "- Sustainability and eco-friendly practices\n"
                    "- Environmental impact and climate change\n"
                    "- Green products and eco scores\n"
                    "- Waste reduction and recycling\n"
                    "- Carbon footprint and water usage\n"
                    "- Energy conservation and renewable energy\n"
                    "- Sustainable living and eco-conscious choices\n\n"
                    "If a user asks about topics unrelated to environment or sustainability "
                    "(like sports, entertainment, general knowledge, coding, etc.), "
                    "politely respond: 'I'm specifically designed to help with environmental and sustainability questions. "
                    "Could you ask me something related to eco-friendly living, green products, or environmental impact instead? 🌱'\n\n"
                    "For valid sustainability questions, give clear, practical, beginner-friendly answers. "
                    "Be concise and encouraging."
                )
            }
        ]
    # -----------------------------
    # DISPLAY CHAT
    # -----------------------------
    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # -----------------------------
    # USER INPUT
    # -----------------------------
    user_input = st.chat_input("Ask something eco-related...")
    if user_input:
        # show user message
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)
        # -----------------------------
        # OPENAI RESPONSE
        # -----------------------------
        with st.chat_message("assistant"):
            with st.spinner("Thinking... 🌍"):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    temperature=0.6
                )
                assistant_reply = response.choices[0].message.content
                st.markdown(assistant_reply)
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_reply}
        )






# -------------------------
# TOTAL IMPACT PAGE
# -------------------------
elif st.session_state.page == "Impact Dashboard":

    import pandas as pd
    import plotly.express as px
    from openai import OpenAI
    import streamlit as st

    # -----------------------------
    # NAV
    # -----------------------------
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.markdown('<h1 style="font-size: 48px; margin-bottom: 8px; color: #5D8A66;">🌍 Your Sustainability Impact</h1>', unsafe_allow_html=True)
    st.caption("A living story of how your choices shape the planet")

    # -----------------------------
    # OPENAI CLIENT
    # -----------------------------
    client = OpenAI(api_key=st.secrets["OpenAIKey"])

    def explain_with_ai(title, data, products):
        prompt = f"""
You are an AI sustainability analyst embedded inside a purchase-impact dashboard.

Context:
- The user logs products they buy
- Each product has an Eco Score, carbon, water, energy, and waste impact
- The dashboard only tracks PURCHASES (not lifestyle habits)

Graph title:
{title}

Products involved:
{products}

User data (aggregated from logged products):
{data}

Your tasks:

1. Explain what this graph reveals about the USER'S PURCHASE PATTERNS.
   - Mention specific impact categories (carbon, water, energy, waste)
   - Point out what is unusually high or low
   - Be concrete and data-driven (not generic)

2. Suggest 3 IMPROVEMENTS RELATED ONLY TO FUTURE PURCHASES.
   - Suggest product alternatives, material swaps, or category changes
   - Example: "Switch from X-type products to Y-type products"
   - You MAY suggest searching for lower-impact alternatives
   - DO NOT suggest lifestyle actions (no showers, lights, transport, etc.)

Rules:
- No generic eco tips
- No guilt or moralising
- Friendly, insightful, specific
- Assume a curious student user
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35
        )

        return response.choices[0].message.content

    # -----------------------------
    # REQUIRE HISTORY
    # -----------------------------
    if "impact_history" not in st.session_state or st.session_state.impact_history.empty:
        st.info("Analyse products to start building your impact story")
        st.stop()

    history = st.session_state.impact_history.copy()
    st.divider()

    # =============================
    # 🌱 SUMMARY METRICS (enhanced)
    # =============================
    avg_score = history["Eco Score"].mean()
    total_score = history["Eco Score"].sum()

    c1, c2, c3, c4 = st.columns(4)
    
    metrics_display = [
        ("Average Eco Score", f"{avg_score:.1f} / 100", "🌿"),
        ("Products Logged", str(len(history)), "📦"),
        ("High-Eco Choices", str((history["Eco Score"] >= 80).sum()), "⭐"),
        ("Total Eco Score", str(int(total_score)), "🏆")
    ]
    
    for col, (label, value, emoji) in zip([c1, c2, c3, c4], metrics_display):
        with col:
            col.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #5D8A6615 0%, #5D8A6608 100%);
                    border-radius: 16px;
                    padding: 20px;
                    text-align: center;
                    border: 2px solid #5D8A6625;
                    box-shadow: 0 4px 12px rgba(93, 138, 102, 0.1);
                ">
                    <div style="font-size: 2.2em; margin-bottom: 8px;">{emoji}</div>
                    <div style="color: #5D8A66; font-size: 2em; font-weight: 700; font-family: 'DM Serif Display', serif; margin-bottom: 4px;">{value}</div>
                    <div style="color: #3A4A3A; font-size: 0.85em; font-weight: 500;">{label}</div>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # =============================
    # 📈 ECOSCORE TREND (with custom colors)
    # =============================
    st.markdown("## Your EcoScore Journey")

    trend_fig = px.line(
        history.reset_index(),
        x=history.reset_index().index,
        y="Eco Score",
        markers=True,
        color_discrete_sequence=["#5D8A66"]
    )
    
    trend_fig.update_layout(
        plot_bgcolor='rgba(245, 241, 232, 0.3)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family="Plus Jakarta Sans",
        font_color="#3A4A3A"
    )

    st.plotly_chart(trend_fig, use_container_width=True)

    if st.button("🤖 Let AI explain this EcoScore trend"):
        with st.spinner("AI analysing your progress"):
            delta = history["Eco Score"].iloc[-1] - history["Eco Score"].iloc[0]

            summary = {
                "starting_score": float(history["Eco Score"].iloc[0]),
                "latest_score": float(history["Eco Score"].iloc[-1]),
                "average_score": round(avg_score, 1),
                "trend": "improving" if delta > 5 else "declining" if delta < -5 else "stable"
            }

            products = history["Product"].tolist()

            ai_text = explain_with_ai(
                "EcoScore trend over time",
                summary,
                products
            )

            st.info(ai_text.strip())

    st.divider()

    # =============================
    # 📊 IMPACT BREAKDOWN
    # =============================
    st.markdown("## What Impacts You the Most")

    impact_avg = history[
        ["Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"]
    ].mean().reset_index()

    impact_avg.columns = ["Impact Type", "Average Value"]

    impact_fig = px.bar(
        impact_avg,
        x="Impact Type",
        y="Average Value",
        color="Impact Type",
        color_discrete_sequence=["#5D8A66", "#7BA57E", "#9cb380", "#E8956B"]
    )
    
    impact_fig.update_layout(
        plot_bgcolor='rgba(245, 241, 232, 0.3)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family="Plus Jakarta Sans",
        font_color="#3A4A3A",
        showlegend=False
    )

    st.plotly_chart(impact_fig, use_container_width=True)

    if st.button("Let AI explain this impact breakdown"):
        with st.spinner("Understanding your impact"):
            impact_dict = dict(
                zip(impact_avg["Impact Type"], impact_avg["Average Value"])
            )

            products = history["Product"].unique().tolist()

            ai_text = explain_with_ai(
                "Average environmental impact by purchase",
                impact_dict,
                products
            )

            st.info(ai_text.strip())

    st.divider()

    # =============================
    # 🔄 PRODUCT COMPARISON (SAME CATEGORY ONLY)
    # =============================
    st.markdown("## Compare Products by Impact")
    st.caption("Compare any products from our database, not just your purchases")

    # Step 1 — Choose category first (from full database)
    compare_category = st.selectbox(
        "Select a category to compare within",
        sorted(summary_df["category"].unique())
    )

    # Step 2 — Show all products from that category in the full database
    category_products = summary_df[
        summary_df["category"] == compare_category
    ]["name"].unique()

    compare_products = st.multiselect(
        "Select products to compare",
        sorted(category_products),
        default=None
    )

    if len(compare_products) >= 2:
        # Get data from the full summary_df instead of history
        compare_df = summary_df[summary_df["name"].isin(compare_products)].copy()
        
        # Rename columns to match the impact display format
        compare_df = compare_df.rename(columns={
            "name": "Product",
            "total_carbon_kg": "Carbon (kg)",
            "total_water_L": "Water (L)",
            "total_energy_MJ": "Energy (MJ)",
            "total_waste_score": "Waste Score"
        })

        impact_cols = ["Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"]
        normalized = compare_df.copy()

        for col in impact_cols:
            max_val = normalized[col].max()
            normalized[col] = normalized[col] / max_val if max_val > 0 else 0

        stacked_fig = px.bar(
            normalized,
            x="Product",
            y=impact_cols,
            barmode="stack",
            color_discrete_sequence=["#5D8A66", "#7BA57E", "#9cb380", "#E8956B"]
        )
        
        stacked_fig.update_layout(
            plot_bgcolor='rgba(245, 241, 232, 0.3)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family="Plus Jakarta Sans",
            font_color="#3A4A3A"
        )

        st.plotly_chart(stacked_fig, use_container_width=True)

        # AI explanation
        if st.button("Let AI explain this product comparison"):
            with st.spinner("Comparing smarter choices"):
                comparison_summary = (
                    compare_df.groupby("Product")[impact_cols]
                    .mean()
                    .to_dict()
                )

                ai_text = explain_with_ai(
                    "Product impact comparison",
                    comparison_summary,
                    compare_products
                )

                st.info(ai_text.strip())

    else:
        st.info("Select at least two products from the same category to compare 🌱")

    st.divider()



    # =============================
    # 📜 HISTORY TABLE
    # =============================
    st.markdown("## Your Impact Log")
    st.dataframe(history[::-1], use_container_width=True)

    if st.button("Clear Impact History"):
        st.session_state.impact_history = st.session_state.impact_history.iloc[0:0]

        if "logged_keys" in st.session_state:
            st.session_state.logged_keys.clear()

        st.success("Impact history cleared 🌱")
        st.rerun()


# -------------------------
# YOUR NEXT STEPS PAGE
# -------------------------
elif st.session_state.page == "NextSteps":

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.markdown('<h1 style="font-size: 48px; margin-bottom: 8px; color: #5D8A66;">Your Next Steps</h1>', unsafe_allow_html=True)
    st.caption("Clear, practical actions to reduce your impact")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================
    # SECTION 1 — ECO ALTERNATIVES
    # ============================

    st.markdown('<h2 style="font-size: 32px; margin-bottom: 18px; color: #5D8A66;">Switch to Better Alternatives</h2>', unsafe_allow_html=True)

    category = st.selectbox(
        "Select a product category",
        [
            "",
            "Shampoo",
            "Cream",
            "Sunscreen",
            "Body Wash",
            "Soft Drink",
            "Instant Noodles",
            "Chips",
            "Chocolate",
            "Biscuits",
            "Candy",
            "Snack"
        ]
    )


    BEST_SUBS = {
    
        # ----------------
        # PERSONAL CARE
        # ----------------
        "Shampoo": [
            "Ethique Shampoo Bar",
            "Earth Rhythm Shampoo Bar",
            "Bare Anatomy Concentrated Shampoo"
        ],
    
        "Cream": [
            "Minimalist Marula Oil Moisturizer",
            "Earth Rhythm Phyto Clear Moisturizer",
            "Plum Green Tea Moisturizer"
        ],
    
        "Sunscreen": [
            "Raw Beauty Wellness Sunscreen Stick",
            "Minimalist SPF 50 (50g)",
            "Dot & Key Sunscreen Stick"
        ],
    
        "Body Wash": [
            "Ethique Solid Body Wash Bar",
            "Earth Rhythm Body Wash Bar",
            "Plum BodyLovin Body Wash Bar"
        ],
    
        # ----------------
        # FOOD & DRINK
        # ----------------
        "Soft Drink": [
            "Returnable glass bottle cola",
            "Powdered drink concentrates",
            "Sparkling water in aluminum can"
        ],
    
        "Instant Noodles": [
            "Whole wheat noodles in paper packaging",
            "Rice noodles in cardboard box",
            "Fresh noodles from local brand"
        ],
    
        "Chips": [
            "Baked chips",
            "Roasted makhana",
            "Popcorn in paper packaging"
        ],
    
        "Chocolate": [
            "Dark chocolate (70%+ cocoa)",
            "Chocolate in paper wrapper",
            "Fair-trade chocolate bar"
        ],
    
        "Biscuits": [
            "Oat biscuits in paper packaging",
            "Digestive biscuits cardboard box",
            "Local bakery cookies"
        ],
    
        "Candy": [
            "Loose candies from bulk store",
            "Jaggery-based sweets",
            "Fruit leathers"
        ],
    
        "Snack": [
            "Roasted chana",
            "Trail mix in paper pouch",
            "Roasted peanuts"
        ]
    }


    if category != "":
        c1, c2, c3 = st.columns(3)

        for i, prod in enumerate(BEST_SUBS[category]):
            with [c1, c2, c3][i]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #5D8A66 0%, #4d7554 100%);
                    border-radius:20px;
                    padding:28px 22px;
                    text-align:center;
                    box-shadow:0 8px 24px rgba(93, 138, 102, 0.3);
                    height:190px;
                    display:flex;
                    flex-direction:column;
                    justify-content:center;
                    transition: transform 0.3s ease;
                " onmouseover="this.style.transform='translateY(-8px)';" onmouseout="this.style.transform='translateY(0)';">
                    <h4 style="color:#F5F1E8; margin-bottom:14px; font-size: 1.15em; font-weight: 700; line-height: 1.3;">{prod}</h4>
                    <p style="color:rgba(245,241,232,0.85); font-size:15px; line-height: 1.5;">
                    Lower packaging & ingredient impact
                    </p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # =================================
    # SECTION 2 — IF YOU ALREADY BOUGHT
    # =================================

    st.markdown('<h2 style="font-size: 32px; margin-bottom: 18px; color: #5D8A66;">If You Already Bought a Regular Product</h2>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    boxes_content = [
        {
            "title": "Use Intentionally",
            "items": [
                "Use only the recommended amount",
                "Avoid unnecessary double cleansing",
                "Don't stockpile backups",
                "Finish before opening a new product"
            ]
        },
        {
            "title": "Extend Product Life",
            "items": [
                "Store away from heat & sunlight",
                "Use pumps/spatulas to avoid contamination",
                "Choose refills next time",
                "Share unopened extras"
            ]
        },
        {
            "title": "Dispose Responsibly",
            "items": [
                "Empty completely",
                "Rinse packaging",
                "Check local recycling rules",
                "Reuse containers for storage"
            ]
        }
    ]
    
    for col, content in zip([c1, c2, c3], boxes_content):
        with col:
            items_html = "".join([f"<li style='margin-bottom: 10px;'>{item}</li>" for item in content['items']])
            col.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #5D8A6618 0%, #5D8A6610 100%);
                border-radius:18px;
                padding:28px 24px;
                height:320px;
                box-shadow:0 6px 20px rgba(93, 138, 102, 0.15);
                border: 2px solid #5D8A6630;
            ">
                <h4 style="color:#3A4A3A; font-size: 1.3em; margin-bottom: 16px; font-weight: 700;">{content['title']}</h4>
                <ul style="color:#3A4A3A; line-height:1.7; font-size: 0.95em; padding-left: 20px;">
                    {items_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ============================
    # SECTION 3 — DAILY MICRO HABITS
    # ============================

    st.markdown('<h2 style="font-size: 32px; margin-bottom: 18px; color: #5D8A66;">Everyday Micro-Habits</h2>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    habits = [
        "Choose refill packs",
        "Prefer bars over liquids",
        "Buy only what you need",
        "Pick paper or aluminum packaging",
        "Carry your own bottle",
        "Support eco-certified brands"
    ]
    
    for i, h in enumerate(habits):
        with [c1, c2, c3][i % 3]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #7BA57E 0%, #6b9570 100%);
                color:#F5F1E8;
                border-radius:16px;
                padding:20px 18px;
                text-align:center;
                margin-bottom:16px;
                box-shadow:0 6px 16px rgba(123, 165, 126, 0.25);
                font-weight:600;
                font-size: 1.05em;
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 8px 24px rgba(123, 165, 126, 0.35)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 6px 16px rgba(123, 165, 126, 0.25)';">
                {h}
            </div>
            """, unsafe_allow_html=True)
