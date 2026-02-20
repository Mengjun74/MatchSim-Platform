"""
Streamlit dashboard for visualizing CaRMS residency program data.
Provides an overview of matching statistics and a detailed program explorer.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

# API configuration via environment variables
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
st.set_page_config(page_title="CaRMS Program Explorer", layout="wide")

def get_data(endpoint, params=None):
    """
    Utility function to fetch data from the backend API.
    Handles standard HTTP errors and returns JSON payload.
    """
    try:
        response = requests.get(f"{API_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return []

def overview_page():
    """
    Renders the Analytics Overview page.
    Includes high-level metrics and distribution charts.
    """
    st.title("Market Overview")
    
    try:
        data = requests.get(f"{API_URL}/analytics/overview").json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Programs", data.get("total_programs", 0))
        col2.metric("Total Disciplines", data.get("total_disciplines", 0))
        col3.metric("Total Schools", data.get("total_schools", 0))
        col4.metric("Avg Sections/Prog", f"{data.get('avg_sections_per_program', 0):.1f}")
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")

    # Visualization: Programs by Discipline
    st.subheader("Programs by Discipline (Top 20)")
    try:
        disc_counts = requests.get(f"{API_URL}/analytics/counts/disciplines").json()
        df_disc = pd.DataFrame(disc_counts)
        if not df_disc.empty:
            fig = px.bar(df_disc.head(20), x='discipline', y='count', color='count', 
                         title="Distribution by Discipline")
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.warning("Could not load discipline data")
        
    # Visualization: Programs by School
    st.subheader("Programs by School (Top 20)")
    try:
        school_counts = requests.get(f"{API_URL}/analytics/counts/schools").json()
        df_school = pd.DataFrame(school_counts)
        if not df_school.empty:
            fig = px.bar(df_school.head(20), x='school', y='count', color='count', 
                         title="Distribution by School")
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.warning("Could not load school data")

def explorer_page():
    """
    Renders the Program Explorer page.
    Provides multi-index filtering, text search, and detailed program insights.
    """
    st.title("Program Explorer")
    
    # Navigation and Filtering Sidebar
    st.sidebar.header("Search & Filters")
    
    # Load filter options
    schools = get_data("schools")
    school_options = {s['name']: s['id'] for s in schools}
    selected_school_name = st.sidebar.selectbox("School", ["All"] + list(school_options.keys()))
    selected_school_id = school_options.get(selected_school_name) if selected_school_name != "All" else None
    
    disciplines = get_data("disciplines")
    disc_options = {d['name']: d['id'] for d in disciplines}
    selected_disc_name = st.sidebar.selectbox("Discipline", ["All"] + list(disc_options.keys()))
    selected_disc_id = disc_options.get(selected_disc_name) if selected_disc_name != "All" else None
    
    search_query = st.sidebar.text_input("Search Program Name")
    
    # Execute query with active filters
    params = {"limit": 100}
    if selected_school_id:
        params['school_id'] = selected_school_id
    if selected_disc_id:
        params['discipline_id'] = selected_disc_id
    if search_query:
        params['search'] = search_query
        
    programs = get_data("programs", params=params)
    
    if programs:
        st.write(f"Showing {len(programs)} results")
        
        # Primary results table
        df = pd.DataFrame(programs)
        st.dataframe(
            df[['name', 'discipline_name', 'school_name', 'url']], 
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("CaRMS Profile")
            }
        )
        
        # Detailed Drill-down View
        st.divider()
        st.subheader("Detail Inspector")
        selected_prog_name = st.selectbox("Choose a program to inspect details", df['name'].tolist())
        
        if selected_prog_name:
            prog_id = df[df['name'] == selected_prog_name].iloc[0]['id']
            detail = requests.get(f"{API_URL}/programs/{prog_id}").json()
            
            st.markdown(f"### {detail['name']}")
            st.markdown(f"**Entity:** {detail['school_name']} | **Discipline:** {detail['discipline_name']}")
            if detail.get('url'):
                st.markdown(f"[External Profile]({detail['url']})")
            
            # Display additional JSON metadata if available
            if detail.get('extra_data'):
                import json
                try:
                    meta = json.loads(detail['extra_data'])
                    with st.expander("Technical Metadata"):
                        st.json(meta)
                except:
                    pass
                
            # Render descriptive sections stored as Markdown
            if detail.get('sections'):
                for section in detail['sections']:
                    with st.expander(section['title']):
                        st.markdown(section['content'])
            else:
                st.info("No detailed program documentation available.")
            
    else:
        st.info("No programs found matching the selected criteria.")

def main():
    """Main dashboard entry point with sidebar navigation."""
    page = st.sidebar.radio("Navigation", ["Overview", "Program Explorer"])
    
    if page == "Overview":
        overview_page()
    elif page == "Program Explorer":
        explorer_page()

if __name__ == "__main__":
    main()
