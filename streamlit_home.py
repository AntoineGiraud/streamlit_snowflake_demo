import streamlit as st


st.set_page_config(page_title="Démos avec Snowflake", page_icon="🧰")
st.title("🧰 Démos avec Snowflake")
st.markdown("*By Antoine G.*")


session = st.connection("snowflake").session()


# Change the query to point to your table
def get_tables(_session):
    query = """-- list tables
        select table_schema, table_name, table_type, row_count, bytes, created, last_ddl_by, table_owner, comment
        from bikeshare.information_schema.tables
        where table_schema not ilike 'information_schema'
        order by 1,2
    """
    data = _session.sql(query).collect()
    return data


expander = st.expander("See Snowflake db bikeshare tables")
with expander:
    st.dataframe(get_tables(session))
