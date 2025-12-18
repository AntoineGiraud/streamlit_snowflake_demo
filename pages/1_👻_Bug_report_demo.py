import streamlit as st
from streamlit.connections import SnowflakeConnection
from typing import Dict

st.set_page_config(page_title="Bug report démo", page_icon="👻")
st.title("👻 Bug report demo!")
st.info(
    "Demo given by [snowflake - Streamlit Getting Started](https://docs.snowflake.com/en/developer-guide/streamlit/getting-started#build-your-first-sis-app)",
    icon="ℹ️",
)

cnx = st.connection("snowflake")
session = cnx.session()


def init_table(_session):
    """Create and populate the table if it doesn't exist"""
    create_query = """
    CREATE TABLE IF NOT EXISTS bronze.BUG_REPORT_DATA (
        AUTHOR VARCHAR(25),
        BUG_TYPE VARCHAR(25),
        COMMENT VARCHAR(100),
        DATE DATE,
        BUG_SEVERITY NUMBER(38,0)
    );
    """
    insert_query = """
    INSERT INTO bronze.BUG_REPORT_DATA (AUTHOR, BUG_TYPE, COMMENT, DATE, BUG_SEVERITY)
    VALUES
    ('John Doe', 'UI', 'The button is not aligned properly', '2024-03-01', 3),
    ('Aisha Patel', 'Performance', 'Page load time is too long', '2024-03-02', 5),
    ('Bob Johnson', 'Functionality', 'Unable to submit the form', '2024-03-03', 4),
    ('Sophia Kim', 'Security', 'SQL injection vulnerability found', '2024-03-04', 8),
    ('Michael Lee', 'Compatibility', 'Does not work on Internet Explorer', '2024-03-05', 2),
    ('Tyrone Johnson', 'UI', 'Font size is too small', '2024-03-06', 3),
    ('David Martinez', 'Performance', 'Search feature is slow', '2024-03-07', 4),
    ('Fatima Abadi', 'Functionality', 'Logout button not working', '2024-03-08', 3),
    ('William Taylor', 'Security', 'Sensitive data exposed in logs', '2024-03-09', 7),
    ('Nikolai Petrov', 'Compatibility', 'Not compatible with Safari', '2024-03-10', 2);
    """
    _session.sql(create_query).collect()
    _session.sql(insert_query).collect()


def get_data(_session):
    """Fetch table data"""
    query = """
        select * from bronze.BUG_REPORT_DATA
        order by date desc
        limit 100
    """
    data = _session.sql(query).collect()
    return data


def add_row_to_db(cnx: SnowflakeConnection, row: Dict):
    """Safely insert a row into the BUG_REPORT_DATA table using parameterized queries."""
    # cf. doc [st.connections.snowflakeconnection](docs.streamlit.io/develop/api-reference/connections/st.connections.snowflakeconnection#snowflakeconnectioncursor)
    sql = """
        INSERT INTO bronze.BUG_REPORT_DATA (author, bug_type, comment, date, bug_severity)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (row["author"], row["bug_type"], row["comment"], row["date"], row["bug_severity"])
    cnx.cursor().execute(sql, params)


form = st.form(key="annotation", clear_on_submit=True)

with form:
    cols = st.columns((1, 1))
    author = cols[0].text_input("Report author:")
    bug_type = cols[1].selectbox("Bug type:", ["Front-end", "Back-end", "Data related", "404"], index=2)
    comment = st.text_area("Comment:")
    cols = st.columns(2)
    date = cols[0].date_input("Bug date occurrence:")
    bug_severity = cols[1].slider("Bug priority :", 1, 5, 2)
    submitted = st.form_submit_button(label="Submit")

if submitted:
    try:
        add_row_to_db(
            cnx,
            {
                "author": author,
                "bug_type": bug_type,
                "comment": comment,
                "date": str(date),
                "bug_severity": bug_severity,
            },
        )
        st.success("Thanks! Your bug was recorded in the database.")
        st.balloons()
    except Exception as e:
        st.error(f"An error occurred: {e}")

expander = st.expander("See 100 most recent records")
with expander:
    try:
        data = get_data(session)
    except Exception:
        st.toast("Table non trouvée. Initialisation en cours...")
        init_table(session)
        data = get_data(session)

    st.dataframe(data)
