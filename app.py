import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide", page_icon="🌍")

# --- ANCHOR: TOP OF PAGE ---
st.markdown('<div id="top"></div>', unsafe_allow_html=True)

# --- REGION MAPPING & COLORS (Keep your existing mapping) ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Ethiopia", "Uganda", "Zambia", "Malawi", "Egypt"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Vietnam", "Thailand", "Sri Lanka"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Georgia", "Armenia", "Kosovo", "Albania", "France", "Spain"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Guatemala", "Honduras", "Haiti", "Dominican Republic", "Jamaica", "Belize"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Bolivia", "Chile", "Paraguay"],
    "Middle East": ["Syria", "Cairo"],
    "Oceania": ["Marshall Islands", "Kwajalein", "Fiji", "Samoa", "Vanuatu"]
}

REGION_COLORS = {
    "Africa": "#FF9F43", "Asia": "#FF6B6B", "Europe": "#4834D4", "North America": "#1DD1A1", 
    "South America": "#FECA57", "Middle East": "#54a0ff", "Oceania": "#9B59B6", "Other": "#C8D6E5"
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
    
    def get_region(loc):
        loc_str = str(loc).lower()
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str for k in keywords): return region
        return "Other"
    df['Region'] = df['Location'].apply(get_region)
    df['Color'] = df['Region'].apply(lambda r: REGION_COLORS.get(r, "#C8D6E5"))

    project_df = df.groupby('Title').agg({
        'ID': 'first',
        'Institution': 'first',
        'Members': lambda x: ', '.join(x.dropna().unique()),
        'Location': 'first',
        'Region': 'first',
        'Color': 'first',
        'lat': 'first',
        'lng': 'first',
        'Pull Quotes': 'first',
        'Quote': 'first'
    }).reset_index()

    def get_tags(title, p_col, s_col):
        subset = df[df['Title'] == title]
        tags = pd.concat([subset[p_col], subset[s_col]]).dropna().unique()
        return [str(t).strip() for t in tags if str(t).lower() != 'nan']

    project_df['Issues'] = project_df['Title'].apply(lambda t: get_tags(t, 'Issue Primary', 'Issue Secondary'))
    project_df['Approaches'] = project_df['Title'].apply(lambda t: get_tags(t, 'Approach Primary', 'Approach Secondary'))

    def resolve_img(id_val):
        if pd.isna(id_val): return None
        clean_id = str(int(id_val))
        for ext in ['.jpg', '.jpeg', '.png']:
            path = f"images/{clean_id}{ext}"
            if os.path.exists(path): return path
        return None

    project_df['imagePath'] = project_df['ID'].apply(resolve_img)
    project_df['imageBase64'] = project_df['imagePath'].apply(get_base64_image)
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Peace Map Controls")
    st.subheader("🔍 Filter Projects")
    search = st.text_input("Search Title or Student Name")
    all_locations = sorted(df['Location'].unique())
    sel_loc = st.multiselect("Filter by Location", all_locations)
    sel_inst = st.multiselect("Filter by Institution", sorted(df['Institution'].unique()))

# --- FILTER LOGIC ---
f_df = df.copy()
if search:
    f_df = f_df[f_df['Title'].str.contains(search, case=False) | f_df['Members'].str.contains(search, case=False)]
if sel_loc:
    f_df = f_df[f_df['Location'].isin(sel_loc)]
if sel_inst:
    f_df = f_df[f_df['Institution'].isin(sel_inst)]

# --- GLOBE COMPONENT ---
st.title("Projects for Peace: 2025 Cohort 🌍")

points_json = json.dumps(f_df.mask(f_df.isna(), None).to_dict(orient='records'))

globe_html = f"""
<div id="globeViz"></div>
<div id="info-card">
    <div id="close-btn" onclick="document.getElementById('info-card').style.display='none'">×</div>
    <div id="card-content"></div>
</div>

<script src="//unpkg.com/globe.gl"></script>
<style>
    body {{ margin: 0; font-family: sans-serif; background: transparent; }}
    #info-card {{
        position: absolute; top: 10px; right: 10px; width: 300px; max-height: 90vh;
        background: white; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        display: none; overflow-y: auto; z-index: 100; border: 1px solid #eee;
    }}
    #close-btn {{ position: absolute; top: 10px; right: 15px; cursor: pointer; font-size: 24px; color: #999; }}
    .c-img {{ width: 100%; border-radius: 12px 12px 0 0; object-fit: cover; height: 160px; }}
    .c-body {{ padding: 15px; }}
    .c-title {{ font-weight: bold; font-size: 1.1em; color: #111; margin-bottom: 5px; }}
    .c-link {{ 
        display: inline-block; margin-top: 15px; padding: 8px 12px; 
        background-color: #4834D4; color: white; text-decoration: none; 
        border-radius: 6px; font-size: 0.85em; font-weight: bold;
    }}
</style>

<script>
    const data = {points_json};
    const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .pointsData(data)
        .pointLat('lat').pointLng('lng').pointColor('Color')
        .pointRadius(0.8).pointAltitude(0.01)
        .pointLabel('Title')
        .onPointHover(point => {{ world.controls().autoRotate = !point; }})
        .onPointClick(d => {{
            const card = document.getElementById('info-card');
            card.style.display = 'block';
            const img = d.imageBase64 ? `<img src="${{d.imageBase64}}" class="c-img">` : '';
            const cleanQuote = (d['Pull Quotes'] || 'No pull quote provided.').replace(/^"|"$/g, '');

            document.getElementById('card-content').innerHTML = `
                ${{img}}
                <div class="c-body">
                    <div class="c-title">${{d.Title}}</div>
                    <div style="font-size: 0.85em; color: #666;">${{d.Institution}} | ${{d.Location}}</div>
                    <div style="font-size: 0.95em; font-style: italic; color: #333; margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px;">"${{cleanQuote}}"</div>
                    <a href="#project-${{d.ID}}" target="_self" class="c-link">📖 View Full Details</a>
                </div>
            `;
        }});
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.6;
</script>
"""
components.html(globe_html, height=600)

# --- DETAILED LIST VIEW ---
st.write("---")
st.subheader("📖 Project Gallery")

if f_df.empty:
    st.warning("No projects match your search criteria.")
else:
    for _, row in f_df.iterrows():
        # Anchor for Jump-to
        st.markdown(f'<div id="project-{row["ID"]}"></div>', unsafe_allow_html=True)
        
        display_quote = str(row['Pull Quotes']).strip('"')
        with st.expander(f"📍 {row['Title']} ({row['Institution']})"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Location:** {row['Location']}")
                st.markdown(f"**Team:** {row['Members']}")
                st.info(f"*{display_quote}*")
                st.write(row['Quote'])
                
                # BACK TO GLOBE BUTTON
                st.markdown(f"""
                    <div style="margin-top: 20px;">
                        <a href="#top" target="_self" style="text-decoration: none; color: #4834D4; font-weight: bold; font-size: 0.9em; border: 1px solid #4834D4; padding: 5px 10px; border-radius: 5px;">
                            🌍 Back to Globe
                        </a>
                    </div>
                """, unsafe_allow_html=True)
                
            with c2:
                if row['imagePath']:
                    st.image(row['imagePath'], use_container_width=True)
