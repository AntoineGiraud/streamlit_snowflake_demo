import streamlit as st

# Define the pages
main_page = st.Page("pages/streamlit_home.py", title="Accueil", icon="🎈")
page_1 = st.Page("pages/streamlit_bug_report_demo.py", title="Bug report demo", icon="👻")
page_2 = st.Page("pages/streamlit_load_csv.py", title="Load table from .csv", icon="🔀")

# Set up navigation
pg = st.navigation([main_page, page_1, page_2])

# Sidebar pour les filtres généraux
st.sidebar.markdown("Youpi ❄️")

# Run the selected page
pg.run()
