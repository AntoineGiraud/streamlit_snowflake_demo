import streamlit as st
import polars as pl

st.set_page_config(page_title="Charger un .csv", page_icon="📄", layout="wide")
st.title("📄 Charger un .csv")

session = st.connection("snowflake").session()

cols = st.columns([1, 2])

with cols[0]:
    # --- Contrats de données ---
    contrats = [
        {"ficher": "retours.csv", "colonnes": ["ID commande", "Retourné"]},
        {"ficher": "ventes.csv", "colonnes": ["Zone géographique", "Responsable régional"]},
    ]

    st.subheader("📋 Contrats de données attendus")
    st.dataframe(contrats)  # Affichage des contrats pour référence

    # --- Upload du fichier CSV ---
    uploaded_file = st.file_uploader("📄 Le .csv à charger dans snowflake", type="csv")
    choix_separator = st.selectbox("📋 le séparateur ?", [",", ";", "|"])

with cols[1]:
    if uploaded_file:
        df = pl.read_csv(uploaded_file, separator=choix_separator)
        st.write(f"✅ Fichier `{uploaded_file.name}` chargé :", df.shape)
        st.dataframe(df)

        # --- Vérification du contrat ---
        contrat = next((c for c in contrats if c["ficher"] == uploaded_file.name), None)
        contrat_ok = False  # valeur par défaut

        if contrat is None:
            st.warning("⚠️ Aucun contrat trouvé pour ce fichier. Impossible de valider le schéma.")
        else:
            colonnes_attendues = set(contrat["colonnes"])
            colonnes_fichier = set(df.columns)

            colonnes_manquantes = colonnes_attendues - colonnes_fichier
            colonnes_en_trop = colonnes_fichier - colonnes_attendues

            if not colonnes_manquantes and not colonnes_en_trop:
                st.success("🟢 Le fichier respecte parfaitement le contrat de données.")
                contrat_ok = True
            else:
                st.error("🔴 Le fichier ne respecte PAS le contrat de données.")
                if colonnes_manquantes:
                    st.error(f"Colonnes manquantes : {list(colonnes_manquantes)}")
                if colonnes_en_trop:
                    st.error(f"Colonnes en trop : {list(colonnes_en_trop)}")

        # --- Bouton d'upload ---
        if st.button("🔀 Charger dans snowflake"):
            # if not contrat_ok:
            #     st.error("❌ Impossible de transformer : le contrat n'est pas respecté.")
            #     st.stop()

            with st.spinner(f"⏳ table en création - {df.height} lignes"):
                res = session.write_pandas(
                    df.to_pandas(),
                    uploaded_file.name.replace(".csv", "").upper(),
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
                st.success("✅ Fichier chargé avec succès dans Snowflake !")
                st.balloons()
                st.dataframe(res.collect())
            else:
                st.error("Oups qqch a planté")
