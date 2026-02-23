import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace Map", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Replace with your actual filename
    df = pd.read_csv("projects_data.csv")
    
    # Clean headers (removes extra spaces and fixes casing)
    df.columns = df.columns.str.strip().str.capitalize()
    
    # Handle the 'Region' column specifically to ensure it exists
    # If your CSV uses a different name, change "Region" here.
    if "Region" not in df.columns:
        st.error("Error: 'Region' column not found in CSV. Please check column headers.")
        st.stop()
        
    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Projects")

# Create a list of regions for the dropdown
region_list = ["All"] + sorted(df["Region"].unique().tolist())
selected_region = st.sidebar.selectbox("Select a Region:", region_list)

# Filter the dataframe based on selection
if selected_region != "All":
    display_df = df[df["Region"] == selected_region]
else:
    display_df = df

# --- CREATE MAP ---
st.title(f"Projects for Peace: {selected_region if selected_region != 'All' else 'Global View'}")

# Initialize map centered on global coordinates
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

# Add markers
for idx, row in display_df.iterrows():
    # CLEANING QUOTES: .strip('"') removes the outer quotes if they exist in the CSV
    project_title = str(row['Project_title']).strip('"')
    description = str(row['Description']).strip('"')
    
    # Build HTML for the popup (no extra quotes added here)
    popup_html = f"""
    <div style="font-family: sans-serif; min-width: 200px;">
        <h4 style="margin-bottom: 5px;">{project_title}</h4>
        <p style="font-size: 12px; color: #555;"><b>Region:</b> {row['Region']}</p>
        <hr style="margin: 10px 0;">
        <p style="font-size: 13px;">{description}</p>
    </div>
    """
    
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=project_title
    ).add_to(m)

# Render map in Streamlit
st_folium(m, width="100%", height=600)

# --- DATA TABLE (Optional) ---
with st.expander("View Project Details"):
    st.write(display_df)
