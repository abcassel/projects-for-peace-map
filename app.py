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
    
    project_df['All_Issues'] = project_df.apply(lambda x: list(set(filter(pd.notna, [x['Issue Primary'], x['Issue Secondary']]))), axis=1)
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- STATE ---
if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = None
if 'view_lat' not in st.session_state:
    st.session_state.view_lat = 20
if 'view_lng' not in st.session_state:
    st.session_state.view_lng = 0

# --- SIDEBAR ---
st.sidebar.header("🔍 Search & Discover")
search_query = st.sidebar.text_input("Search Project/Student")
all_inst = sorted(df['Institution'].unique())
selected_inst = st.sidebar.multiselect("Institution / School", all_inst)

if st.sidebar.button("🎲 Surprise Me!"):
    random_row = df.sample(n=1).iloc[0]
    st.session_state.selected_project_id = random_row['Title']
    st.session_state.view_lat = random_row['lat']
    st.session_state.view_lng = random_row['lng']

st.sidebar.markdown("---")
selected_regions = st.sidebar.multiselect("World Region", sorted(df['Region'].unique()))
selected_issues = st.sidebar.multiselect("Issue Area", sorted(list(set([i for sub in df['All_Issues'] for i in sub]))))

# --- FILTERING ---
f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions: f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst: f_df = f_df[f_df['Institution'].isin(selected_inst)]
if selected_issues: f_df = f_df[f_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues))]

# --- GLOBE ---
st.title("Projects for Peace 🌍")
points_json = json.dumps(f_df.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; }} </style>
  </head>
  <body>
    <div id="globeViz"></div>
    <script>
      const gData = {points_json};
      const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .pointsData(gData)
        .pointLat('lat')
        .pointLng('lng')
        .pointColor('Color')
        .pointRadius(0.7)
        .pointAltitude(0.01)
        // HOVER LABEL
        .pointLabel(d => `<div style="padding: 8px; background: white; color: black; border-radius: 4px; border: 1px solid #ccc; font-family: sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <b>${{d.Title}}</b><br/>${{d.Institution}}
                          </div>`)
        // STOP ON HOVER
        .onPointHover(point => {{
          world.controls().autoRotate = !point;
        }})
        // CLICK TO SELECT
        .onPointClick(d => {{
          window.parent.postMessage({{type: 'streamlit:setComponentValue', value: d.Title}}, '*');
        }});

      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.6;

      if ("{st.session_state.selected_project_id}" !== "None") {{
          world.pointOfView({{ lat: {st.session_state.view_lat}, lng: {st.session_state.view_lng}, altitude: 1.8 }}, 1000);
      }}
    </script>
  </body>
</html>
"""

components.html(globe_html, height=600)

# --- FEATURED SECTION ---
if st.session_state.selected_project_id:
    res = df[df['Title'] == st.session_state.selected_project_id]
    if not res.empty:
        row = res.iloc[0]
        st.info(f"### ✨ Selected Project: {row['Title']}")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**🏫 Institution:** {row['Institution']}")
            st.write(f"**📍 Location:** {row['Location']}")
            st.write(f"**🤝 Members:** {row['Members']}")
            if st.button("✖️ Clear & Resume Exploring"):
                st.session_state.selected_project_id = None
                st.rerun()
        with col2:
            st.write(f"**The Story:**\n\n{row['Quote']}")

st.markdown("---")

# --- LIST VIEW ---
st.subheader("📚 All Projects")
for _, row in f_df.iterrows():
    with st.expander(f"📌 {row['Title']} ({row['Location']})"):
        st.write(f"**🏫 Institution:** {row['Institution']}")
        st.write(f"**🤝 Members:** {row['Members']}")
        st.write(row['Quote'])




