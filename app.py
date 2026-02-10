import streamlit as st
import pandas as pd
import json
import random
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace", layout="wide")

# --- REGION MAPPING & COLORS ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Burkina Faso", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Cacuaco", "Makeni", "Arusha", "Kigali", "Lagos", "Accra", "Addis Ababa", "Johannesburg"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Jaipur", "Islamabad", "Dhaka", "Tokyo", "Phnom Penh", "Jakarta", "Bali"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Epirus", "Bucharest", "Mainz", "Skopje", "Georgia"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Toronto", "NYC", "New York", "Chicago", "Baltimore", "Oaxaca"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Medellin", "Rio de Janeiro", "Quito"],
    "Oceania": ["Marshall Islands", "Kwajalein"]
}

REGION_COLORS = {
    "Africa": "#FF9F43", "Asia": "#FF6B6B", "Europe": "#4834D4",
    "North America": "#1DD1A1", "South America": "#FECA57",
    "Oceania": "#9B59B6", "Other": "#C8D6E5"
}

@st.cache_data
def load_data():
    # Load your specific CSV
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    cols_to_fill = ['Title', 'Institution', 'Location', 'Coordinates', 'Issue Primary', 'Issue Secondary', 'Approach Primary', 'Approach Secondary', 'Quote']
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
    
    project_df = df.groupby('Title').agg({
        'Institution': 'first', 'Members': lambda x: ', '.join(x.astype(str)),
        'Location': 'first', 'Region': 'first', 'Color': 'first',
        'lat': 'first', 'lng': 'first', 'Issue Primary': 'first',
        'Issue Secondary': 'first', 'Approach Primary': 'first',
        'Approach Secondary': 'first', 'Quote': 'first'
    }).reset_index()
    
    # Create alphanumeric ID for HTML anchoring
    project_df['anchor_id'] = project_df['Title'].str.replace(r'[^a-zA-Z0-9]', '', regex=True)
    project_df['All_Issues'] = project_df.apply(lambda x: list(set(filter(pd.notna, [x['Issue Primary'], x['Issue Secondary']]))), axis=1)
    project_df['All_Approaches'] = project_df.apply(lambda x: list(set(filter(pd.notna, [x['Approach Primary'], x['Approach Secondary']]))), axis=1)
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- STATE ---
if 'view_lat' not in st.session_state: st.session_state.view_lat = 20
if 'view_lng' not in st.session_state: st.session_state.view_lng = 0
if 'scroll_to' not in st.session_state: st.session_state.scroll_to = None

# --- SIDEBAR ---
st.sidebar.header("🔍 Search & Filter")
search_query = st.sidebar.text_input("Search Project/Student")
selected_inst = st.sidebar.multiselect("Institution / School", sorted(df['Institution'].unique()))
selected_regions = st.sidebar.multiselect("World Region", sorted(df['Region'].unique()))
selected_issues = st.sidebar.multiselect("Issue Area", sorted(list(set([i for sub in df['All_Issues'] for i in sub]))))
selected_apps = st.sidebar.multiselect("Project Approach", sorted(list(set([a for sub in df['All_Approaches'] for a in sub]))))

st.sidebar.markdown("---")
if st.sidebar.button("🎲 Visit a Project at random"):
    random_row = df.sample(n=1).iloc[0]
    st.session_state.view_lat = random_row['lat']
    st.session_state.view_lng = random_row['lng']
    st.session_state.scroll_to = random_row['anchor_id']

# --- FILTERING ---
f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions: f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst: f_df = f_df[f_df['Institution'].isin(selected_inst)]
if selected_issues: f_df = f_df[f_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues))]
if selected_apps: f_df = f_df[f_df['All_Approaches'].apply(lambda x: any(a in x for a in selected_apps))]

# --- GLOBE ---
st.title("Projects for Peace 🌍")
points_json = json.dumps(f_df.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> 
        body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; font-family: sans-serif; }}
        #info-card {{
            position: absolute; top: 20px; right: 20px; width: 280px; max-height: 70vh;
            background: rgba(255, 255, 255, 0.98); padding: 18px; border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12); display: none; overflow-y: auto;
            z-index: 1000; border: 1px solid #eee;
        }}
        .close-btn {{ float: right; cursor: pointer; font-weight: bold; color: #aaa; font-size: 20px; }}
        .card-title {{ font-weight: bold; color: #2c3e50; margin-bottom: 5px; font-size: 1.1em; }}
        .card-text {{ font-size: 0.85rem; color: #555; line-height: 1.4; }}
    </style>
  </head>
  <body>
    <div id="info-card">
        <span class="close-btn" onclick="this.parentElement.style.display='none'">&times;</span>
        <div id="card-content" class="card-text"></div>
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
        .pointLat('lat').pointLng('lng').pointColor('Color').pointRadius(0.7).pointAltitude(0.01)
        .pointLabel(d => `<div style="padding: 4px; background: white; border: 1px solid #ccc; border-radius: 3px;"><b>${{d.Title}}</b></div>`)
        .onPointHover(point => {{ world.controls().autoRotate = !point; }})
        .onPointClick(d => {{
            infoCard.style.display = 'block';
            cardContent.innerHTML = `<div class="card-title">${{d.Title}}</div>
                                     <b>${{d.Institution}}</b><br/>
                                     <small>📍 ${{d.Location}}</small><br/><br/>
                                     <i>"${{d.Quote.substring(0, 400)}}..."</i>`;
        }});

      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.6;
      world.pointOfView({{ lat: {st.session_state.view_lat}, lng: {st.session_state.view_lng}, altitude: 1.8 }}, 1000);
    </script>
  </body>
</html>
"""

components.html(globe_html, height=600)

# JS Scroll Trigger for the "Random" button
if st.session_state.scroll_to:
    components.html(f"""
        <script>
            window.parent.document.getElementById('{st.session_state.scroll_to}').scrollIntoView({{behavior: 'smooth'}});
        </script>
    """, height=0)
    st.session_state.scroll_to = None

st.markdown("---")

# --- LIST VIEW ---
st.subheader("📚 Explore All Project Descriptions")
for _, row in f_df.iterrows():
    st.markdown(f'<div id="{row["anchor_id"]}"></div>', unsafe_content_allowed=True)
    with st.expander(f"📌 {row['Title']} ({row['Location']})"):
        st.write(f"**🏫 Institution:** {row['Institution']}")
        st.write(f"**🤝 Members:** {row['Members']}")
        st.write(f"**🛠 Approach:** {', '.join(row['All_Approaches'])}")
        st.write(row['Quote'])
