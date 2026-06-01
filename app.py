import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace Map", layout="wide", page_icon="🌍")

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

# --- COHORT COLOR CONFIG ---
YEAR_COLORS = {
    2025: "#00B5AD",  # Teal
    2026: "#FF6B6B"   # Coral Red
}

# --- HELPERS ---
def get_base64_image(image_path):
    if isinstance(image_path, str) and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                ext = image_path.split('.')[-1].lower()
                mime = "image/png" if ext == 'png' else "image/jpeg"
                return f"data:{mime};base64,{data}"
        except: return None
    return None

def process_individual_dataframe(file_path, year):
    """Safely cleans and formats an individual year's dataframe, handling missing columns."""
    if not os.path.exists(file_path):
        return pd.DataFrame()
        
    df = pd.read_csv(file_path)
    
    # Ensure necessary columns exist (prevents crashes if a year's sheet is missing them)
    expected_cols = ['Title', 'Institution', 'Location', 'Coordinates', 'Quote', 'Pull Quotes', 'Members', 'Region', 'ID']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
            
    # Fill gaps 
    fill_cols = ['Title', 'Institution', 'Location', 'Coordinates']
    df[fill_cols] = df[fill_cols].ffill()
    
    def parse_coords(c):
        try:
            parts = str(c).split(',')
            return float(parts[0]), float(parts[1])
        except: return None, None
    df['lat'], df['lng'] = zip(*df['Coordinates'].apply(parse_coords))
    
    # If Region is entirely missing, infer from Location
    def get_region(loc):
        loc_str = str(loc).lower()
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str for k in keywords): return region
        return "Other"
        
    if df['Region'].isna().all() and not df['Location'].isna().all():
        df['Region'] = df['Location'].apply(get_region)
    else:
        df['Region'] = df['Region'].fillna("Other")
        
    df['Year'] = year
    df['Color'] = YEAR_COLORS.get(year, "#00B5AD")
    
    project_df = df.groupby('Title').agg({
        'ID': 'first', 'Institution': 'first', 'Members': lambda x: ', '.join([str(m) for m in x.dropna().unique() if str(m).lower() != 'nan']),
        'Location': 'first', 'Region': 'first', 'Color': 'first', 'lat': 'first', 'lng': 'first',
        'Pull Quotes': 'first', 'Quote': 'first', 'Year': 'first'
    }).reset_index()

    def get_tags(title, p_col, s_col):
        if p_col not in df.columns or s_col not in df.columns: return []
        subset = df[df['Title'] == title]
        return [str(t).strip() for t in pd.concat([subset[p_col], subset[s_col]]).dropna().unique() if str(t).lower() != 'nan']

    project_df['Issues'] = project_df['Title'].apply(lambda t: get_tags(t, 'Issue Primary', 'Issue Secondary'))
    project_df['Approaches'] = project_df['Title'].apply(lambda t: get_tags(t, 'Approach Primary', 'Approach Secondary'))

    def resolve_img(id_val):
        if pd.isna(id_val): return None
        try:
            clean_id = str(int(float(id_val)))
            for ext in ['.jpg', '.jpeg', '.png']:
                path = f"images/{clean_id}{ext}"
                if os.path.exists(path): return path
        except: pass
        return None

    project_df['imageBase64'] = project_df['ID'].apply(resolve_img).apply(get_base64_image)
    return project_df.dropna(subset=['lat', 'lng'])

@st.cache_data
def load_all_data():
    # Process 2025
    df_2025 = process_individual_dataframe('2025 Projects ABC Worksheet - App worksheet.csv', 2025)
    
    # Process 2026 
    df_2026 = process_individual_dataframe('2026 Projects ABC Worksheet coordinates - filled.csv', 2026)
    
    # Combine datasets
    dfs_to_concat = []
    if not df_2025.empty: dfs_to_concat.append(df_2025)
    if not df_2026.empty: dfs_to_concat.append(df_2026)
    
    if dfs_to_concat:
        return pd.concat(dfs_to_concat, ignore_index=True)
    return pd.DataFrame()

df = load_all_data()

# --- SIDEBAR: INSTRUCTIONS & CONTROLS ---
with st.sidebar:
    st.title("Peace Map Controls")
    
    st.markdown(f"""
    **Map Legend:**
    * <span style="color:{YEAR_COLORS[2025]}; font-weight:bold;">●</span> 2025 Cohort
    * <span style="color:{YEAR_COLORS[2026]}; font-weight:bold;">●</span> 2026 Cohort
    """, unsafe_allow_html=True)
    
    st.info("1. Rotate: Auto-spins\n2. Stop: Hover pin\n3. Explore: Click pin")
    
    st.subheader("📅 Filter Cohort Year")
    available_years = sorted(df['Year'].unique().tolist()) if not df.empty else [2025, 2026]
    sel_years = st.multiselect("Select Years to View", options=available_years, default=available_years)
    
    st.subheader("🔍 Filter Projects")
    search = st.text_input("Search Title or Student Name")
    
    # Generate lists for filters
    all_locations = sorted([str(x) for x in df['Location'].dropna().unique()]) if not df.empty else []
    all_regions = sorted([str(x) for x in df['Region'].dropna().unique()]) if not df.empty else []
    all_inst = sorted([str(x) for x in df['Institution'].dropna().unique()]) if not df.empty else []
    all_issues = sorted(list(set([i for sub in df['Issues'] for i in sub]))) if not df.empty else []
    all_apps = sorted(list(set([a for sub in df['Approaches'] for a in sub]))) if not df.empty else []
    
    sel_region = st.multiselect("Filter by Region", all_regions)
    sel_inst = st.multiselect("Filter by Institution", all_inst)
    sel_issue = st.multiselect("Filter by Issue Area", all_issues)
    sel_app = st.multiselect("Filter by Approach", all_apps)
    
    st.markdown("---")
    st.caption("✨ Tip: Scroll down the main page for the gallery.")

# --- FILTERING LOGIC ---
f_df = df.copy()
if not f_df.empty:
    if sel_years: 
        f_df = f_df[f_df['Year'].isin(sel_years)]
    else:
        f_df = f_df.head(0) 
        
    if search: 
        f_df = f_df[f_df['Title'].str.contains(search, case=False, na=False) | f_df['Members'].str.contains(search, case=False, na=False)]
    if sel_region: 
        f_df = f_df[f_df['Region'].isin(sel_region)]
    if sel_inst: 
        f_df = f_df[f_df['Institution'].isin(sel_inst)]
    if sel_issue: 
        f_df = f_df[f_df['Issues'].apply(lambda x: any(i in x for i in sel_issue))]
    if sel_app: 
        f_df = f_df[f_df['Approaches'].apply(lambda x: any(a in x for a in sel_app))]

# --- GLOBE ---
st.title("Projects for Peace: Global Dashboard 🌍")
points_json = json.dumps(f_df.mask(f_df.isna(), None).to_dict(orient='records')) if not f_df.empty else "[]"

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
            
            // Handle missing quotes/locations gracefully
            const cleanQuote = d['Pull Quotes'] ? `"${{d['Pull Quotes'].replace(/^"|"$/g, '')}}"` : '';
            const locationText = d.Location ? `📍 ${{d.Location}}` : `📍 ${{d.Region}}`;

            document.getElementById('card-content').innerHTML = `
                ${{img}}
                <div style="padding:15px;">
                    <div style="font-weight:bold; font-size:1.1em; color:#111; margin-bottom:5px;">${{d.Title}}</div>
                    <div style="font-size:0.85em; font-weight:bold; color:\${{d.Color}}; margin-bottom:10px;">\${{d.Year}} Cohort | \${{d.Institution}}</div>
                    <div style="font-size:0.85em; color:#666; margin-bottom:10px;">\${{locationText}}</div>
                    <div style="font-size:0.95em; font-style:italic; color:#333; border-top:1px solid #eee; padding-top:10px;">\${{cleanQuote}}</div>
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
    st.warning("No projects match your current filters.")
else:
    for _, row in f_df.iterrows():
        with st.expander(f"📍 [{row['Year']}] {row['Title']} ({row['Institution']})"):
            c1, c2 = st.columns([2, 1])
            with c1:
                if row.get('Location'): st.write(f"**Location:** {row['Location']}")
                if row.get('Members'): st.write(f"**Team:** {row['Members']}")
                if row.get('Issues'): st.write(f"**Focus:** {', '.join(row['Issues'])}")
                if row.get('Approaches'): st.write(f"**Approach:** {', '.join(row['Approaches'])}")
                if row.get('Pull Quotes'): st.info(f"*{str(row['Pull Quotes']).strip('\"')}*")
                if row.get('Quote'): st.write(row['Quote'])
            with c2:
                if row.get('imageBase64'):
                    st.markdown(f'<img src="{row["imageBase64"]}" style="width:100%; border-radius:10px;">', unsafe_allow_html=True)
                else:
                    st.caption("No image available.")
