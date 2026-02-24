import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide", page_icon="🌍")

# --- MAPPINGS ---
ISSUE_EMOJI_MAP = {
    "Education": "📚", "Food Security": "🍎", "Environment": "🌱",
    "Health": "🏥", "Economic Development": "💰", "Technology": "💻",
    "Arts": "🎨", "Peacebuilding": "🕊️", "Conflict Resolution": "🤝",
    "Human Rights": "⚖️", "Youth Empowerment": "🎒", "Women's Empowerment": "💜"
}

# --- HELPERS ---
def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                return f"data:image/jpeg;base64,{data}"
        except: return None
    return None

@st.cache_data
def load_data():
    # Ensure this matches your exact filename
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    
    # Clean and Fill Data
    fill_cols = ['Title', 'Institution', 'Location', 'Coordinates', 'Quote', 'Pull Quotes']
    df[fill_cols] = df[fill_cols].ffill()
    
    def parse_coords(c):
        try:
            parts = str(c).split(',')
            return float(parts[0]), float(parts[1])
        except: return None, None
    df['lat'], df['lng'] = zip(*df['Coordinates'].apply(parse_coords))
    
    # Group for Projects
    project_df = df.groupby('Title').agg({
        'ID': 'first',
        'Institution': 'first',
        'Location': 'first',
        'lat': 'first',
        'lng': 'first',
        'Pull Quotes': 'first',
        'Quote': 'first',
        'Issue Primary': 'first',
        'Members': lambda x: ', '.join(x.dropna().unique().astype(str))
    }).reset_index()

    # Create the label that shows the Emoji
    def get_disp_label(row):
        emoji = ISSUE_EMOJI_MAP.get(str(row['Issue Primary']).strip(), "📍")
        return f"{emoji} {row['Title']}"
    
    project_df['DisplayLabel'] = project_df.apply(get_disp_label, axis=1)

    # Process Images
    def resolve_img(id_val):
        if pd.isna(id_val): return None
        clean_id = str(int(float(id_val)))
        for ext in ['.jpg', '.jpeg', '.png']:
            path = f"images/{clean_id}{ext}"
            if os.path.exists(path): return path
        return None

    project_df['imageBase64'] = project_df['ID'].apply(resolve_img).apply(get_base64_image)
    
    return project_df.dropna(subset=['lat', 'lng'])

# Load data once
df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Peace Map Controls")
    st.info("""
    **How to interact:**
    1. **Rotate:** Globe spins automatically.
    2. **Stop:** Hover over a pin.
    3. **Explore:** Click a pin for the story.
    """)
    
    st.subheader("🔍 Search & Filter")
    search = st.text_input("Search Title or Student Name")
    all_locs = sorted(df['Location'].unique())
    sel_loc = st.multiselect("Filter by Location", all_locs)

# --- FILTER LOGIC ---
f_df = df.copy()
if search:
    f_df = f_df[f_df['Title'].str.contains(search, case=False) | f_df['Members'].str.contains(search, case=False)]
if sel_loc:
    f_df = f_df[f_df['Location'].isin(sel_loc)]

# --- GLOBE COMPONENT ---
st.title("Projects for Peace: 2025 Cohort 🌍")

# Convert to JSON for JS (handling NaNs)
points_json = json.dumps(f_df.where(pd.notnull(f_df), None).to_dict(orient='records'))

globe_html = f"""
<div id="globeViz" style="width: 100%; height: 600px;"></div>
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
        .pointColor(() => '#FFD700') // Gold color
        .pointRadius(0.6)
        .pointAltitude(0.01) // Keep them flat to the surface (prevents "pylons")
        .pointLabel('DisplayLabel')
        .onPointClick(d => {{
            const card = document.getElementById('info-card');
            card.style.display = 'block';
            
            const imgHtml = d.imageBase64 ? `<img src="${{d.imageBase64}}" class="c-img">` : '';
            const cleanQuote = (d['Pull Quotes'] || '').replace(/^"|"$/g, '');

            document.getElementById('card-content').innerHTML = `
                ${{imgHtml}}
                <div class="c-body">
                    <div class="c-title">${{d.Title}}</div>
                    <div class="c-school">${{d.Institution}} | ${{d.Location}}</div>
                    <div class="c-quote">"${{cleanQuote}}"</div>
                </div>
            `;
        }});

    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.7;
</script>

<style>
    body {{ margin: 0; font-family: sans-serif; }}
    #info-card {{
        position: absolute; top: 10px; right: 10px; width: 300px; max-height: 80vh;
        background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        display: none; overflow-y: auto; z-index: 1000; border: 1px solid #eee;
    }}
    #close-btn {{ position: absolute; top: 10px; right: 15px; cursor: pointer; font-size: 20px; color: #999; }}
    .c-img {{ width: 100%; border-radius: 12px 12px 0 0; object-fit: cover; height: 160px; }}
    .c-body {{ padding: 15px; }}
    .c-title {{ font-weight: bold; font-size: 1.1em; color: #111; }}
    .c-school {{ font-size: 0.85em; color: #666; margin-top: 4px; }}
    .c-quote {{ font-size: 0.95em; font-style: italic; color: #444; margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px; }}
</style>
"""

components.html(globe_html, height=620)

# --- GALLERY ---
st.write("---")
st.subheader("📖 Project Gallery")
if f_df.empty:
    st.warning("No projects found matching those filters.")
else:
    for _, row in f_df.iterrows():
        # Clean quotes for the expander
        q = str(row['Pull Quotes']).strip('"')
        with st.expander(f"{row['DisplayLabel']} — {row['Location']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**Team:** {row['Members']}")
                st.info(f"\"{q}\"")
                st.write(row['Quote'])
            with c2:
                if row['imageBase64']:
                    st.image(row['imageBase64'], use_container_width=True)
