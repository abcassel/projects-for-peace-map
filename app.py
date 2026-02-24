import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide", page_icon="🌍")

# --- MAPPINGS ---
# (Keeping your REGION_MAP and ISSUE_EMOJI_MAP as before)
ISSUE_EMOJI_MAP = {
    "Education": "📚", "Food Security": "🍎", "Environment": "🌱",
    "Health": "🏥", "Economic Development": "💰", "Technology": "💻",
    "Arts": "🎨", "Peacebuilding": "🕊️", "Conflict Resolution": "🤝",
    "Human Rights": "⚖️", "Youth Empowerment": "🎒", "Women's Empowerment": "💜"
}

# --- HELPERS ---
def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{data}"
    return None

@st.cache_data
def load_data():
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    fill_cols = ['Title', 'Institution', 'Location', 'Coordinates', 'Quote', 'Pull Quotes']
    df[fill_cols] = df[fill_cols].ffill()
    
    def parse_coords(c):
        try:
            parts = str(c).split(',')
            return float(parts[0]), float(parts[1])
        except: return None, None
    df['lat'], df['lng'] = zip(*df['Coordinates'].apply(parse_coords))
    
    project_df = df.groupby('Title').agg({
        'ID': 'first', 'Institution': 'first', 'Location': 'first',
        'lat': 'first', 'lng': 'first', 'Pull Quotes': 'first',
        'Quote': 'first', 'Issue Primary': 'first',
        'Members': lambda x: ', '.join(x.dropna().unique())
    }).reset_index()

    # Create the display label with Emoji
    def make_label(row):
        emoji = ISSUE_EMOJI_MAP.get(str(row['Issue Primary']).strip(), "📍")
        return f"{emoji} {row['Title']}"
    
    project_df['DisplayLabel'] = project_df.apply(make_label, axis=1)
    
    def resolve_img(id_val):
        if pd.isna(id_val): return None
        path = f"images/{str(int(id_val))}.jpg" # Simplified for debug
        return path if os.path.exists(path) else None

    project_df['imageBase64'] = project_df['ID'].apply(resolve_img).apply(get_base64_image)
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Peace Map Controls")
    st.info("Rotate the globe to explore. Click a pin to see the story.")
    search = st.text_input("Search Title or Student")
    sel_loc = st.multiselect("Filter by Location", sorted(df['Location'].unique()))

# --- FILTER LOGIC ---
f_df = df.copy()
if search:
    f_df = f_df[f_df['Title'].str.contains(search, case=False)]
if sel_loc:
    f_df = f_df[f_df['Location'].isin(sel_loc)]

# --- GLOBE ---
st.title("Projects for Peace: 2025 Cohort 🌍")

# Prepare JSON
points_json = json.dumps(f_df.to_dict(orient='records'))

globe_html = f"""
<div id="globeViz"></div>
<div id="info-card">
    <div id="close-btn" onclick="document.getElementById('info-card').style.display='none'">×</div>
    <div id="card-content"></div>
</div>

<script src="//unpkg.com/globe.gl"></script>
<script>
    const data = {points_json};
    const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .pointsData(data)
        .pointLat('lat')
        .pointLng('lng')
        .pointColor(() => '#ffeb3b') // Bright yellow points for visibility
        .pointRadius(0.7)
        .pointLabel('DisplayLabel') // This shows the Emoji + Title on hover
        .onPointClick(d => {{
            const card = document.getElementById('info-card');
            card.style.display = 'block';
            const cleanQuote = (d['Pull Quotes'] || '').replace(/^"|"$/g, '');
            const imgHtml = d.imageBase64 ? `<img src="${{d.imageBase64}}" style="width:100%; border-radius:12px 12px 0 0;">` : '';
            
            document.getElementById('card-content').innerHTML = `
                ${{imgHtml}}
                <div style="padding:15px; font-family:sans-serif;">
                    <div style="font-weight:bold; font-size:1.1em;">${{d.Title}}</div>
                    <div style="color:#666; font-size:0.85em;">${{d.Institution}}</div>
                    <div style="margin-top:10px; font-style:italic; border-top:1px solid #eee; padding-top:10px;">"${{cleanQuote}}"</div>
                </div>
            `;
        }});
    world.controls().autoRotate = true;
</script>
<style>
    #info-card {{
        position: absolute; top: 10px; right: 10px; width: 280px; 
        background: white; border-radius: 12px; display: none; z-index: 1000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    #close-btn {{ position: absolute; top: 5px; right: 10px; cursor: pointer; font-size: 20px; }}
</style>
"""

components.html(globe_html, height=600)

# --- GALLERY ---
st.subheader("📖 Project Gallery")
for _, row in f_df.iterrows():
    with st.expander(f"{row['DisplayLabel']} — {row['Location']}"):
        st.write(row['Quote'])
