import streamlit as st
import polars as pl
import os

st.set_page_config(page_title="Export .parquet table ❄️", page_icon="💾")
st.title("💾 Export .parquet table ❄️")


conn = st.connection("snowflake")
session = conn.session()

db_to_show = "BIKESHARE"
os.makedirs("offload", exist_ok=True)


# Change the query to point to your table


@st.cache_data
def get_tables(_session):
    query = f"""-- list tables
        select table_schema, table_name, table_type, row_count, bytes, created, last_ddl_by, table_owner, comment, concat(table_schema, '.', table_name) as full_name
        from {db_to_show}.information_schema.tables
        where table_schema not ilike 'information_schema'
        order by 1,2
    """
    data = pl.from_pandas(_session.sql(query).to_pandas())
    return data


def snow_offload_stage_interne(session, schema: str, table: str) -> str:
    export_sql = f"""
COPY INTO @~/offload/{schema}_{table}.parquet
FROM {db_to_show}.{schema}.{table}
FILE_FORMAT = (TYPE = PARQUET COMPRESSION = SNAPPY)
SINGLE = TRUE
OVERWRITE = TRUE;
    """

    expander_snowcli = st.expander("Alternative: Offload stage interne + snowcli")
    with expander_snowcli:
        st.code(export_sql.strip(), language="sql")
        st.code(f"snow storage cp @~/offload/{schema}_{table}.parquet file://./offload/{schema}_{table}.parquet", language="bash")

    # session.sql(export_sql).collect()
    return f"{schema}_{table}.parquet"


def stream_table_to_parquet(conn, full_table_name: str, parquet_path: str):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {full_table_name}")

    batches = cursor.fetch_arrow_batches()

    df = None
    for batch in batches:
        pl_batch = pl.from_arrow(batch)
        if df is None:
            df = pl_batch
        else:
            df.vstack(pl_batch, in_place=True)

    df.write_parquet(parquet_path)

    return df


with st.spinner(f"⏳ récupération des tables `{db_to_show}`"):
    sf_tables = get_tables(session)

    expander = st.expander(f"Liste des {len(sf_tables)} tables `{db_to_show}`")
    with expander:
        st.dataframe(sf_tables)

    # Sélecteur de table
    selected_table = st.selectbox("📋 Sélectionnez une table à exporter", sf_tables["FULL_NAME"].to_list())

    # Bouton d'export
    if st.button("💾 Préparer le .parquet"):
        schema, table = selected_table.split(".")
        query = f"SELECT * FROM {db_to_show}.{schema}.{table}"

        with st.spinner(f"📦 Export de `{selected_table}` en cours..."):
            parquet_path = f"offload/{table}.parquet"
            stream_table_to_parquet(conn, f"{db_to_show}.{schema}.{table}", f"offload/{table}.parquet")

            # slow j'ai peur #pasDeStream
            # pl_df = pl.from_pandas(session.sql(query).to_pandas())
            # pl_df.write_parquet(parquet_path)

            st.success(f"✅ Export terminé : `{parquet_path}`")

            snow_offload_stage_interne(session, schema, table)

        with open(parquet_path, "rb") as f:
            st.download_button(
                label="📥 Télécharger le fichier .parquet",
                data=f,
                file_name=os.path.basename(parquet_path),
                mime="application/octet-stream",
            )
