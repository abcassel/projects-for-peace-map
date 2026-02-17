import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide")

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
    # Added new columns to ffill list
    cols_to_fill = ['Title', 'Institution', 'Location', 'Coordinates', 'Issue Primary', 'Approach Primary', 'Pull Quote', 'Card Photo', 'Quote']
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
    
    # Aggregate data with Pull Quote and Photo
    project_df = df.groupby('Title').agg({
        'Institution': 'first', 
        'Members': lambda x: ', '.join(x.astype(str)),
        'Location': 'first', 
        'Region': 'first', 
        'Color': 'first',
        'lat': 'first', 
        'lng': 'first',
        'Pull Quote': 'first',
        'Card Photo': 'first',
        'Quote': 'first'
    }).reset_index()
    
    project_df['All_Issues'] = df.groupby('Title')['Issue Primary'].apply(lambda x: list(set(filter(pd.notna, x))))
    project_df['All_Approaches'] = df.groupby('Title')['Approach Primary'].apply(lambda x: list(set(filter(pd.notna, x))))
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR FILTERS (Random button removed) ---
st.sidebar.header("🔍 Search & Filter")
search_query = st.sidebar.text_input("Search Project/Student")
selected_inst = st.sidebar.multiselect("Institution / School", sorted(df['Institution'].unique()))
selected_regions = st.sidebar.multiselect("World Region", sorted(df['Region'].unique()))
selected_issues = st.sidebar.multiselect("Issue Area", sorted(list(set([i for sub in df['All_Issues'] for i in sub]))))
selected_apps = st.sidebar.multiselect("Project Approach", sorted(list(set([a for sub in df['All_Approaches'] for a in sub]))))

# --- FILTER LOGIC ---
f_df = df.copy()
if search_query:
    f_df = f_df[f_df['Title'].str.contains(search_query, case=False) | f_df['Members'].str.contains(search_query, case=False)]
if selected_regions: f_df = f_df[f_df['Region'].isin(selected_regions)]
if selected_inst: f_df = f_df[f_df['Institution'].isin(selected_inst)]
if selected_issues: f_df = f_df[f_df['All_Issues'].apply(lambda x: any(i in x for i in selected_issues))]
if selected_apps: f_df = f_df[f_df['All_Approaches'].apply(lambda x: any(a in x for a in selected_apps))]

# --- GLOBE VISUALIZATION ---
st.title("Projects for Peace 🌍")
points_json = json.dumps(f_df.to_dict(orient='records'))

globe_html = f"""
<html>
  <head>
    <script src="//unpkg.com/globe.gl"></script>
    <style> 
        body {{ margin: 0; background: linear-gradient(to bottom, #ffffff, #e3f2fd); overflow: hidden; font-family: sans-serif; }}
        #info-card {{
            position: absolute; top: 20px; right: 20px; width: 350px; max-height: 85vh;
            background: rgba(255, 255, 255, 0.98); padding: 0; border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15); display: none; overflow-y: auto;
            z-index: 1000; border: 1px solid #eee;
        }}
        .card-img {{ width: 100%; height: 200px; object-fit: cover; border-top-left-radius: 12px; border-top-right-radius: 12px; }}
        .card-body {{ padding: 20px; }}
        .close-btn {{ position: absolute; top: 10px; right: 15px; cursor: pointer; font-weight: bold; color: white; font-size: 24px; text-shadow: 0 0 5px rgba(0,0,0,0.5); z-index: 1001; }}
        .card-title {{ font-weight: bold; color: black; margin-bottom: 5px; font-size: 1.2em; line-height: 1.2; }}
        .card-meta {{ font-size: 0.85rem; color: black; margin-bottom: 12px; line-height: 1.4; }}
        .card-quote {{ font-size: 0.95rem; color: black; font-style: italic; border-top: 1px solid #eee; padding-top: 12px; line-height: 1.5; }}
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
        .pointLabel(d => `<div style="padding: 6px; background: white; border: 1px solid #ccc; border-radius: 4px; color: black;"><b>${{d.Title}}</b></div>`)
        .onPointHover(point => {{ world.controls().autoRotate = !point; }})
        .onPointClick(d => {{
            infoCard.style.display = 'block';
            const photoHtml = d['Card Photo'] ? `<img src="${{d['Card Photo']}}" class="card-img">` : '<div style="height:20px;"></div>';
            cardContent.innerHTML = `
                ${{photoHtml}}
                <div class="card-body">
                    <div class="card-title">${{d.Title}}</div>
                    <div class="card-meta">
                        <b>${{d.Institution}}</b><br/>
                        📍 ${{d.Location}}<br/>
                        🤝 ${{d.Members}}
                    </div>
                    <div class="card-quote">
                        "${{d['Pull Quote']}}"
                    </div>
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
st.subheader("📚 Full Project Descriptions")
for _, row in f_df.iterrows():
    with st.expander(f"📌 {row['Title']} ({row['Location']})"):
        st.write(f"**🏫 Institution:** {row['Institution']}")
        st.write(f"**🤝 Members:** {row['Members']}")
        st.write(f"**🛠 Approach:** {', '.join(row['All_Approaches'])}")
        st.write(row['Quote'])
