import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide")

# --- REGION MAPPING & COLORS ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Burkina Faso", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Ethiopia", "Uganda", "Zambia", "Malawi"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Vietnam", "Thailand", "Sri Lanka"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Georgia", "Armenia", "Kosovo", "Albania", "France", "Spain"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Guatemala", "Honduras", "Haiti", "Dominican Republic", "Jamaica", "Belize"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Bolivia", "Chile", "Paraguay"],
    "Oceania": ["Marshall Islands", "Kwajalein", "Fiji", "Samoa", "Vanuatu"]
}

REGION_COLORS = {
    "Africa": "#FF9F43", "Asia": "#FF6B6B", "Europe": "#4834D4",
    "North America": "#1DD1A1", "South America": "#FECA57",
    "Oceania": "#9B59B6", "Other": "#C8D6E5"
}

@st.cache_data
def load_data():
    # Load your CSV file
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    
    # Using 'Pull Quotes' with an S as discussed
    cols_to_fill = ['Title', 'Institution', 'Location', 'Coordinates', 'Issue Primary', 'Approach Primary', 'Pull Quotes', 'Quote']
    df[cols_to_fill] = df[cols_to_fill].ffill()
    
    def parse_coords(c):
        try:
            lat, lon = str(c).split(',')
            return float(lat.strip()), float(lon.strip())
        except: return None, None
    df[['lat', 'lng']] = df['Coordinates'].apply(lambda x: pd.Series(parse_coords(x)))
    
    def get_region(loc):
        loc_str = str(loc)
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str.lower() for k in keywords): return region
        return "Other"
    
    df['Region'] = df['Location'].apply(get_region)
    df['Color'] = df['Region'].apply(lambda r: REGION_COLORS.get(r, "#CCCCCC"))
    
    # Aggregate data into one row per Project Title
    project_df = df.groupby('Title').agg({
        'Institution': 'first', 
        'Members': lambda x: ', '.join(x.astype(str).unique()),
        'Location': 'first', 
        'Region': 'first', 
        'Color': 'first',
        'lat': 'first', 
        'lng': 'first',
        'Pull Quotes': 'first',
        'Quote': 'first'
    }).reset_index()
    
    project_df['All_Issues'] = df.groupby('Title')['Issue Primary'].apply(lambda x: list(set(filter(pd.notna, x))))
    project_df['All_Approaches'] = df.groupby('Title')['Approach Primary'].apply(lambda x: list(set(filter(pd.notna, x))))
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Search & Filter")
search_query = st.sidebar.text_input("Search Project/Student")
selected_inst = st.sidebar.multiselect("Institution / School", sorted(df['Institution'].unique()))
selected_regions = st.sidebar.multiselect("World Region", sorted(df['Region'].unique()))
selected_issues = st.sidebar.multiselect("Issue Area", sorted(list(set([i for sub in df['All_Issues'] for i in sub]))))
selected_apps = st.sidebar.multiselect("Project Approach", sorted(list(set([a for sub in df['All_Approaches'] for a in sub]))))

# --- APPLY FILTERS ---
f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions: f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst: f_df = f_df[f_df['Institution'].isin(selected_inst)]
if selected_issues: f_df = f_df[f_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues))]
if selected_apps: f_df = f_df[f_df['All_Approaches'].apply(lambda x: any(a in x for a in selected_apps))]

# --- GLOBE SECTION ---
st.title("Projects for Peace 🌍")
points_json = json.dumps(f_df.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> 
        body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; font-family: sans-serif; }}
        #info-card {{
            position: absolute; top: 20px; right: 20px; width: 300px; max-height: 80vh;
            background: rgba(255, 255, 255, 0.98); padding: 20px; border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2); display: none; overflow-y: auto;
            z-index: 1000; border: 1px solid #ddd;
        }}
        .close-btn {{ float: right; cursor: pointer; font-weight: bold; color: #888; font-size: 24px; }}
        .card-title {{ font-weight: bold; color: black; margin-bottom: 8px; font-size: 1.2em; line-height: 1.2; }}
        .card-meta {{ font-size: 0.9rem; color: black; margin-bottom: 15px; line-height: 1.5; }}
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
            cardContent.innerHTML = `
                <div class="card-title">${{d.Title}}</div>
                <div class="card-meta">
                    <b>${{d.Institution}}</b><br/>
                    📍 ${{d.Location}}<br/>
                    🤝 ${{d.Members}}
                </div>
                <div class="card-quote">
                    "${{d['Pull Quotes']}}"
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
        st.markdown(f"***{row['Pull Quotes']}***")
        st.write(f"**🏫 Institution:** {row['Institution']}")
        st.write(f"**🤝 Members:** {row['Members']}")
        st.write(row['Quote'])
