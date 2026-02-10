import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace - Interactive Globe", layout="wide")

# --- DATA LOADING & CLEANING ---
@st.cache_data
def load_data():
    # Load your specific file
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    
    # 1. Fill down project details for rows with multiple members
    cols_to_fill = ['ID', 'Title', 'Institution', 'Location', 'Coordinates', 
                    'Issue Primary', 'Issue Secondary', 'Approach Primary', 
                    'Approach Secondary', 'Youth Focused?', 'Quote']
    df[cols_to_fill] = df[cols_to_fill].ffill()
    
    # 2. Parse Coordinates
    def parse_coords(c):
        try:
            lat, lon = str(c).split(',')
            return float(lat.strip()), float(lon.strip())
        except:
            return None, None
            
    df[['lat', 'lng']] = df['Coordinates'].apply(lambda x: pd.Series(parse_coords(x)))
    df = df.dropna(subset=['lat', 'lng'])
    
    # 3. Consolidate members into a single string per project for searching
    # We group by Title so all members of the same project appear in one pin
    agg_dict = {
        'Institution': 'first',
        'Members': lambda x: ', '.join(x.astype(str)),
        'Location': 'first',
        'lat': 'first',
        'lng': 'first',
        'Issue Primary': 'first',
        'Issue Secondary': 'first',
        'Approach Primary': 'first',
        'Approach Secondary': 'first',
        'Quote': 'first'
    }
    project_df = df.groupby('Title').agg(agg_dict).reset_index()
    
    # Create combined lists for filtering
    project_df['All_Issues'] = project_df.apply(lambda x: [i for i in [x['Issue Primary'], x['Issue Secondary']] if pd.notna(i)], axis=1)
    project_df['All_Approaches'] = project_df.apply(lambda x: [a for a in [x['Approach Primary'], x['Approach Secondary']] if pd.notna(a)], axis=1)
    
    return project_df

df = load_data()

# --- SIDEBAR / FILTERS ---
st.sidebar.title("🔍 Search Projects")

# Search by Keywords (Title or Members)
search_query = st.sidebar.text_input("Search by Title or Member Name")

# Dropdown Filters
all_institutions = sorted(df['Institution'].unique())
selected_inst = st.sidebar.multiselect("School / Institution", all_institutions)

# Unique values for Issues and Approaches (flattening the lists)
all_issues = sorted(list(set([item for sublist in df['All_Issues'] for item in sublist])))
selected_issues = st.sidebar.multiselect("Issues Addressed", all_issues)

all_approaches = sorted(list(set([item for sublist in df['All_Approaches'] for item in sublist])))
selected_approaches = st.sidebar.multiselect("Project Approach", all_approaches)

# --- FILTERING LOGIC ---
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df['Title'].str.contains(search_query, case=False, na=False) | 
        filtered_df['Members'].str.contains(search_query, case=False, na=False)
    ]

if selected_inst:
    filtered_df = filtered_df[filtered_df['Institution'].isin(selected_inst)]

if selected_issues:
    filtered_df = filtered_df[filtered_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues))]

if selected_approaches:
    filtered_df = filtered_df[filtered_df['All_Approaches'].apply(lambda x: any(a in x for a in selected_approaches))]

# --- 3D GLOBE VISUALIZATION ---
st.title("Projects for Peace 2025")
st.write(f"Showing {len(filtered_df)} projects across the globe. Click a pin to see details.")

# Convert dataframe to JSON for the Javascript Globe
points_data = filtered_df.to_dict(orient='records')
points_json = json.dumps(points_data)

# HTML/JS for Globe.gl
globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> body {{ margin: 0; background: #000; overflow: hidden; }} </style>
  </head>
  <body>
    <div id="globeViz"></div>
    <script>
      const gData = {points_json};

      const world = Globe()
        (document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .htmlElementsData(gData)
        .htmlElement(d => {{
          const el = document.createElement('div');
          el.innerHTML = `<div style="width: 12px; height: 12px; background: #00ffcc; border-radius: 50%; cursor: pointer; border: 2px solid white; box-shadow: 0 0 10px #00ffcc;"></div>`;
          el.style.color = 'white';
          el.style['pointer-events'] = 'auto';
          el.onclick = () => window.parent.postMessage({{type: 'project_click', data: d}}, '*');
          return el;
        }})
        .htmlLat(d => d.lat)
        .htmlLng(d => d.lng)
        .pointLabel(d => `<b>${{d.Title}}</b><br/>${{d.Institution}}<br/>${{d.Location}}`);

      // Auto-rotate
      world.controls().autoRotate = true;
      world.controls().autoRotateSpeed = 0.5;

    </script>
  </body>
</html>
"""

components.html(globe_html, height=600)

# --- DETAIL PANEL ---
# This section allows users to view the list of filtered projects in detail below the map
if not filtered_df.empty:
    st.subheader("Project Details")
    for _, row in filtered_df.iterrows():
        with st.expander(f"{row['Title']} ({row['Institution']})"):
            st.markdown(f"**📍 Location:** {row['Location']}")
            st.markdown(f"**👥 Members:** {row['Members']}")
            st.markdown(f"**🛠 Approaches:** {', '.join(row['All_Approaches'])}")
            st.markdown(f"**🎯 Issues:** {', '.join(row['All_Issues'])}")
            if pd.notna(row['Quote']):
                st.info(f"**Project Summary:**\n\n {row['Quote']}")
else:
    st.warning("No projects match your search criteria.")
