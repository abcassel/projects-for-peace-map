import streamlit as st
import pandas as pd
import json
import os
import base64
from io import BytesIO
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide")

# --- REGION MAPPING ---
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

# --- IMAGE HELPER ---
def get_base64_image(image_path):
    """Encodes an image to a base64 string for the HTML globe."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

@st.cache_data
def load_data():
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    cols_to_fill = ['Title', 'Institution', 'Location', 'Latitude', 'Longitude', 'Issue Primary', 'Approach Primary', 'Pull Quotes', 'Quote']
    df[cols_to_fill] = df[cols_to_fill].ffill()
    
    def get_region(loc):
        loc_str = str(loc)
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str.lower() for k in keywords): return region
        return "Other"
    
    df['Region'] = df['Location'].apply(get_region)
    df['Color'] = df['Region'].apply(lambda r: REGION_COLORS.get(r, "#CCCCCC"))
    
    # Process Tags
    def clean_tags(row, col_p, col_s):
        tags = [str(row[col_p]), str(row[col_s])]
        return [t.strip().title() for t in tags if pd.notna(t) and str(t).lower() != 'nan' and t.strip() != '']

    df['Issues_List'] = df.apply(lambda r: clean_tags(r, 'Issue Primary', 'Issue Secondary'), axis=1)
    df['Apps_List'] = df.apply(lambda r: clean_tags(r, 'Approach Primary', 'Approach Secondary'), axis=1)

    project_df = df.groupby('Title').agg({
        'ID': 'first', 'Institution': 'first', 
        'Members': lambda x: ', '.join([str(m) for m in x.unique() if pd.notna(m)]),
        'Location': 'first', 'Region': 'first', 'Color': 'first',
        'Latitude': 'first', 'Longitude': 'first', 'Pull Quotes': 'first', 'Quote': 'first'
    }).reset_index()
    
    issues_map = df.groupby('Title')['Issues_List'].apply(lambda x: list(set([item for sublist in x for item in sublist])))
    apps_map = df.groupby('Title')['Apps_List'].apply(lambda x: list(set([item for sublist in x for item in sublist])))
    project_df['All_Issues'] = project_df['Title'].map(issues_map)
    project_df['All_Approaches'] = project_df['Title'].map(apps_map)
    
    # Image Path Logic
    def resolve_image(id_val):
        for ext in ['.jpeg', '.jpg', '.png', '.JPEG', '.JPG', '.PNG']:
            p = f"images/{id_val}{ext}"
            if os.path.exists(p): return p
        return ""

    project_df['imagePath'] = project_df['ID'].apply(resolve_image)
    # This creates the Base64 string specifically for the Globe
    project_df['imageBase64'] = project_df['imagePath'].apply(get_base64_image)
    
    project_df = project_df.rename(columns={'Latitude': 'lat', 'Longitude': 'lng'})
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- FILTERS ---
st.sidebar.header("🔍 Search & Filter")
search_query = st.sidebar.text_input("Search Project/Student")
unique_inst = sorted([str(x).strip() for x in df['Institution'].unique() if pd.notna(x)])
unique_reg = sorted([str(x).strip() for x in df['Region'].unique() if pd.notna(x)])

selected_inst = st.sidebar.multiselect("Institution", options=unique_inst)
selected_regions = st.sidebar.multiselect("Region", options=unique_reg)

f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions: f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst: f_df = f_df[f_df['Institution'].isin(selected_inst)]

# --- GLOBE ---
st.title("Projects for Peace 🌍")
f_df_clean = f_df.mask(f_df.isna(), None)
points_json = json.dumps(f_df_clean.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> 
        body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; font-family: sans-serif; }}
        #info-card {{
            position: absolute; top: 20px; right: 20px; width: 300px; max-height: 85vh;
            background: white; padding: 0; border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15); display: none; overflow-y: auto;
            z-index: 1000; border: 1px solid #eee;
        }}
        .card-img {{ width: 100%; height: 180px; object-fit: cover; border-top-left-radius: 15px; border-top-right-radius: 15px; }}
        .card-body {{ padding: 15px; }}
        .close-btn {{ position: absolute; top: 10px; right: 15px; cursor: pointer; color: white; font-size: 24px; text-shadow: 0 0 5px rgba(0,0,0,0.5); }}
        .card-title {{ font-weight: bold; color: #1a1a1a; margin-bottom: 5px; font-size: 1.1em; }}
        .card-meta {{ font-size: 0.85rem; color: #666; margin-bottom: 10px; }}
        .card-quote {{ font-size: 0.9rem; color: #333; font-style: italic; border-top: 1px solid #f0f0f0; padding-top: 10px; }}
    </style>
  </head>
  <body>
    <div id="info-card">
        <span class="close-btn" onclick="this.parentElement.style.display='none'">&times;</span>
        <div id="card-content"></div>
    </div>
    <div id="globeViz"></div>
    <script>
      const gData = {points_json};
      const infoCard = document.getElementById('info-card');
      const cardContent = document.getElementById('card-content');

      const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .pointsData(gData)
        .pointLat('lat').pointLng('lng').pointColor('Color').pointRadius(0.7).pointAltitude(0.02)
        .pointLabel(d => `<div style="padding: 4px; background: white; border-radius: 4px; color: black;">${{d.Title}}</div>`)
        .onPointClick(d => {{
            infoCard.style.display = 'block';
            const imgHtml = d.imageBase64 ? `<img class="card-img" src="${{d.imageBase64}}">` : `<div style="height:20px"></div>`;
            cardContent.innerHTML = `
                ${{imgHtml}}
                <div class="card-body">
                    <div class="card-title">${{d.Title}}</div>
                    <div class="card-meta"><b>${{d.Institution}}</b><br>📍 ${{d.Location}}</div>
                    <div class="card-quote">${{d['Pull Quotes'] || 'Project details available below.'}}</div>
                </div>
            `;
        }});
      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.5;
    </script>
  </body>
</html>
"""
components.html(globe_html, height=650)

# --- LIST VIEW ---
st.markdown("---")
st.subheader("📚 Detailed Project Stories")
for _, row in f_df.iterrows():
    with st.expander(f"📌 {row['Title']} — {row['Location']}"):
        col1, col2 = st.columns([2, 1])
        with col1:
            if pd.notna(row['Pull Quotes']): st.markdown(f"***{row['Pull Quotes']}***")
            st.write(f"**🏫 Institution:** {row['Institution']}")
            st.write(f"**🤝 Members:** {row['Members']}")
            st.write(f"**🎯 Issues:** {', '.join(row['All_Issues'])}")
        with col2:
            if row['imagePath']: st.image(row['imagePath'], use_container_width=True)
            else: st.info("No photo available")
        if pd.notna(row['Quote']): st.write(row['Quote'])
