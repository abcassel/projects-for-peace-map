import streamlit as st
import pandas as pd
import json
import os
import base64
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace 2025", layout="wide", page_icon="🌍")

# --- MAPPINGS & STYLING ---
REGION_MAP = {
    "Africa": ["Angola", "Kenya", "Nigeria", "Ghana", "Tanzania", "Rwanda", "Sierra Leone", "South Sudan", "South Africa", "Mozambique", "Senegal", "Togo", "Niger", "Cameroon", "Zimbabwe", "Ethiopia", "Uganda", "Zambia", "Malawi", "Egypt"],
    "Asia": ["India", "Pakistan", "Afghanistan", "Bangladesh", "Nepal", "Turkmenistan", "China", "Japan", "Malaysia", "Cambodia", "Indonesia", "Philippines", "Bhutan", "Kyrgyzstan", "Vietnam", "Thailand", "Sri Lanka"],
    "Europe": ["Greece", "Romania", "Germany", "Macedonia", "Ukraine", "Georgia", "Armenia", "Kosovo", "Albania", "France", "Spain"],
    "North America": ["United States", "USA", "Canada", "Mexico", "Guatemala", "Honduras", "Haiti", "Dominican Republic", "Jamaica", "Belize"],
    "South America": ["Brazil", "Colombia", "Argentina", "Peru", "Ecuador", "Uruguay", "Bolivia", "Chile", "Paraguay"],
    "Middle East": ["Syria", "Cairo", "Jordan", "Lebanon"],
    "Oceania": ["Marshall Islands", "Fiji", "Samoa", "Vanuatu", "Australia"]
}

# Mapping Issue Primary to Emojis
ISSUE_EMOJI_MAP = {
    "Education": "📚",
    "Food Security": "🍎",
    "Environment": "🌱",
    "Health": "🏥",
    "Economic Development": "💰",
    "Technology": "💻",
    "Arts": "🎨",
    "Peacebuilding": "🕊️",
    "Conflict Resolution": "🤝",
    "Human Rights": "⚖️",
    "Youth Empowerment": "🎒",
    "Women's Empowerment": "💜",
    "Infrastructure": "🏗️"
}

# --- HELPERS ---
def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{data}"
    return None

@st.cache_data
def load_data():
    df = pd.read_csv('2025 Projects ABC Worksheet - App worksheet.csv')
    
    # Clean and Fill Data
    fill_cols = ['Title', 'Institution', 'Location', 'Coordinates', 'Quote', 'Pull Quotes']
    df[fill_cols] = df[fill_cols].ffill()
    
    # Split Coordinates
    def parse_coords(c):
        try:
            parts = str(c).split(',')
            return float(parts[0]), float(parts[1])
        except: return None, None
    df['lat'], df['lng'] = zip(*df['Coordinates'].apply(parse_coords))
    
    # Assign Regions
    def get_region(loc):
        loc_str = str(loc).lower()
        for region, keywords in REGION_MAP.items():
            if any(k.lower() in loc_str for k in keywords): return region
        return "Other"
    df['Region'] = df['Location'].apply(get_region)

    # Group for Projects
    project_df = df.groupby('Title').agg({
        'ID': 'first',
        'Institution': 'first',
        'Members': lambda x: ', '.join(x.dropna().unique()),
        'Location': 'first',
        'Region': 'first',
        'lat': 'first',
        'lng': 'first',
        'Pull Quotes': 'first',
        'Quote': 'first',
        'Issue Primary': 'first'
    }).reset_index()

    # Assign Emoji based on Primary Issue
    project_df['Emoji'] = project_df['Issue Primary'].apply(lambda x: ISSUE_EMOJI_MAP.get(str(x).strip(), "📍"))

    # Extract Issue/Approach Tags for sidebar filters
    def get_tags(title, p_col, s_col):
        subset = df[df['Title'] == title]
        tags = pd.concat([subset[p_col], subset[s_col]]).dropna().unique()
        return [str(t).strip() for t in tags if str(t).lower() != 'nan']

    project_df['Issues'] = project_df['Title'].apply(lambda t: get_tags(t, 'Issue Primary', 'Issue Secondary'))
    project_df['Approaches'] = project_df['Title'].apply(lambda t: get_tags(t, 'Approach Primary', 'Approach Secondary'))

    # Images
    def resolve_img(id_val):
        if pd.isna(id_val): return None
        clean_id = str(int(id_val))
        for ext in ['.jpg', '.jpeg', '.png']:
            path = f"images/{clean_id}{ext}"
            if os.path.exists(path): return path
        return None

    project_df['imagePath'] = project_df['ID'].apply(resolve_img)
    project_df['imageBase64'] = project_df['imagePath'].apply(get_base64_image)
    
    return project_df.dropna(subset=['lat', 'lng'])

df = load_data()

# --- SIDEBAR: FILTERS ---
with st.sidebar:
    st.title("Peace Map Controls")
    st.info("Click an emoji on the globe to see the project story and photo.")
    
    st.subheader("🔍 Filter Projects")
    search = st.text_input("Search Title or Student Name")
    
    all_locations = sorted(df['Location'].unique())
    all_inst = sorted(df['Institution'].unique())
    all_issues = sorted(list(set([i for sub in df['Issues'] for i in sub])))
    
    sel_loc = st.multiselect("Filter by Location", all_locations)
    sel_inst = st.multiselect("Filter by Institution", all_inst)
    sel_issue = st.multiselect("Filter by Issue Area", all_issues)

# --- FILTER LOGIC ---
f_df = df.copy()
if search:
    f_df = f_df[f_df['Title'].str.contains(search, case=False) | f_df['Members'].str.contains(search, case=False)]
if sel_loc:
    f_df = f_df[f_df['Location'].isin(sel_loc)]
if sel_inst:
    f_df = f_df[f_df['Institution'].isin(sel_inst)]
if sel_issue:
    f_df = f_df[f_df['Issues'].apply(lambda x: any(i in x for i in sel_issue))]

# --- GLOBE COMPONENT ---
st.title("Projects for Peace: 2025 Cohort 🌍")

points_json = json.dumps(f_df.mask(f_df.isna(), None).to_dict(orient='records'))

globe_html = f"""
<div id="globeViz"></div>
<div id="info-card">
    <div id="close-btn" onclick="document.getElementById('info-card').style.display='none'">×</div>
    <div id="card-content"></div>
</div>

<script src="//unpkg.com/globe.gl"></script>
<script>
    const data = {points_json};
    const world = Globe()(document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .htmlElementsData(data)
        .htmlElement(d => {{
          const el = document.createElement('div');
          // Display the emoji as the marker
          el.innerHTML = `<div style="font-size: 22px; cursor: pointer; filter: drop-shadow(0 0 3px white);">${{d.Emoji}}</div>`;
          
          el.onclick = () => {{
              const card = document.getElementById('info-card');
              const content = document.getElementById('card-content');
              card.style.display = 'block';
              const img = d.imageBase64 ? `<img src="${{d.imageBase64}}" class="c-img">` : '';
              
              // Strip outer quotes from the pull quote
              const cleanQuote = (d['Pull Quotes'] || 'No quote provided').replace(/^"|"$/g, '');

              content.innerHTML = `
                  ${{img}}
                  <div class="c-body">
                      <div class="c-title">${{d.Title}}</div>
                      <div class="c-school">${{d.Institution}} | ${{d.Location}}</div>
                      <div class="c-quote">"${{cleanQuote}}"</div>
                  </div>
              `;
          }};
          return el;
        }})
        .onPointHover(point => {{ world.controls().autoRotate = !point; }});
    
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.5;
</script>

<style>
    body {{ margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: transparent; }}
    #info-card {{
        position: absolute; top: 20px; right: 20px; width: 320px; max-height: 85vh;
        background: white; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.25);
        display: none; overflow-y: auto; z-index: 1000; border: 1px solid #ddd;
    }}
    #close-btn {{ position: absolute; top: 10px; right: 15px; cursor: pointer; font-size: 24px; color: #aaa; transition: 0.3s; }}
    #close-btn:hover {{ color: #333; }}
    .c-img {{ width: 100%; border-radius: 15px 15px 0 0; object-fit: cover; height: 180px; }}
    .c-body {{ padding: 20px; }}
    .c-title {{ font-weight: 700; font-size: 1.2em; color: #2c3e50; margin-bottom: 8px; line-height: 1.3; }}
    .c-school {{ font-size: 0.9em; color: #7f8c8d; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .c-quote {{ font-size: 1em; font-style: italic; color: #34495e; border-top: 2px solid #f1f1f1; padding-top: 15px; line-height: 1.5; }}
</style>
"""
components.html(globe_html, height=650)

# --- GALLERY VIEW ---
st.write("---")
st.subheader("📖 Full Project Gallery")

if f_df.empty:
    st.warning("Try adjusting your filters to see more projects.")
else:
    for _, row in f_df.iterrows():
        # Clean quotes for list view
        clean_p_quote = str(row['Pull Quotes']).strip('"')
        with st.expander(f"{row['Emoji']} {row['Title']} — {row['Location']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Institution:** {row['Institution']}")
                st.write(f"**Team Members:** {row['Members']}")
                st.write(f"**Primary Theme:** {row['Issue Primary']}")
                st.info(f"\"{clean_p_quote}\"")
            with col2:
                if row['imagePath']:
                    st.image(row['imagePath'], use_container_width=True)
            st.markdown("**Full Project Narrative:**")
            st.write(row['Quote'])
