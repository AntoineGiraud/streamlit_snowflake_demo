import streamlit as st
import polars as pl
import plotly.express as px

st.set_page_config(page_title="Démos avec Snowflake", page_icon="🧰", layout="wide")
st.title("🧰 Démos avec Snowflake")

session = st.connection("snowflake").session()


@st.cache_data(ttl=600)
def get_tables(_session) -> pl.DataFrame:
    """Get list of tables in Snowflake database"""
    query = """-- list tables
        select table_schema, table_name, table_type, row_count, bytes, created, last_ddl, last_altered, last_ddl_by, table_owner, comment, table_catalog
        from information_schema.tables
        where table_schema not ilike 'information_schema'
        order by 1,2
    """
    df = pl.from_pandas(_session.sql(query).to_pandas())
    df = df.with_columns(
        [
            (pl.col("BYTES") / 1024**2).alias("BYTES_MB"),
            (pl.col("BYTES") / 1024**3).alias("BYTES_GB"),
        ]
    )
    return df


def human_size_format(bytes: int) -> str:
    size_mb = bytes / (1024**2)
    return f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb / 1024:.1f} GB"


def human_nb_format(num: int) -> str:
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}k"
    else:
        return str(num)


df = get_tables(session)


# ------ KPI / Big ass numbers ------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tables + Vues", df.height)
col2.metric("Vues", df.filter(pl.col("TABLE_TYPE") == "VIEW").height)
col3.metric("Total Rows", human_nb_format(int(df["ROW_COUNT"].sum())))
col4.metric("Total Size", human_size_format(int(df["BYTES"].sum())))

# ------ df des tables ------
expander = st.expander(f"See {df.height} Snowflake tables")
with expander:
    st.dataframe(df)

# ------ Graphiques ------
col1, col2 = st.columns(2)

with col1:
    # --- Graph par schéma
    df_schema = (
        df.group_by("TABLE_SCHEMA")
        .agg([pl.count().alias("nb_tables"), pl.sum("ROW_COUNT").alias("rows"), pl.sum("BYTES").alias("bytes")])
        .sort("nb_tables", descending=False)
        .to_pandas()
    )

    fig_schema = px.bar(
        df_schema,
        x="nb_tables",
        y="TABLE_SCHEMA",
        hover_data={"rows": ":,d", "bytes": ":,d"},
        title="Nb tables par schéma",
        orientation="h",
    )
    fig_schema.update_traces(
        text=df_schema["nb_tables"],  # format avec séparateur
        textposition="outside",  # place le texte à l'extrémité
    )
    fig_schema.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        xaxis_tickformat="~s",  # format abrégé (1k, 1M…)
    )
    col1.plotly_chart(fig_schema, use_container_width=True)

with col2:
    tables_pd = df.filter(pl.col("ROW_COUNT").is_not_null()).sort("ROW_COUNT", descending=True).head(30).to_pandas()

    # --- Graph par table (nb lignes)
    fig_tables = px.bar(
        tables_pd,
        x="ROW_COUNT",
        y="TABLE_NAME",
        hover_data={"BYTES": ":,d"},
        title="Top 30 tables par nombre de lignes",
        orientation="h",
    )
    fig_tables.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        xaxis_tickformat="~s",  # format abrégé (k, M…)
        yaxis=dict(categoryorder="total ascending"),  # force l’ordre
    )
    col2.plotly_chart(fig_tables, use_container_width=True)
