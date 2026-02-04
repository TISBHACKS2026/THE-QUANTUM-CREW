
import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import requests
def get_greener_alternatives(current_product_name, summary_df, max_alternatives=5):
    """
    Find greener alternatives from the actual product database.
    Returns products in the same category with better eco scores.
    """
    # Get current product details
    current = summary_df[summary_df['name'] == current_product_name]
    if current.empty:
        return []
    
    current_row = current.iloc[0]
    current_category = current_row['category']
    current_score = current_row['eco_score']
    
    # Find alternatives: same category, better score, exclude current product
    alternatives = summary_df[
        (summary_df['category'] == current_category) &
        (summary_df['eco_score'] > current_score) &
        (summary_df['name'] != current_product_name)
    ].copy()
    
    # Sort by eco score (best first)
    alternatives = alternatives.sort_values('eco_score', ascending=False)
    
    # Take top N
    alternatives = alternatives.head(max_alternatives)
    
    # Calculate improvement metrics for each alternative
    results = []
    for _, alt in alternatives.iterrows():
        carbon_reduction = ((current_row['total_carbon_kg'] - alt['total_carbon_kg']) / current_row['total_carbon_kg'] * 100) if current_row['total_carbon_kg'] > 0 else 0
        water_reduction = ((current_row['total_water_L'] - alt['total_water_L']) / current_row['total_water_L'] * 100) if current_row['total_water_L'] > 0 else 0
        energy_reduction = ((current_row['total_energy_MJ'] - alt['total_energy_MJ']) / current_row['total_energy_MJ'] * 100) if current_row['total_energy_MJ'] > 0 else 0
        
        # Find the biggest improvement
        improvements = []
        if carbon_reduction > 5:
            improvements.append(f"{carbon_reduction:.0f}% less carbon")
        if water_reduction > 5:
            improvements.append(f"{water_reduction:.0f}% less water")
        if energy_reduction > 5:
            improvements.append(f"{energy_reduction:.0f}% less energy")
        
        if not improvements:
            improvements.append("Better overall eco score")
        
        results.append({
            'name': alt['name'],
            'eco_score': alt['eco_score'],
            'improvement': improvements[0],  # Show the best improvement
            'score_diff': alt['eco_score'] - current_score
        })
    
    return results
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
    "Shampoo": [
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

NEW_FLAG_COLS = [
    "microplastics",
    "palm_oil",
    "parabens",
    "sulfates",
    "recyclable_packaging",
    "eco_certified",
]

for c in NEW_FLAG_COLS:
    if c not in products_df.columns:
        products_df[c] = 0

# Make sure flags are 0/1 ints (handles blanks/NaN)
products_df[NEW_FLAG_COLS] = products_df[NEW_FLAG_COLS].fillna(0).astype(int)

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
# PACKAGING ECOSCORE (0–100)
# =============================
products_df['packaging_score'] = (
    (1 - products_df['carbon_norm']) * 0.35 +
    (1 - products_df['water_norm']) * 0.25 +
    (1 - products_df['energy_norm']) * 0.25 +
    (1 - products_df['waste_norm']) * 0.15
) * 100

products_df['packaging_score'] = products_df['packaging_score'].round(1)

# =============================
# INGREDIENT SCORE (0–100) using 0/1 flags
# =============================
# penalties (tweak anytime; these are hackathon-friendly)
products_df['ingredient_score'] = 100 - (
    30 * products_df['microplastics'] +
    20 * products_df['palm_oil'] +
    10 * products_df['parabens'] +
    10 * products_df['sulfates']
)

products_df['ingredient_score'] = products_df['ingredient_score'].clip(0, 100).round(1)

# =============================
# BONUS SCORE (0–100)
# - small trust/circularity boost
# =============================
# simple: if recyclable or certified -> better bonus
products_df['bonus_score'] = 60 + (
    20 * products_df['recyclable_packaging'] +
    20 * products_df['eco_certified']
)
products_df['bonus_score'] = products_df['bonus_score'].clip(0, 100).round(1)

# =============================
# FINAL ECOSCORE (0–100)
# Breakup: 50% packaging, 40% ingredients, 10% bonus
# =============================
products_df['eco_score'] = (
    0.50 * products_df['packaging_score'] +
    0.40 * products_df['ingredient_score'] +
    0.10 * products_df['bonus_score']
).round(1)

# =============================
# FINAL SUMMARY TABLE (REQUIRED FOR GREEN SCORE PAGE)
# =============================
summary_df = products_df[[
    'name',
    'category',
    'total_carbon_kg',
    'total_water_L',
    'total_energy_MJ',
    'total_waste_score',
    'packaging_score',
    'ingredient_score',
    'bonus_score',
    'eco_score'
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
    <h1 style="text-align:center; font-size:72px; margin:0;">
        🌱 EcoLens
    </h1>
    <p style="text-align:center; font-size:18px; opacity:0.85; margin-top:6px; margin-bottom:14px;">
        Make smarter, sustainable buying decisions
    </p>
    """,
    unsafe_allow_html=True
)

c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
with c1:
    st.button("🌿 GreenScore", use_container_width=True, on_click=go, args=("GreenScore",))
with c2:
    st.button("🤖 AI Chatbot", use_container_width=True, on_click=go, args=("Chatbot",))
with c3:
    st.button("🌏Impact Dashboard", use_container_width=True, on_click=go, args=("Impact Dashboard",))
with c4:
    st.button("ℹ️ About", use_container_width=True, on_click=go, args=("About",))
with c5:
    st.button("🧭 Your Next Steps", use_container_width=True, on_click=go, args=("NextSteps",))


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
    <h2 style="font-size:35px; margin-bottom:18px;">What is EcoLens?</h2>
    <p style="font-size:20px; line-height:1.7; max-width:600px;">
    EcoLens helps people understand the real environmental impact of the products they buy, so they can make more informed and sustainable choices.
    </p>
    </div>""",
            unsafe_allow_html=True
        )

    st.header("The Hidden Cost of Everyday Products")
    st.write("Every year, the world produces over 400 million tonnes of plastic waste, and nearly half of this comes from single-use packaging like bottles, bags, wrappers, and cartons. Only around 9% of all plastic ever produced has been recycled, while the rest ends up in landfills, incinerators, or in the environment.")
    st.write("Packaging alone can account for 20–40% of a product’s total environmental footprint, yet this hidden cost is rarely visible when we shop. Most of the time, consumers only see branding and marketing claims, not the true environmental impact behind a product.")

    st.header("The Problem")
    st.write("Sustainability labels are vague and poorly regulated, so consumers often rely on marketing language instead of real data. Many of these claims are misleading, allowing greenwashing to go unnoticed. Because people lack the time and expertise to properly assess environmental impact, they make well-intentioned but poor choices. Additionally, there is no standardized way to verify eco-claims, and most existing apps reduce sustainability to simple green or red labels, hiding the real environmental costs of everyday products.")

    st.header("Small Choices, Big Impact")
    st.write("A single purchase may feel insignificant, but when millions of people repeat small decisions every day, the impact becomes massive. If just 1 million people replaced one single-use plastic bottle per day, over 7,000 tonnes of plastic waste could be prevented each year. EcoLens makes these invisible impacts visible, so your everyday choices can become part of a much bigger change.")

    st.header("✨ Key Features")

    components.html("""
<div style="
    background:#3f5a4d;
    border-radius:18px;
    padding:44px 38px;
    margin-top:18px;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
">
  <div style="display:flex; gap:34px; align-items:center;">

    <div style="flex:1.2;">
      <h2 style="margin:0 0 14px 0; font-size:38px; color:white;">
        🌿 GreenScore Tracker
      </h2>

      <p style="margin:0 0 14px 0; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
        Scan personal-care products and get a transparent sustainability score with clear reasons.
      </p>

      <ul style="margin:0; padding-left:20px; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
        <li>Barcode scan / product lookup</li>
        <li>Score breakdown (ingredients, packaging, claims)</li>
        <li>Greenwashing flags + simple explanations</li>
        <li>Better alternatives for your purpose</li>
      </ul>
    </div>

    <div style="flex:1; display:flex; justify-content:flex-end;">
      <div style="
          width:520px;
          height:320px;
          border-radius:16px;
          overflow:hidden;
          box-shadow: 0 10px 30px rgba(0,0,0,0.25);
          background: rgba(255,255,255,0.06);
      ">
        <img src="https://www.iberdrola.com/documents/20125/40513/huella-de-carbono-746x419.jpg/f61f98a2-7c51-27f9-31d2-41b1dafe6bf7?t=1738248418273"
             style="width:100%; height:100%; object-fit:cover;">
      </div>
    </div>

  </div>
</div>
""", height=420)


    
    #-------------------------
    # AI Chatbot
    #-------------------------

    components.html("""
    <div style="
        background:#15597e;   /* blueish */
        border-radius:18px;
        padding:44px 38px;
        margin-top:22px;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
    ">
      <div style="display:flex; gap:34px; align-items:center;">
    
        <!-- LEFT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-start;">
          <div style="
              width:520px;
              height:320px;
              border-radius:16px;
              overflow:hidden;
              box-shadow: 0 10px 30px rgba(0,0,0,0.30);
              background: rgba(255,255,255,0.06);
          ">
            <img src="https://beetroot.co/wp-content/uploads/sites/2/2024/12/Cover_AI-chatbots-in-GreenTech.png"
                 style="width:100%; height:100%; object-fit:cover;">
          </div>
        </div>
    
        <!-- RIGHT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 14px 0; font-size:38px; color:white;">
            🤖 AI Chatbot
          </h2>
    
          <p style="margin:0 0 14px 0; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            Ask questions in plain English and get smart, personalized sustainability advice instantly.
          </p>
    
          <ul style="margin:0; padding-left:20px; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            <li>Ask about ingredients and claims</li>
            <li>Detect greenwashing language</li>
            <li>Get product recommendations</li>
            <li>Tips for safer / sustainable swaps</li>
          </ul>
        </div>
    
      </div>
    </div>
    """, height=420)

    #---------------------
    # Impact Score
    #---------------------
  
    components.html("""
    <div style="
        background:#1c3b2b;   /* forest green */
        border-radius:18px;
        padding:44px 38px;
        margin-top:22px;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
    ">
      <div style="display:flex; gap:34px; align-items:center;">
    
        <!-- LEFT TEXT -->
        <div style="flex:1.2;">
          <h2 style="margin:0 0 14px 0; font-size:38px; color:white;">
            🌲 Impact Score
          </h2>
    
          <p style="margin:0 0 14px 0; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            See the real environmental impact of every purchase in clear, easy-to-understand metrics.
          </p>
    
          <ul style="margin:0; padding-left:20px; font-size:18px; line-height:1.7; color:rgba(255,255,255,0.92);">
            <li>Track carbon footprint savings</li>
            <li>Water & plastic reduction estimates</li>
            <li>Compare products side-by-side</li>
            <li>Visualize your eco progress over time</li>
          </ul>
        </div>
    
        <!-- RIGHT IMAGE -->
        <div style="flex:1; display:flex; justify-content:flex-end;">
          <div style="
              width:520px;
              height:320px;
              border-radius:16px;
              overflow:hidden;
              box-shadow: 0 10px 30px rgba(0,0,0,0.30);
              background: rgba(255,255,255,0.06);
          ">
            <img src="https://greenscoreapp.com/wp-content/uploads/2024/09/Empowering-Sustainability-Through-Innovation-image2-Green-Score.webp"
                 style="width:100%; height:100%; object-fit:cover;">
          </div>
        </div>
    
      </div>
    </div>
    """, height=420)

# -------------------------
# GREEN SCORE PAGE
# -------------------------
elif st.session_state.page == "GreenScore":
    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌿 GreenScore")    
    # Check if user clicked an alternative product
    if "impact_history" not in st.session_state:
        st.session_state.impact_history = pd.DataFrame(columns=[
            "Product", "Category", "Eco Score",
            "Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"
        ])

    if "logged_keys" not in st.session_state:
        st.session_state.logged_keys = set()
    if 'selected_alternative' in st.session_state:
        product_input = st.session_state['selected_alternative']
        del st.session_state['selected_alternative']  # Clear it after using
    else:
        product_input = None

    # -----------------------------
    # Step 7: USER INPUT + DISPLAY
    # -----------------------------
#If coming from alternative click, pre-select i
    if product_input:
        default_index = list(sorted(summary_df['name'].unique())).index(product_input)
    else:
        default_index = None
    
    product_input = st.selectbox(
        "🔍 Search for a product",
        options=sorted(summary_df['name'].unique()),
        index=default_index,
        placeholder="Start typing to search..."
    )
    if product_input:
        result = summary_df[summary_df['name'] == product_input]
        st.session_state.selected_product = product_input
    
        if result.empty:
            st.error("❌ Product not found in database.")
        else:
            r = result.iloc[0]
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
    
            st.divider()
            
            # ---------- ECO SCORE ----------
            st.markdown("### 🌿 Eco Score")
            
            # Create a more visually appealing score display
            score_col1, score_col2 = st.columns([2, 3])
            
            with score_col1:
                # Large score display
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 20px;
                        padding: 30px;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    ">
                        <h1 style="color: white; margin: 0; font-size: 4em;">{r['eco_score']}</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 1.1em;">out of 100</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with score_col2:
                # Score interpretation
                if r['eco_score'] >= 80:
                    badge_color = "#10b981"
                    badge_text = "Excellent"
                    emoji = "🌟"
                elif r['eco_score'] >= 60:
                    badge_color = "#3b82f6"
                    badge_text = "Good"
                    emoji = "👍"
                elif r['eco_score'] >= 40:
                    badge_color = "#f59e0b"
                    badge_text = "Moderate"
                    emoji = "⚠️"
                else:
                    badge_color = "#ef4444"
                    badge_text = "Needs Improvement"
                    emoji = "❗"
                
                st.markdown(f"""
                    <div style="padding: 20px 0;">
                        <div style="
                            background-color: {badge_color};
                            color: white;
                            padding: 15px 25px;
                            border-radius: 12px;
                            display: inline-block;
                            font-size: 1.3em;
                            font-weight: bold;
                            margin-bottom: 15px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            {emoji} {badge_text}
                        </div>
                        <p style="color: #6b7280; margin-top: 10px; line-height: 1.6;">
                            This score reflects the overall environmental impact across carbon, water, energy, and waste metrics.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Progress bar with custom styling
            st.markdown(f"""
                <div style="margin: 20px 0;">
                    <div style="
                        background-color: #e5e7eb;
                        border-radius: 10px;
                        height: 12px;
                        overflow: hidden;
                    ">
                        <div style="
                            background: linear-gradient(90deg, #10b981 0%, #3b82f6 50%, #f59e0b 100%);
                            width: {r['eco_score']}%;
                            height: 100%;
                            border-radius: 10px;
                            transition: width 0.5s ease;
                        "></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
            st.divider()
    
            # ---------- METRICS ----------
            st.markdown("### 📊 Environmental Impact Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
    
            with col1:
                st.markdown(f"""
                    <div style="
                        background-color: #fef3c7;
                        border-left: 4px solid #f59e0b;
                        border-radius: 8px;
                        padding: 20px 15px;
                        text-align: center;
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">🌫</div>
                        <div style="color: #78716c; font-size: 0.85em; margin-bottom: 5px;">Carbon Footprint</div>
                        <div style="color: #292524; font-size: 1.5em; font-weight: bold;">{r['total_carbon_kg']}</div>
                        <div style="color: #78716c; font-size: 0.75em;">kg CO₂e</div>
                    </div>
                """, unsafe_allow_html=True)
    
            with col2:
                st.markdown(f"""
                    <div style="
                        background-color: #dbeafe;
                        border-left: 4px solid #3b82f6;
                        border-radius: 8px;
                        padding: 20px 15px;
                        text-align: center;
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">💧</div>
                        <div style="color: #475569; font-size: 0.85em; margin-bottom: 5px;">Water Usage</div>
                        <div style="color: #1e293b; font-size: 1.5em; font-weight: bold;">{r['total_water_L']}</div>
                        <div style="color: #475569; font-size: 0.75em;">Liters</div>
                    </div>
                """, unsafe_allow_html=True)
    
            with col3:
                st.markdown(f"""
                    <div style="
                        background-color: #fef9c3;
                        border-left: 4px solid #eab308;
                        border-radius: 8px;
                        padding: 20px 15px;
                        text-align: center;
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">⚡</div>
                        <div style="color: #78716c; font-size: 0.85em; margin-bottom: 5px;">Energy Use</div>
                        <div style="color: #292524; font-size: 1.5em; font-weight: bold;">{r['total_energy_MJ']}</div>
                        <div style="color: #78716c; font-size: 0.75em;">MJ</div>
                    </div>
                """, unsafe_allow_html=True)
    
            with col4:
                st.markdown(f"""
                    <div style="
                        background-color: #e0e7ff;
                        border-left: 4px solid #6366f1;
                        border-radius: 8px;
                        padding: 20px 15px;
                        text-align: center;
                    ">
                        <div style="font-size: 2em; margin-bottom: 10px;">🗑</div>
                        <div style="color: #475569; font-size: 0.85em; margin-bottom: 5px;">Waste Impact</div>
                        <div style="color: #1e293b; font-size: 1.5em; font-weight: bold;">{r['total_waste_score']}</div>
                        <div style="color: #475569; font-size: 0.75em;">Score</div>
                    </div>
                """, unsafe_allow_html=True)
    
            st.markdown("<br>", unsafe_allow_html=True)
    
            # ---------- OPTIONAL DETAILS ----------
            with st.expander("📊 View detailed data"):
                st.dataframe(result, use_container_width=True)

            # ✅ FIX 1: category must be INSIDE else block# =============================
            # GREENER ALTERNATIVES
            # =============================
            st.subheader("🌿 Greener Alternatives")
            st.caption("Click any product to view its full eco score")
            
            alternatives = get_greener_alternatives(product_input, summary_df, max_alternatives=5)
            
            if alternatives:
                for alt in alternatives:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(
                            f"""
                            <div style="
                                background: linear-gradient(135deg, #E8F5E9 0%, #F5F1E8 100%);
                                border-left: 4px solid #66BB6A;
                                border-radius: 12px;
                                padding: 16px;
                                margin-bottom: 12px;
                                cursor: pointer;
                                transition: all 0.3s ease;
                                box-shadow: 0 2px 6px rgba(46, 125, 50, 0.1);
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="color:#2E7D32; font-size:17px;">{alt['name']}</strong><br>
                                        <span style="color:#66BB6A; font-size:14px;">✨ {alt['improvement']}</span>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color:#2E7D32; font-size:24px; font-weight:700;">{alt['eco_score']}</div>
                                        <div style="color:#616161; font-size:12px;">+{alt['score_diff']:.1f} points</div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        if st.button("View →", key=f"view_{alt['name']}", use_container_width=True):
                            st.session_state['selected_alternative'] = alt['name']
                            st.rerun()
            else:
                st.info("🎉 Great choice! This is already one of the greenest options in its category.")
            

# -------------------------
# CHATBOT PAGE
# -------------------------

elif st.session_state.page == "Chatbot":
  

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🤖 AI Chatbot")
    st.write("Ask a question about sustainability, ingredients, and alternatives.")

    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    HEADERS = {
        "Authorization": f"Bearer {st.secrets['HF_API_KEY']}"
    }

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_q = st.text_input("Your question")

    if st.button("Ask") and user_q.strip():
        with st.spinner("Thinking..."):
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={"inputs": f"Answer clearly:\n{user_q}"}
            )

            if response.status_code == 200:
                ai_reply = response.json()[0]["generated_text"]
            else:
                ai_reply = "⚠️ AI service unavailable. Try again."

        st.session_state.chat_history.append(("You", user_q))
        st.session_state.chat_history.append(("AI", ai_reply))

    for speaker, msg in st.session_state.chat_history:
        st.markdown(f"**{speaker}:** {msg}")


# -------------------------
# TOTAL IMPACT PAGE
# -------------------------
elif st.session_state.page == "Impact Dashboard":
    import pandas as pd
    import plotly.express as px

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🌍 Your Sustainability Impact")
    st.caption("A living story of how your choices shape the planet 🌱")

    # =============================
    # REQUIRE HISTORY
    # =============================
    if "impact_history" not in st.session_state or st.session_state.impact_history.empty:
        st.info("Analyse products to start building your impact story 🌱")
        st.stop()

    history = st.session_state.impact_history.copy()

    st.divider()

    # =============================
    # 🌱 BIG SUMMARY METRICS
    # =============================
    avg_score = history["Eco Score"].mean()
    total_score = history["Eco Score"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average Eco Score", f"{avg_score:.1f} / 100")
    c2.metric("Products Logged", len(history))
    c3.metric("High-Eco Choices", (history["Eco Score"] >= 80).sum())
    c4.metric("Total Eco Score", int(total_score))

    st.divider()

    # =============================
    # 🌍 HUMAN IMPACT TRANSLATION
    # =============================
    avg_carbon = history["Carbon (kg)"].mean()
    avg_water = history["Water (L)"].mean()
    avg_energy = history["Energy (MJ)"].mean()

    st.markdown("## 🌍 What This Means for the Planet")

    st.markdown(f"""
🌱 **On average, your purchases cause:**

- 💨 **{avg_carbon:.2f} kg CO₂**  
  *(≈ charging a phone {int(avg_carbon*120)} times 📱)*

- 💧 **{avg_water:.1f} L water use**  
  *(≈ {int(avg_water/50)} quick showers 🚿)*

- ⚡ **{avg_energy:.1f} MJ energy demand**  
  *(≈ powering a home for hours 🔌)*

✨ *Small choices. Real consequences. Growing awareness.*
""")

    st.divider()

    # =============================
    # 📈 ECOSCORE TREND
    # =============================
    st.markdown("## 📈 Your EcoScore Journey")

    trend_fig = px.line(
        history.reset_index(),
        x=history.reset_index().index,
        y="Eco Score",
        markers=True,
        color_discrete_sequence=["#22c55e"]
    )

    trend_fig.update_layout(
        xaxis_title="Order of products analysed",
        yaxis_title="Eco Score"
    )

    st.plotly_chart(trend_fig, use_container_width=True)
    if len(history) >= 2:
            delta = history["Eco Score"].iloc[-1] - history["Eco Score"].iloc[0]

            if delta > 5:
                st.success(f"📈 Your EcoScore improved by **{delta:.1f} points** — your choices are getting greener 🌿")
            elif delta < -5:
                st.warning(f"📉 Your EcoScore dropped by **{abs(delta):.1f} points** — consider greener swaps 🔄")
            else:
                st.info("➖ Your EcoScore has stayed fairly stable — consistency is forming 🌱")

    st.divider()

   

    # =============================
    # 📊 AVERAGE IMPACT BREAKDOWN
    # =============================
    st.markdown("## 📊 What Impacts You the Most")

    impact_avg = history[
        ["Carbon (kg)", "Water (L)", "Energy (MJ)", "Waste Score"]
    ].mean().reset_index()

    impact_avg.columns = ["Impact Type", "Average Value"]

    impact_fig = px.bar(
        impact_avg,
        x="Impact Type",
        y="Average Value",
        color="Impact Type",
        color_discrete_sequence=px.colors.sequential.Greens
    )

    st.plotly_chart(impact_fig, use_container_width=True)

    st.divider()

    # =============================
    # 🔄 STACKED PRODUCT COMPARISON
    # =============================
    st.markdown("## 🔄 Compare Products by Impact")
    st.caption("See *why* a product scores better — not just the number 🌿")

    compare_products = st.multiselect(
        "Select products",
        history["Product"].unique(),
        default=list(history["Product"].unique()[:2])
    )

    if len(compare_products) >= 2:
        compare_df = history[history["Product"].isin(compare_products)]

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
            color_discrete_sequence=px.colors.sequential.Greens
        )

        st.plotly_chart(stacked_fig, use_container_width=True)
    else:
        st.info("Select at least two products 🌱")

    st.divider()

    # =============================
    # 🏆 ECO STATUS
    # =============================
    st.markdown("## 🏆 Your Sustainability Status")

    if avg_score >= 80:
        st.success("🌟 Eco Hero — nature approves")
    elif avg_score >= 65:
        st.info("👍 Conscious Consumer")
    elif avg_score >= 50:
        st.warning("⚠️ Improving — momentum building")
    else:
        st.error("❗ High Impact — greener swaps needed")

    st.divider()

    # =============================
    # 📜 HISTORY TABLE
    # =============================
    st.markdown("## 📜 Your Impact Log")
    st.dataframe(history[::-1], use_container_width=True)

    if st.button("🗑️ Clear Impact History"):
        st.session_state.impact_history = st.session_state.impact_history.iloc[0:0]

        # 🔑 also reset logging guards
        if "logged_keys" in st.session_state:
            st.session_state.logged_keys.clear()

        st.success("Impact history cleared 🌱")
        st.rerun()


# -------------------------
# YOUR NEXT STEPS PAGE
# -------------------------
elif st.session_state.page == "NextSteps":

    st.button("← Back to Home", on_click=go, args=("Home",))
    st.title("🧭 Your Next Steps")
    st.caption("Practical swaps and habits to lower your impact")

    category = st.selectbox(
        "Choose a product type",
        ["Shampoo", "Cream", "Sunscreen", "Body Wash"]
    )

    st.divider()

    # -------------------------
    # BEST ECO SUBSTITUTES
    # -------------------------
    BEST_SUBS = {
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
            "Earth Rhythm Body Wash Bar"
        ]
    }

    st.subheader("🌿 Better Alternatives")

    for prod in BEST_SUBS[category]:
        st.markdown(f"✅ {prod}")

    st.divider()

    # -------------------------
    # IF YOU ALREADY BOUGHT IT
    # -------------------------
    st.subheader("♻️ If You Already Bought a Regular Product")

    tips = [
        "Use the product fully before replacing it",
        "Reuse the container for storage or refills",
        "Recycle packaging properly",
        "Use smaller amounts per wash",
        "Avoid double-washing or overuse"
    ]

    for t in tips:
        st.markdown(f"- {t}")

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


    
