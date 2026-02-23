import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide")

# --- 1. REGION MAPPING & COLORS (Expanded with City/State Keywords) ---
REGION_MAP = {
    "Africa": [
        "Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Sierra Leone", 
        "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", 
        "Cameroon", "Zimbabwe", "Ethiopia", "Uganda", "Zambia", "Malawi", "Egypt",
        "Cacuaco", "Makeni", "Arusha", "Laikipia", "Kasungu", "Kigali", "Bugesera", 
        "Langa", "Lagos", "Lokichoggio", "Kiambu", "Accra", "Tonj", "Addis Ababa", 
        "Ouangolodougou", "Moamba", "Kadi'ba", "Kashusha", "Kisumu", "Nairobi", 
        "Akuse", "Bassar", "Johannesburg", "Matabeleland", "Gweru", "Niamey"
    ],
    "Asia": [
        "India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", 
        "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", 
        "Kyrgyzstan", "Vietnam", "Thailand", "Sri Lanka", "Singapore", "Mongolia",
        "Jaipur", "Islamabad", "Bayramaly", "Lalitpur", "Mughalpura", "Sindhuli", 
        "Yasin Ghizer", "Koshi", "Mustang", "Jiangsu", "Khagrachari", "Dili", 
        "Hokkaido", "Kachankawal", "Jakarta", "Zhalal-Abad", "Rangamati", "Vijayawada", 
        "Sulawesi", "Tokyo", "Phnom Penh", "Sibuyan", "Sankhatar", "Chakwal", 
        "Bali", "Chittagong", "Uttar Pradesh", "Punjab", "Dhaka"
    ],
    "Europe": [
        "Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Georgia", "Armenia", 
        "Kosovo", "Albania", "France", "Spain", "Epirus", "Bucharest", "Mainz", 
        "Skopje", "Chernivtsi"
    ],
    "North America": [
        "United States", "USA", "Canada", "Mexico", "Guatemala", "Honduras", "Haiti", 
        "Dominican Republic", "Jamaica", "Belize", "Toronto", "Baltimore", "Chicago", 
        "Maine", "Michigan", "Nashville", "San Bernardino", "Pennsylvania", "New York", 
        "Gainesville", "Boston", "North Carolina", "Oregon", "Pittsburgh", "Maryland", 
        "Oaxaca"
    ],
    "South America": [
        "Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Bolivia", 
        "Chile", "Paraguay", "Bahia", "Montevideo", "Medellín", "Planes-Mirador", 
        "Chimborazo", "Rio de Janeiro", "Concepcion", "Jacarezinho", "Quito", 
        "Colonia Suiza", "Pocrane"
    ],
    "Middle East": ["Syria", "Cairo"],
    "Oceania": ["Marshall Islands", "Kwajalein", "Fiji", "Samoa", "Vanuatu"]
}

REGION_COLORS = {
    "Africa": "#FF9F43", "Asia": "#FF6B6B", "Europe": "#4834D4",
    "North America": "#1DD1A1", "South America": "#FECA57",
    "Middle East": "#54a0ff", "Oceania": "#9B59B6", "Other": "#C8D6E5"
}

@st.cache_data
def load_data():
    # Load raw data
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    
    # 1. Fill missing values for merged rows
    cols_to_fill = ['Title', 'Institution', 'Location', 'Latitude', 'Longitude', 'Issue Primary', 'Approach Primary', 'Pull Quotes', 'Quote']
    df[cols_to_fill] = df[cols_to_fill].ffill()
    
    # 2. Assign Region based on keywords
    def get_region(loc):
        loc_str = str(loc)
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str.lower() for k in keywords): 
                return region
        return "Other"
    
    df['Region'] = df['Location'].apply(get_region)
    df['Color'] = df['Region'].apply(lambda r: REGION_COLORS.get(r, "#CCCCCC"))
    
    # 3. Process Tags (Issues and Approaches)
    def clean_tags(row, col_p, col_s):
        tags = [str(row[col_p]), str(row[col_s])]
        return [t.strip().title() for t in tags if pd.notna(t) and str(t).lower() != 'nan' and t.strip() != '']

    df['Issues_List'] = df.apply(lambda r: clean_tags(r, 'Issue Primary', 'Issue Secondary'), axis=1)
    df['Apps_List'] = df.apply(lambda r: clean_tags(r, 'Approach Primary', 'Approach Secondary'), axis=1)

    # 4. Aggregate individual student rows into project blocks
    project_df = df.groupby('Title').agg({
        'ID': 'first',
        'Institution': 'first', 
        'Members': lambda x: ', '.join([str(m) for m in x.unique() if pd.notna(m)]),
        'Location': 'first', 
        'Region': 'first', 
        'Color': 'first',
        'Latitude': 'first', 
        'Longitude': 'first',
        'Pull Quotes': 'first',
        'Quote': 'first'
    }).reset_index()
    
    # 5. Correct Mapping for Tags
    issues_map = df.groupby('Title')['Issues_List'].apply(lambda x: list(set([item for sublist in x for item in sublist])))
    apps_map = df.groupby('Title')['Apps_List'].apply(lambda x: list(set([item for sublist in x for item in sublist])))
    project_df['All_Issues'] = project_df['Title'].map(issues_map)
    project_df['All_Approaches'] = project_df['Title'].map(apps_map)
    
    # 6. DUAL-FORMAT IMAGE LOGIC
    # Checks for .jpg, .jpeg, or .png automatically
    def get_image_path(id_val):
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            path = f"images/{id_val}{ext}"
            if os.path.exists(path):
                return path
        return f"images/{id_val}.jpg" # Fallback path

    project_df['imageUrl'] = project_df['ID'].apply(get_image_path)
    
    # 7. Final preparation
    project_df = project_df.rename(columns={'Latitude': 'lat', 'Longitude': 'lng'})
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Search & Filter")
search_query = st.sidebar.text_input("Search Project/Student")

def get_filter_options(series_of_lists):
    flat_list = []
    for item_data in series_of_lists:
        if isinstance(item_data, list):
            for item in item_data:
                val = str(item).strip()
                if val and val.lower() != 'nan': flat_list.append(val)
    return sorted(list(set(flat_list)))

unique_inst = sorted([str(x).strip() for x in df['Institution'].unique() if pd.notna(x)])
unique_reg = sorted([str(x).strip() for x in df['Region'].unique() if pd.notna(x)])
unique_issues = get_filter_options(df['All_Issues'])
unique_apps = get_filter_options(df['All_Approaches'])

selected_inst = st.sidebar.multiselect("Institution / School", options=unique_inst)
selected_regions = st.sidebar.multiselect("World Region", options=unique_reg)
selected_issues = st.sidebar.multiselect("Issue Area", options=unique_issues)
selected_apps = st.sidebar.multiselect("Project Approach", options=unique_apps)

# --- APPLY FILTERS ---
f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions: f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst: f_df = f_df[f_df['Institution'].isin(selected_inst)]
if selected_issues: f_df = f_df[f_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues) if isinstance(x, list) else False)]
if selected_apps: f_df = f_df[f_df['All_Approaches'].apply(lambda x: any(a in x for a in selected_apps) if isinstance(x, list) else False)]

# --- GLOBE VISUALIZATION ---
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
            position: absolute; top: 20px; right: 20px; width: 320px; max-height: 80vh;
            background: rgba(255, 255, 255, 0.98); padding: 20px; border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2); display: none; overflow-y: auto;
            z-index: 1000; border: 1px solid #ddd;
        }}
        .close-btn {{ float: right; cursor: pointer; font-weight: bold; color: #888; font-size: 24px; }}
        .card-img {{ width: 100%; border-radius: 8px; margin-bottom: 12px; object-fit: cover; max-height: 200px; }}
        .card-title {{ font-weight: bold; color: black; margin-bottom: 8px; font-size: 1.2em; line-height: 1.2; }}
        .card-meta {{ font-size: 0.9rem; color: #444; margin-bottom: 15px; line-height: 1.5; }}
        .card-quote {{ font-size: 1rem; color: black; font-style: italic; border-top: 1px solid #eee; padding-top: 15px; line-height: 1.6; }}
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
        .pointLat('lat').pointLng('lng').pointColor('Color').pointRadius(0.8).pointAltitude(0.01)
        .pointLabel(d => `<div style="padding: 6px; background: white; border: 1px solid #ccc; border-radius: 4px; color: black; font-weight: bold;">${{d.Title}}</div>`)
        .onPointHover(point => {{ world.controls().autoRotate = !point; }})
        .onPointClick(d => {{
            infoCard.style.display = 'block';
            const displayQuote = d['Pull Quotes'] ? `"${{d['Pull Quotes']}}"` : 'Explore the project details below.';
            
            cardContent.innerHTML = `
                <img class="card-img" src="${{d.imageUrl}}" onerror="this.style.display='none'">
                <div class="card-title">${{d.Title}}</div>
                <div class="card-meta">
                    <b>${{d.Institution}}</b><br/>
                    📍 ${{d.Location}}<br/>
                    🤝 ${{d.Members}}
                </div>
                <div class="card-quote">
                    ${{displayQuote}}
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
            
            issues_str = ", ".join([str(i) for i in row['All_Issues'] if pd.notna(i)]) if isinstance(row['All_Issues'], list) else ""
            apps_str = ", ".join([str(a) for a in row['All_Approaches'] if pd.notna(a)]) if isinstance(row['All_Approaches'], list) else ""
            
            st.write(f"**🎯 Issues:** {issues_str}")
            st.write(f"**🛠 Approaches:** {apps_str}")

        with col2:
            if os.path.exists(row['imageUrl']):
                st.image(row['imageUrl'], use_container_width=True)
            else:
                st.info("Photo not found.")

        if pd.notna(row['Quote']): 
            st.markdown("---")
            st.write(row['Quote'])
