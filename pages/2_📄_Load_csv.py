import streamlit as st
import polars as pl

st.set_page_config(page_title="Charger un .csv", page_icon="📄")
st.title("📄 Charger un .csv")

session = st.connection("snowflake").session()

# 2. Upload du fichier CSV
uploaded_file = st.file_uploader("📄 Le .csv à charger dans snowflake", type="csv")

choix_separator = st.selectbox("📋 le séparateur ?", [',', ';'])

print(f"{uploaded_file=}")

if uploaded_file:
    df = pl.read_csv(uploaded_file, separator=choix_separator)
    st.write(f"✅ Fichier {uploaded_file.name} chargé :", df.shape)
    st.dataframe(df)

    if st.button("🔀 Transformer en table"):
        with st.spinner(f"⏳ table en création - {df.height} lignes"):
            res = session.write_pandas(
                df.to_pandas(),
                uploaded_file.name.replace(".csv", "").upper(),
                database="BIKESHARE",
                schema="BRONZE",
                auto_create_table=True,
                overwrite=True,
                use_logical_type=True,
            )

            # df.write_database(
            #     table_name="bikeshare.bronze.demo_csv_upload",
            #     connection=session.raw_connection,
            #     engine="adbc",
            # )

        if res.table_name:
            st.success("✅ Actualisation terminée")
            st.dataframe(res.collect())
        else:
            st.error("Oups qqch a planté")
