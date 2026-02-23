import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide", page_icon="🌍")

# --- REGION MAPPING & COLORS ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Ethiopia", "Uganda", "Zambia", "Malawi", "Egypt", "Cacuaco", "Makeni", "Arusha", "Laikipia", "Kasungu", "Kigali", "Bugesera", "Langa", "Lagos", "Lokichoggio", "Kiambu", "Accra", "Tonj", "Addis Ababa", "Ouangolodougou", "Moamba", "Kadi'ba", "Kashusha", "Kisumu", "Nairobi", "Akuse", "Bassar", "Johannesburg", "Matabeleland", "Gweru", "Niamey"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Vietnam", "Thailand", "Sri Lanka", "Singapore", "Mongolia", "Jaipur", "Islamabad", "Bayramaly", "Lalitpur", "Mughalpura", "Sindhuli", "Yasin Ghizer", "Koshi", "Mustang", "Jiangsu", "Khagrachari", "Dili", "Hokkaido", "Kachankawal", "Jakarta", "Zhalal-Abad", "Rangamati", "Vijayawada", "Sulawesi", "Tokyo", "Phnom Penh", "Sibuyan", "Sankhatar", "Chakwal", "Bali", "Chittagong", "Uttar Pradesh", "Punjab", "Dhaka"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Georgia", "Armenia", "Kosovo", "Albania", "France", "Spain", "Epirus", "Bucharest", "Mainz", "Skopje", "Chernivtsi"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Guatemala", "Honduras", "Haiti", "Dominican Republic", "Jamaica", "Belize", "Toronto", "Baltimore", "Chicago", "Maine", "Michigan", "Nashville", "San Bernardino", "Pennsylvania", "New York", "Gainesville", "Boston", "North Carolina", "Oregon", "Pittsburgh", "Maryland", "Oaxaca"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Bolivia", "Chile", "Paraguay", "Bahia", "Montevideo", "Medellín", "Planes-Mirador", "Chimborazo", "Rio de Janeiro", "Concepcion", "Jacarezinho", "Quito", "Colonia Suiza", "Pocrane"],
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
    
    # 1. Clean and Fill Merged Data
    fill_cols = ['Title', 'Institution', 'Location', 'Coordinates', 'Quote', 'Pull Quotes']
    df[fill_cols] = df[fill_cols].ffill()
    
    # 2. Split Coordinates
    def parse_coords(c):
        try:
            parts = str(c).split(',')
            return float(parts[0]), float(parts[1])
        except: return None, None
    df['lat'], df['lng'] = zip(*df['Coordinates'].apply(parse_coords))
    
    # 3. Assign Regions
    def get_region(loc):
        loc_str = str(loc).lower()
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str for k in keywords): return region
        return "Other"
    df['Region'] = df['Location'].apply(get_region)
    df['Color'] = df['Region'].apply(lambda r: REGION_COLORS.get(r, "#C8D6E5"))

    # 4. Group for Projects
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

    # 5. Extract Issue/Approach Tags
    def get_tags(title, p_col, s_col):
        subset = df[df['Title'] == title]
        tags = pd.concat([subset[p_col], subset[s_col]]).dropna().unique()
        return [str(t).strip() for t in tags if str(t).lower() != 'nan']

    project_df['Issues'] = project_df['Title'].apply(lambda t: get_tags(t, 'Issue Primary', 'Issue Secondary'))
    project_df['Approaches'] = project_df['Title'].apply(lambda t: get_tags(t, 'Approach Primary', 'Approach Secondary'))

    # 6. Image Paths & Base64
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

# --- SIDEBAR: INSTRUCTIONS & FILTERS ---
with st.sidebar:
    st.title("Peace Map Controls")
    st.info("""
    **How to interact:**
    1. **Rotate:** The globe spins automatically.
    2. **Stop:** Hover your mouse over a pin to stop the rotation.
    3. **Explore:** Click a pin to see the project's story and photo.
    4. **Filter:** Use the menus below to find specific themes.
    """)
    
    st.subheader("🔍 Filter Projects")
    search = st.text_input("Search Title or Student Name")
    
    # Generate filter lists
    all_inst = sorted(df['Institution'].unique())
    all_issues = sorted(list(set([i for sub in df['Issues'] for i in sub])))
    all_apps = sorted(list(set([a for sub in df['Approaches'] for a in sub])))
    
    sel_inst = st.multiselect("Filter by Institution", all_inst)
    sel_issue = st.multiselect("Filter by Issue Area", all_issues)
    sel_app = st.multiselect("Filter by Approach", all_apps)

# --- FILTER LOGIC ---
f_df = df.copy()
if search:
    f_df = f_df[f_df['Title'].str.contains(search, case=False) | f_df['Members'].str.contains(search, case=False)]
if sel_inst:
    f_df = f_df[f_df['Institution'].isin(sel_inst)]
if sel_issue:
    f_df = f_df[f_df['Issues'].apply(lambda x: any(i in x for i in sel_issue))]
if sel_app:
    f_df = f_df[f_df['Approaches'].apply(lambda x: any(a in x for a in sel_app))]

# --- GLOBE COMPONENT ---
st.title("Projects for Peace: 2025 Cohort 🌍")

# Prepare JSON for JS
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
    .c-title {{ font-weight: bold; font-size: 1.1em; color: #111; margin-bottom: 5px; line-height: 1.2; }}
    .c-school {{ font-size: 0.85em; color: #666; margin-bottom: 10px; }}
    .c-quote {{ font-size: 0.95em; font-style: italic; color: #333; border-top: 1px solid #eee; padding-top: 10px; }}
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
            const content = document.getElementById('card-content');
            card.style.display = 'block';
            const img = d.imageBase64 ? `<img src="${{d.imageBase64}}" class="c-img">` : '';
            content.innerHTML = `
                ${{img}}
                <div class="c-body">
                    <div class="c-title">${{d.Title}}</div>
                    <div class="c-school">${{d.Institution}} | ${{d.Location}}</div>
                    <div class="c-quote">"${{d['Pull Quotes'] || 'No pull quote provided.'}}"</div>
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
        with st.expander(f"📍 {row['Title']} ({row['Institution']})"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Location:** {row['Location']}")
                st.markdown(f"**Team:** {row['Members']}")
                st.markdown(f"**Focus:** {', '.join(row['Issues'])}")
                st.markdown(f"**Approach:** {', '.join(row['Approaches'])}")
                st.info(f"*{row['Pull Quotes']}*")
            with c2:
                if row['imagePath']:
                    st.image(row['imagePath'], use_container_width=True)
                else:
                    st.caption("No image available.")
            
            st.write("---")
            st.write("**The Full Story:**")
            st.write(row['Quote'])
