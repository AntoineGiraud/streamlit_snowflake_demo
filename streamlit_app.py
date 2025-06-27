import streamlit as st

# Define the pages
main_page = st.Page("streamlit_home.py", title="Accueil", icon="🎈")
page_1 = st.Page("pages/1_👻_bug_report_demo.py", title="Bug report demo", icon="👻")
page_2 = st.Page("pages/2_📄_load_csv.py", title="Load table from .csv", icon="📄")

# Set up navigation
pg = st.navigation([main_page, page_1, page_2])
pg.run()  # Run the selected page

# Sidebar pour les filtres généraux
st.sidebar.markdown("Youpi ❄️")
