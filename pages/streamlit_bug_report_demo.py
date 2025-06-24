import streamlit as st

cnx = st.connection("snowflake")
session = cnx.session()

st.title("👻 Bug report demo!")
st.info("Demo given by [snowflake - Streamlit Getting Started](https://docs.snowflake.com/en/developer-guide/streamlit/getting-started#build-your-first-sis-app)", icon="ℹ️")


def get_data(_session):
    """Fetch table data"""
    query = """
        select * from bikeshare.bronze.BUG_REPORT_DATA
        order by date desc
        limit 100
    """
    data = _session.sql(query).collect()
    return data


def add_row_to_db(cnx, row):
    """Safely insert a row into the BUG_REPORT_DATA table using parameterized queries."""
    # cf. doc [st.connections.snowflakeconnection](docs.streamlit.io/develop/api-reference/connections/st.connections.snowflakeconnection#snowflakeconnectioncursor)
    sql = """
        INSERT INTO bikeshare.bronze.BUG_REPORT_DATA (author, bug_type, comment, date, bug_severity)
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
        add_row_to_db(cnx, {"author": author, "bug_type": bug_type, "comment": comment, "date": str(date), "bug_severity": bug_severity})
        st.success("Thanks! Your bug was recorded in the database.")
        st.balloons()
    except Exception as e:
        st.error(f"An error occurred: {e}")

expander = st.expander("See 100 most recent records")
with expander:
    st.dataframe(get_data(session))
