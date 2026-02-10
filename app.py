import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace", layout="wide")

# --- REGION MAPPING & COLORS ---
# Mapping keywords in the "Location" column to global regions
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Burkina Faso", "Sierra Leone", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Cacuaco", "Makeni", "Arusha", "Kigali", "Lagos", "Accra", "Addis Ababa", "Johannesburg"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Jaipur", "Islamabad", "Dhaka", "Tokyo", "Phnom Penh", "Jakarta", "Bali"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Epirus", "Bucharest", "Mainz", "Skopje"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Toronto", "NYC", "New York", "Chicago", "Baltimore", "Oaxaca"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Medellin", "Rio de Janeiro", "Quito"],
    "Oceania": ["Marshall Islands", "Kwajalein"]
}

REGION_COLORS = {
    "Africa": "#FF9F43",        # Vibrant Orange
    "Asia": "#FF6B6B",          # Soft Red
    "Europe": "#4834D4",        # Deep Blue
    "North America": "#1DD1A1", # Bright Teal
    "South America": "#FECA57", # Warm Yellow
    "Oceania": "#9B59B6",       # Amethyst Purple
    "Other": "#C8D6E5"          # Grey
}

@st.cache_data
def load_data():
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    
    # Clean and Fill
    cols_to_fill = ['Title', 'Institution', 'Location', 'Coordinates', 
                    'Issue Primary', 'Issue Secondary', 'Approach Primary', 
                    'Approach Secondary', 'Quote']
    df[cols_to_fill] = df[cols_to_fill].ffill()
    
    # Coordinate Parsing
    def parse_coords(c):
        try:
            lat, lon = str(c).split(',')
            return float(lat.strip()), float(lon.strip())
        except: return None, None
    df[['lat', 'lng']] = df['Coordinates'].apply(lambda x: pd.Series(parse_coords(x)))
    
    # Assign Regions
    def get_region(loc):
        loc_str = str(loc)
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str.lower() for k in keywords):
                return region
        return "Other"
    
    df['Region'] = df['Location'].apply(get_region)
    df['Color'] = df['Region'].apply(lambda r: REGION_COLORS.get(r, "#CCCCCC"))
    
    # Group by Title to consolidate members
    project_df = df.groupby('Title').agg({
        'Institution': 'first',
        'Members': lambda x: ', '.join(x.astype(str)),
        'Location': 'first',
        'Region': 'first',
        'Color': 'first',
        'lat': 'first',
        'lng': 'first',
        'Issue Primary': 'first',
        'Issue Secondary': 'first',
        'Approach Primary': 'first',
        'Approach Secondary': 'first',
        'Quote': 'first'
    }).reset_index()
    
    # Helper lists for filtering
    project_df['All_Issues'] = project_df.apply(lambda x: list(set(filter(pd.notna, [x['Issue Primary'], x['Issue Secondary']]))), axis=1)
    project_df['All_Approaches'] = project_df.apply(lambda x: list(set(filter(pd.notna, [x['Approach Primary'], x['Approach Secondary']]))), axis=1)
    
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR SEARCH & FILTERS ---
st.sidebar.header("🔍 Search & Filter")

# 1. Search by Name (Project or Student)
search_query = st.sidebar.text_input("Search by Project or Student Name")

# 2. Filter by Region
all_regions = sorted(df['Region'].unique())
selected_regions = st.sidebar.multiselect("World Region", all_regions)

# 3. Filter by Institution
all_inst = sorted(df['Institution'].unique())
selected_inst = st.sidebar.multiselect("Institution", all_inst)

# 4. Filter by Issue
all_issues = sorted(list(set([i for sub in df['All_Issues'] for i in sub])))
selected_issues = st.sidebar.multiselect("Issue Area", all_issues)

# 5. Filter by Approach
all_apps = sorted(list(set([a for sub in df['All_Approaches'] for a in sub])))
selected_apps = st.sidebar.multiselect("Project Approach", all_apps)

# --- FILTER LOGIC ---
f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions:
    f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst:
    f_df = f_df[f_df['Institution'].isin(selected_inst)]
if selected_issues:
    f_df = f_df[f_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues))]
if selected_apps:
    f_df = f_df[f_df['All_Approaches'].apply(lambda x: any(a in x for a in selected_apps))]

# --- GLOBE VISUALIZATION ---
st.title("Projects for Peace 🌍")
st.markdown(f"**Found {len(f_df)} projects.** Hover over a dot to see the title.")

points_json = json.dumps(f_df.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> 
        body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; }} 
    </style>
  </head>
  <body>
    <div id="globeViz"></div>
    <script>
      const gData = {points_json};

      const world = Globe()
        (document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .pointsData(gData)
        .pointLat(d => d.lat)
        .pointLng(d => d.lng)
        .pointColor(d => d.Color)
        .pointRadius(0.6)
        .pointAltitude(0.01)
        .pointLabel(d => `<div style="padding: 8px; background: white; color: black; border-radius: 4px; border: 1px solid #ccc; font-family: sans-serif;">
                            <strong>${{d.Title}}</strong><br/>
                            <small>${{d.Institution}} | ${{d.Location}}</small>
                          </div>`)
        .onPointClick(d => window.parent.postMessage({{type: 'click', title: d.Title}}, '*'));

      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.6;
    </script>
  </body>
</html>
"""

components.html(globe_html, height=600)

# --- EXPANDABLE LIST ---
if not f_df.empty:
    st.subheader("Project Details")
    for _, row in f_df.iterrows():
        with st.expander(f"{row['Title']} — {row['Location']}"):
            st.write(f"**Region:** {row['Region']}")
            st.write(f"**Institution:** {row['Institution']}")
            st.write(f"**Members:** {row['Members']}")
            st.write(f"**Approach:** {', '.join(row['All_Approaches'])}")
            st.info(row['Quote'])
