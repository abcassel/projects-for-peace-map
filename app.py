import streamlit as st
import pandas as pd
import json
import random
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace", layout="wide")

# --- REGION MAPPING & COLORS ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Burkina Faso", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Cacuaco", "Makeni", "Arusha", "Kigali", "Lagos", "Accra", "Addis Ababa", "Johannesburg", "Ethiopia", "Congo"],
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
    project_df['All_Approaches'] = project_df.apply(lambda x: list(set(filter(pd.notna, [x['Approach Primary'], x['Approach Secondary']]))), axis=1)
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- STATE MANAGEMENT ---
if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = None
if 'view_lat' not in st.session_state:
    st.session_state.view_lat = 20
if 'view_lng' not in st.session_state:
    st.session_state.view_lng = 0

# --- SIDEBAR ---
st.sidebar.header("🔍 Search & Discover")
search_query = st.sidebar.text_input("Search by Project or Student Name")
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
    <style> 
        body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; font-family: sans-serif; }}
        .custom-tooltip {{
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.95);
            color: #333;
            border-radius: 6px;
            border: 1px solid #ddd;
            font-size: 13px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            pointer-events: none;
            position: absolute;
            transform: translate(-50%, -120%);
            z-index: 9999;
        }}
    </style>
  </head>
  <body>
    <div id="globeViz"></div>
    <script>
      const gData = {points_json};
      const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .htmlElementsData(gData)
        .htmlElement(d => {{
          const el = document.createElement('div');
          
          // The Glowing Marker
          el.innerHTML = `<div style="
            width: 14px; 
            height: 14px; 
            background: ${{d.Color}}; 
            border-radius: 50%; 
            border: 2px solid white;
            box-shadow: 0 0 20px 6px ${{d.Color}};
            cursor: pointer;
          "></div>`;
          
          // CLICK: Send project title to Streamlit
          el.onclick = () => {{
             window.parent.postMessage({{type: 'streamlit:setComponentValue', value: d.Title}}, '*');
          }};
          
          // HOVER: Stop rotation and show label
          el.onmouseenter = () => {{
             world.controls().autoRotate = false;
             const label = document.createElement('div');
             label.className = 'custom-tooltip';
             label.id = 'tt-' + d.lat.toString().replace('.', '');
             label.innerHTML = `<b>${{d.Title}}</b><br/>${{d.Institution}}`;
             el.appendChild(label);
          }};

          // LEAVE: Resume rotation and hide label
          el.onmouseleave = () => {{
             world.controls().autoRotate = true;
             const label = el.querySelector('.custom-tooltip');
             if (label) el.removeChild(label);
          }};

          return el;
        }})
        .htmlLat(d => d.lat)
        .htmlLng(d => d.lng);

      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.7;

      // Handle Surprise Me Zoom
      if ("{st.session_state.selected_project_id}" !== "None") {{
          world.pointOfView({{ lat: {st.session_state.view_lat}, lng: {st.session_state.view_lng}, altitude: 1.8 }}, 1200);
      }}
    </script>
  </body>
</html>
"""

# Capture clicking
components.html(globe_html, height=600)

# --- FEATURED SECTION ---
if st.session_state.selected_project_id:
    res = df[df['Title'] == st.session_state.selected_project_id]
    if not res.empty:
        row = res.iloc[0]
        st.success(f"### ✨ Selected Project: {row['Title']}")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**🏫 Institution:** {row['Institution']}")
            st.write(f"**📍 Location:** {row['Location']}")
            st.write(f"**🤝 Members:** {row['Members']}")
            if st.button("✖️ Reset View"):
                st.session_state.selected_project_id = None
                st.rerun()
        with col2:
            st.info(f"**The Story:**\n\n{row['Quote']}")

st.markdown("---")

# --- LIST ---
st.subheader("📚 Explore All Projects")
for _, row in f_df.iterrows():
    with st.expander(f"📌 {row['Title']} ({row['Location']})"):
        st.write(f"**🏫 Institution:** {row['Institution']}")
        st.write(f"**🤝 Members:** {row['Members']}")
        st.write(f"**🎯 Issues:** {', '.join(row['All_Issues'])}")
        st.write(row['Quote'])



