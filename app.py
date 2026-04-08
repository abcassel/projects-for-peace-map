import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide", page_icon="🌍")

# --- REGION MAPPING ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Ethiopia", "Uganda", "Zambia", "Malawi", "Egypt", "Cacuaco", "Makeni", "Arusha", "Laikipia", "Kasungu", "Kigali", "Bugesera", "Langa", "Lagos", "Lokichoggio", "Kiambu", "Accra", "Tonj", "Addis Ababa", "Ouangolodougou", "Moamba", "Kadi'ba", "Kashusha", "Kisumu", "Nairobi", "Akuse", "Bassar", "Johannesburg", "Matabeleland", "Gweru", "Niamey"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Vietnam", "Thailand", "Sri Lanka", "Singapore", "Mongolia", "Jaipur", "Islamabad", "Bayramaly", "Lalitpur", "Mughalpura", "Sindhuli", "Yasin Ghizer", "Koshi", "Mustang", "Jiangsu", "Khagrachari", "Dili", "Hokkaido", "Kachankawal", "Jakarta", "Zhalal-Abad", "Rangamati", "Vijayawada", "Sulawesi", "Tokyo", "Phnom Penh", "Sibuyan", "Sankhatar", "Chakwal", "Bali", "Chittagong", "Uttar Pradesh", "Punjab", "Dhaka", "Timor-Leste", "East Timor"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Georgia", "Armenia", "Kosovo", "Albania", "France", "Spain", "Epirus", "Bucharest", "Mainz", "Skopje", "Chernivtsi"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Guatemala", "Honduras", "Haiti", "Dominican Republic", "Jamaica", "Belize", "Toronto", "Baltimore", "Chicago", "Maine", "Michigan", "Nashville", "San Bernardino", "Pennsylvania", "New York", "Gainesville", "Boston", "North Carolina", "Oregon", "Pittsburgh", "Maryland", "Oaxaca"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Bolivia", "Chile", "Paraguay", "Bahia", "Montevideo", "Medellín", "Planes-Mirador", "Chimborazo", "Rio de Janeiro", "Concepcion", "Jacarezinho", "Quito", "Colonia Suiza", "Pocrane"],
    "Middle East": ["Syria", "Cairo"],
    "Oceania": ["Marshall Islands", "Kwajalein", "Fiji", "Samoa", "Vanuatu"]
}

TEAL_COLOR = "#00B5AD"

# --- HELPERS ---
def get_base64_image(image_path):
    if isinstance(image_path, str) and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                # Detect extension for the mime type
                ext = image_path.split('.')[-1].lower()
                if ext == 'png': mime = "image/png"
                else: mime = "image/jpeg"
                return f"data:{mime};base64,{data}"
        except: return None
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
    
    df['Region'] = df['Location'].apply(lambda x: next((r for r, k in REGION_MAP.items() if any(i.lower() in str(x).lower() for i in k)), "Other"))
    df['Color'] = TEAL_COLOR

    project_df = df.groupby('Title').agg({
        'ID': 'first', 'Institution': 'first', 'Members': lambda x: ', '.join(x.dropna().unique()),
        'Location': 'first', 'Region': 'first', 'Color': 'first', 'lat': 'first', 'lng': 'first',
        'Pull Quotes': 'first', 'Quote': 'first'
    }).reset_index()

    def get_tags(title, p_col, s_col):
        subset = df[df['Title'] == title]
        return [str(t).strip() for t in pd.concat([subset[p_col], subset[s_col]]).dropna().unique() if str(t).lower() != 'nan']

    project_df['Issues'] = project_df['Title'].apply(lambda t: get_tags(t, 'Issue Primary', 'Issue Secondary'))
    project_df['Approaches'] = project_df['Title'].apply(lambda t: get_tags(t, 'Approach Primary', 'Approach Secondary'))

    def resolve_img(id_val):
        if pd.isna(id_val): return None
        for ext in ['.jpg', '.jpeg', '.png']:
            path = f"images/{int(id_val)}{ext}"
            if os.path.exists(path): return path
        return None

    project_df['imageBase64'] = project_df['ID'].apply(resolve_img).apply(get_base64_image)
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Peace Map Controls")
    st.info("1. Rotate: Auto-spins\n2. Stop: Hover pin\n3. Explore: Click pin")
    st.subheader("🔍 Filter Projects")
    search = st.text_input("Search Title or Student Name")
    sel_loc = st.multiselect("Filter by Location", sorted(df['Location'].unique()))
    sel_inst = st.multiselect("Filter by Institution", sorted(df['Institution'].unique()))
    st.markdown("---")
    st.caption("✨ Tip: Scroll down the main page for the gallery.")

# --- FILTERING ---
f_df = df.copy()
if search: f_df = f_df[f_df['Title'].str.contains(search, case=False) | f_df['Members'].str.contains(search, case=False)]
if sel_loc: f_df = f_df[f_df['Location'].isin(sel_loc)]
if sel_inst: f_df = f_df[f_df['Institution'].isin(sel_inst)]

# --- GLOBE ---
st.title("Projects for Peace: 2025 Cohort 🌍")
points_json = json.dumps(f_df.mask(f_df.isna(), None).to_dict(orient='records'))

globe_html = f"""
<div id="globeViz"></div>
<div id="info-card" style="position: absolute; top: 10px; right: 10px; width: 300px; max-height: 90vh; background: white; border-radius: 12px; display: none; overflow-y: auto; z-index: 100; border: 1px solid #eee; font-family: sans-serif;">
    <div id="close-btn" onclick="this.parentElement.style.display='none'" style="position: absolute; top: 10px; right: 15px; cursor: pointer; font-size: 24px; color: #999;">×</div>
    <div id="card-content"></div>
</div>
<script src="//unpkg.com/globe.gl"></script>
<script>
    const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .pointsData({points_json})
        .pointLat('lat').pointLng('lng').pointColor('Color')
        .pointRadius(0.8).pointAltitude(0.01).pointLabel('Title')
        .onPointHover(p => world.controls().autoRotate = !p)
        .onPointClick(d => {{
            const card = document.getElementById('info-card');
            card.style.display = 'block';
            const img = d.imageBase64 ? `<img src="${{d.imageBase64}}" style="width:100%; height:160px; object-fit:cover; border-radius:12px 12px 0 0;">` : '';
            document.getElementById('card-content').innerHTML = `
                ${{img}}
                <div style="padding:15px;">
                    <div style="font-weight:bold; font-size:1.1em; color:#111; margin-bottom:5px;">${{d.Title}}</div>
                    <div style="font-size:0.85em; color:#666; margin-bottom:10px;">${{d.Institution}} | ${{d.Location}}</div>
                    <div style="font-size:0.95em; font-style:italic; color:#333; border-top:1px solid #eee; padding-top:10px;">"${{(d['Pull Quotes'] || '').replace(/^"|"$/g, '')}}"</div>
                </div>`;
        }});
    world.controls().autoRotate = true;
</script>
<style>body{{margin:0;}} #globeViz{{width:100%; height:600px;}}</style>
"""
components.html(globe_html, height=600)

# --- GALLERY ---
st.write("---")
st.subheader("📖 Project Gallery")
if f_df.empty:
    st.warning("No projects match.")
else:
    for _, row in f_df.iterrows():
        with st.expander(f"📍 {row['Title']} ({row['Institution']})"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**Location:** {row['Location']}")
                st.write(f"**Team:** {row['Members']}")
                st.info(f"*{str(row['Pull Quotes']).strip('\"')}*")
                st.write(row['Quote'])
            with c2:
                if row['imageBase64']:
                    # BYPASSING st.image: Using raw HTML to display the base64 string safely
                    st.markdown(f'<img src="{row["imageBase64"]}" style="width:100%; border-radius:10px;">', unsafe_allow_html=True)
                else:
                    st.caption("No image available.")
