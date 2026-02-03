
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="EcoLens", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1rem !important; }

/* Sticky header box */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 999;
  background: #0e1117;   /* dark theme background */
  padding: 0.5rem 0 0.75rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

GREENER_ALTERNATIVES = {
    "Cream": [
        {
            "name": "Minimalist Marula Oil Moisturizer",
            "reason": "Uses an aluminum tube instead of a plastic jar, reducing total plastic waste."
        },
        {
            "name": "Earth Rhythm Phyto Clear Moisturizer",
            "reason": "Packaged in a reusable glass jar with lower waste impact than PET."
        },
        {
            "name": "Plum Green Tea Moisturizer",
            "reason": "Smaller packaging size means less total material used."
        }
    ],
    "Body Wash": [
        {
            "name": "Ethique Solid Body Wash Bar",
            "reason": "Eliminates plastic bottles entirely by using a solid bar format."
        },
        {
            "name": "Earth Rhythm Body Wash Bar",
            "reason": "Zero plastic packaging results in near-zero packaging emissions."
        }
    ],
    "Sunscreen": [
        {
            "name": "Raw Beauty Wellness Sunscreen Stick",
            "reason": "Paper-based packaging avoids high-energy aluminum and plastic bottles."
        },
        {
            "name": "Dot & Key Sunscreen Stick",
            "reason": "Compact solid format reduces packaging weight significantly."
        },
        {
            "name": "Minimalist SPF 50 (50g)",
            "reason": "Smaller tube uses far less material than large sunscreen bottles."
        }
    ],
    "L'Oreal Shampoo 300ml": [
        {
            "name": "Ethique Shampoo Bar",
            "reason": "Solid shampoo bar completely removes the need for plastic bottles."
        },
        {
            "name": "Earth Rhythm Shampoo Bar",
            "reason": "Lower water and carbon footprint due to zero liquid packaging."
        },
        {
            "name": "Bare Anatomy Concentrated Shampoo",
            "reason": "Concentrated formula requires a smaller bottle."
        }
    ]
}


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

# =============================
# MATERIAL IMPACT DICTIONARY
# =============================
material_impact_dict = {}
for _, row in materials_df.iterrows():
    material_impact_dict[row['material']] = {
        'carbon': row['carbon_kg_per_kg'],
        'water': row['water_L_per_kg'],
        'energy': row['energy_MJ_per_kg'],
        'waste': row['waste_score']  # 1–5 (higher = worse)
    }

# =============================
# INITIALIZE RESULT COLUMNS
# =============================
products_df['total_carbon_kg'] = 0.0
products_df['total_water_L'] = 0.0
products_df['total_energy_MJ'] = 0.0
products_df['total_waste_score'] = 0.0

# =============================
# COMPUTE ENVIRONMENTAL IMPACT
# =============================
for i, product in products_df.iterrows():
    total_carbon = 0.0
    total_water = 0.0
    total_energy = 0.0
    waste_scores = []

    for j in range(1, 4):
        material = product.get(f'material_{j}')
        weight_g = product.get(f'weight_{j}_g')

        if pd.isna(material) or pd.isna(weight_g):
            continue

        impact = material_impact_dict.get(material)
        if not impact:
            continue

        weight_kg = weight_g / 1000

        total_carbon += weight_kg * impact['carbon']
        total_water += weight_kg * impact['water']
        total_energy += weight_kg * impact['energy']

        # Waste is a material-type penalty (not mass-scaled)
        waste_scores.append(impact['waste'])

    products_df.at[i, 'total_carbon_kg'] = total_carbon
    products_df.at[i, 'total_water_L'] = total_water
    products_df.at[i, 'total_energy_MJ'] = total_energy
    products_df.at[i, 'total_waste_score'] = np.mean(waste_scores) if waste_scores else 0

# =============================
# NORMALIZATION CAPS (FIXED)
# =============================
CARBON_CAP = 0.5   # kg CO₂e
WATER_CAP = 10.0   # liters
ENERGY_CAP = 20.0  # MJ
WASTE_CAP = 5.0    # max material waste score

products_df['carbon_norm'] = (products_df['total_carbon_kg'] / CARBON_CAP).clip(0, 1)
products_df['water_norm'] = (products_df['total_water_L'] / WATER_CAP).clip(0, 1)
products_df['energy_norm'] = (products_df['total_energy_MJ'] / ENERGY_CAP).clip(0, 1)
products_df['waste_norm'] = (products_df['total_waste_score'] / WASTE_CAP).clip(0, 1)

# =============================
# FINAL ECOSCORE (0–100)
# =============================
products_df['eco_score'] = (
    (1 - products_df['carbon_norm']) * 0.35 +
    (1 - products_df['water_norm']) * 0.25 +
    (1 - products_df['energy_norm']) * 0.25 +
    (1 - products_df['waste_norm']) * 0.15
) * 100

products_df['eco_score'] = products_df['eco_score'].round(1)

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
    <h1 style="text-align:center; font-size:72px; margin:0;">
        🌱 EcoLens
    </h1>
    <p style="text-align:center; font-size:18px; opacity:0.85; margin-top:6px; margin-bottom:14px;">
        Make smarter, sustainable buying decisions
    </p>
    """,
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    st.button("🌿 GreenScore", use_container_width=True, on_click=go, args=("GreenScore",))
with c2:
    st.button("🤖 AI Chatbot", use_container_width=True, on_click=go, args=("Chatbot",))
with c3:
    st.button("🌏Total Impact", use_container_width=True, on_click=go, args=("Impact",))
with c4:
    st.button("ℹ️ About", use_container_width=True, on_click=go, args=("About",))

st.markdown("</div>", unsafe_allow_html=True)
st.write("")  # spacer

# -------------------------
# HOME
# -------------------------
if st.session_state.page == "Home":

    left, right = st.columns([1.2, 1.8], gap="large")

    with left:
        st.markdown("""
            <div style="height:420px; overflow:hidden; border-radius:12px;">
                <img src="https://images.openai.com/static-rsc-3/L_9-L2VXhvFW5NZZvI6VLjA1QxHDiDeV5vyXsgKqM2ycJVtMFds_HEsJfhXYdziNs9fdDa4f0k4koZsaN3gehTxDddohscLt0wYAfwvMxRE?purpose=fullsize"
                     style="width:100%; height:100%; object-fit:cover;">
            </div>
        """, unsafe_allow_html=True)
    
    with right:
        st.markdown(
            """<div style="height:420px; display:flex; flex-direction:column; justify-content:center;">
    <h2 style="font-size:42px; margin-bottom:18px;">What is EcoLens?</h2>
    <p style="font-size:20px; line-height:1.7; max-width:680px;">
    EcoLens helps eco-conscious shoppers identify truly sustainable products by providing clear insights into a product’s sustainability impact.
    Scan a product, detect greenwashing, and get a clear <b>Green Score</b> with reasons.
    </p>
    </div>""",
            unsafe_allow_html=True
        )

    st.header("🚨 The Problem")
    st.write("Sustainability labels are vague and poorly regulated, so consumers often rely on marketing language instead of real data. Many of these claims are misleading, allowing greenwashing to go unnoticed. Because people lack the time and expertise to properly assess environmental impact, they make well-intentioned but poor choices. Additionally, there is no standardized way to verify eco-claims, and most existing apps reduce sustainability to simple green or red labels, hiding the real environmental costs of everyday products. As a result, people want to buy more environmentally friendly products but struggle to know which ones truly are.")
    

    st.header("✨ Key Features")
    f1, f2 = st.columns(2)
    with f1:
        st.subheader("🌿 GreenScore")
        st.write("- Barcode scan\n- Score + explanation\n- Better alternatives")
    with f2:
        st.subheader("🤖 AI Chatbot")
        st.write("- Ingredient explanations\n- Claim checks\n- Eco tips")

# -------------------------
# GREEN SCORE PAGE
# -------------------------
elif st.session_state.page == "GreenScore":
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌿 GreenScore")

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

        category = result.iloc[0]['category']

        st.subheader("🌿 Greener Alternatives")

        if category in GREENER_ALTERNATIVES:
            for alt in GREENER_ALTERNATIVES[category]:
                st.markdown(
                    f"""
                    **{alt['name']}**  
                    *Why it’s greener:* {alt['reason']}
                    """
                )
        else:
            st.write("No greener alternatives available for this category.")

# -------------------------
# CHATBOT PAGE
# -------------------------
import requests
elif st.session_state.page == "Chatbot":
 

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🤖 AI Chatbot")

    st.write("Ask a question about sustainability, ingredients, and alternatives.")

    # --- Hugging Face API setup (FREE) ---
    API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
    HF_API_KEY = "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"
    HEADERS = {
    "Authorization": f"Bearer {st.secrets['HF_API_KEY']}"
    }

    # Store chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_q = st.text_input("Your question")

    if st.button("Ask") and user_q.strip() != "":
        with st.spinner("Thinking..."):
            payload = {
                "inputs": f"Answer clearly and simply:\n{user_q}"
            }

            response = requests.post(API_URL, headers=HEADERS, json=payload)

            if response.status_code == 200:
                ai_reply = response.json()[0]["generated_text"]
            else:
                ai_reply = "⚠️ AI service unavailable. Try again."

        st.session_state.chat_history.append(("You", user_q))
        st.session_state.chat_history.append(("AI", ai_reply))

    # Display conversation
    for speaker, msg in st.session_state.chat_history:
        if speaker == "You":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 AI:** {msg}")

# -------------------------
# TOTAL IMPACT PAGE
# -------------------------
elif st.session_state.page == "Impact":
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌏Total Impact")

    st.write("Find out the environmental impact of your choices, and discover ways to increase your eco-friendliness")
# -------------------------
# ABOUT PAGE
# -------------------------
elif st.session_state.page == "About":
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("ℹ️ About")

    st.write("Built by **The Quantum Crew** for TISB Hacks.")

    st.subheader("👥 Team")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### Pihu Gupta")
        st.caption("Backend & APIs")

    with col2:
        st.markdown("### Saanvi Khetan")
        st.caption("ML & Scoring")

    with col3:
        st.markdown("### Sinita Ray")
        st.caption("UX & Frontend")

    with col4:
        st.markdown("### Nivedha Sundar")
        st.caption("Product & Pitch")


    
