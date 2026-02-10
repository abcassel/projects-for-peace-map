import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace", layout="wide")

# --- COLORS FOR RAINBOW EFFECT ---
# Map common issues to friendly colors
ISSUE_COLORS = {
    "Youth development": "#FF6B6B",      # Coral
    "Health & Well-being": "#FFD93D",    # Sunny Yellow
    "Art & Design": "#FF8E3C",           # Orange
    "Social Cohesion": "#6BCB77",        # Fresh Green
    "Education Quality": "#4D96FF",      # Sky Blue
    "Ag & Food Security": "#9ED5C5",     # Sage
    "default": "#B197FC"                 # Soft Purple
}

@st.cache_data
def load_data():
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    cols_to_fill = ['Title', 'Institution', 'Location', 'Coordinates', 
                    'Issue Primary', 'Approach Primary', 'Quote']
    df[cols_to_fill] = df[cols_to_fill].ffill()
    
    def parse_coords(c):
        try:
            lat, lon = str(c).split(',')
            return float(lat.strip()), float(lon.strip())
        except: return None, None
            
    df[['lat', 'lng']] = df['Coordinates'].apply(lambda x: pd.Series(parse_coords(x)))
    df = df.dropna(subset=['lat', 'lng'])
    
    # Assign colors based on Issue
    def get_color(issue):
        return ISSUE_COLORS.get(issue, ISSUE_COLORS["default"])
    
    project_df = df.groupby('Title').agg({
        'Institution': 'first',
        'Members': lambda x: ', '.join(x.astype(str)),
        'Location': 'first',
        'lat': 'first',
        'lng': 'first',
        'Issue Primary': 'first',
        'Quote': 'first'
    }).reset_index()
    
    project_df['color'] = project_df['Issue Primary'].apply(get_color)
    return project_df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("🌈 Filter Projects")
search_query = st.sidebar.text_input("Search by Keyword")
selected_inst = st.sidebar.multiselect("School", sorted(df['Institution'].unique()))

# Filter Logic
filtered_df = df.copy()
if search_query:
    filtered_df = filtered_df[filtered_df['Title'].str.contains(search_query, case=False)]
if selected_inst:
    filtered_df = filtered_df[filtered_df['Institution'].isin(selected_inst)]

# --- THE GLOBE COMPONENT ---
points_json = json.dumps(filtered_df.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> 
        body {{ 
            margin: 0; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); /* Bright Friendly Background */
            overflow: hidden; 
        }} 
    </style>
  </head>
  <body>
    <div id="globeViz"></div>
    <script>
      const gData = {points_json};

      const world = Globe()
        (document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg') // Brighter Earth
        .backgroundColor('rgba(0,0,0,0)') // Transparent to show the CSS gradient
        .htmlElementsData(gData)
        .htmlElement(d => {{
          const el = document.createElement('div');
          // Rainbow "Pulse" Pins
          el.innerHTML = `<div style="
            width: 16px; 
            height: 16px; 
            background: ${{d.color}}; 
            border-radius: 50%; 
            border: 2px solid white;
            box-shadow: 0 0 15px ${{d.color}};
            cursor: pointer;
          "></div>`;
          return el;
        }})
        .htmlLat(d => d.lat)
        .htmlLng(d => d.lng);

      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.8;
    </script>
  </body>
</html>
"""

st.title("Projects for Peace 🌍")
components.html(globe_html, height=650)

# --- LIST VIEW BELOW ---
st.subheader("Explore Projects")
cols = st.columns(2)
for i, row in filtered_df.iterrows():
    with cols[i % 2].expander(f"{row['Title']}"):
        st.write(f"**School:** {row['Institution']}")
        st.write(f"**Issue:** {row['Issue Primary']}")
        st.write(f"**Members:** {row['Members']}")
        st.caption(row['Quote'][:300] + "...")
