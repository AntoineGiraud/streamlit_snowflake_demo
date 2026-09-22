import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import polars as pl
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

if TYPE_CHECKING:
    from snowflake.snowpark import Session
    from snowflake.snowpark.dataframe import DataFrame as SnowparkDataFrame


# ==========================================
# DATACLASSES
# ==========================================


@dataclass
class ResultatValidation:
    contrat_trouve: bool
    est_valide: bool
    colonnes_manquantes: list[str] = field(default_factory=list)
    colonnes_en_trop: list[str] = field(default_factory=list)


# ==========================================
# FONCTIONS MÉTIER
# ==========================================


def load_file_to_dataframe(file: UploadedFile, file_ext: str, separator: str = ",") -> pl.DataFrame:
    """Lit un objet UploadedFile (CSV ou Parquet) et le convertit en DataFrame Polars."""
    if file_ext == ".csv":
        return pl.read_csv(file, separator=separator)
    if file_ext == ".parquet":
        return pl.read_parquet(file)

    raise ValueError(f"Format de fichier non supporté : {file_ext}")


def valider_contrat_donnees(
    nom_fichier: str, colonnes_df: list[str], contrats: list[dict[str, Any]]
) -> ResultatValidation:
    """
    Vérifie si les colonnes d'un DataFrame respectent le contrat attendu.
    Retourne une Dataclass explicite.
    """
    contrat = next((c for c in contrats if c["fichier"] == nom_fichier), None)

    if not contrat:
        return ResultatValidation(contrat_trouve=False, est_valide=False)

    colonnes_attendues = set(contrat["colonnes"])
    colonnes_fichier = set(colonnes_df)

    colonnes_manquantes = list(colonnes_attendues - colonnes_fichier)
    colonnes_en_trop = list(colonnes_fichier - colonnes_attendues)

    est_valide = not colonnes_manquantes and not colonnes_en_trop

    return ResultatValidation(
        contrat_trouve=True,
        est_valide=est_valide,
        colonnes_manquantes=colonnes_manquantes,
        colonnes_en_trop=colonnes_en_trop,
    )


def write_dataframe_to_snowflake(session: "Session", df: pl.DataFrame, table_name: str) -> "SnowparkDataFrame":
    """Charge un DataFrame Polars dans Snowflake."""
    return session.write_pandas(
        df.to_pandas(),
        table_name.upper(),
        # schema="BRONZE",
        auto_create_table=True,
        overwrite=True,
        use_logical_type=True,
    )


def get_target_path(table_name: str) -> str:
    """Récupère la DB et le Schema depuis st.secrets pour construire le chemin complet."""
    try:
        # On va chercher dans [connections.snowflake]
        sf_secrets = st.secrets["connections"]["snowflake"]
        # .get() permet de mettre une valeur par défaut si la clé est absente du toml
        db = sf_secrets.get("database", "DB_PAR_DEFAUT").upper()
        schema = sf_secrets.get("schema", "SCHEMA_PAR_DEFAUT").upper()
    except KeyError:
        db = "DB_INCONNUE"
        schema = "SCHEMA_INCONNU"

    return f"{db}.{schema}.{table_name.upper()}"


# ==========================================
# APPLICATION STREAMLIT
# ==========================================

st.set_page_config(page_title="Charger un fichier", page_icon="📄", layout="wide")
st.title("📄 Charger un fichier (.csv ou .parquet)")

cols = st.columns([1, 2])

with cols[0]:
    contrats: list[dict[str, Any]] = [
        {"fichier": "retours", "colonnes": ["ID commande", "Retourné"]},
        {"fichier": "personnes", "colonnes": ["Zone géographique", "Responsable régional"]},
    ]

    st.subheader("📋 Contrats de données attendus")
    st.dataframe(contrats)

    uploaded_file = st.file_uploader("📄 Fichier à charger", type=["csv", "parquet"])

    choix_separator = ","
    if uploaded_file and uploaded_file.name.endswith(".csv"):
        choix_separator = st.selectbox("📋 Le séparateur ?", [";", ",", "|"])

with cols[1]:
    if uploaded_file:
        file_name, file_ext = os.path.splitext(uploaded_file.name)
        file_ext = file_ext.lower()

        # 1. Chargement
        try:
            df = load_file_to_dataframe(uploaded_file, file_ext, choix_separator)
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {e}")
            st.stop()

        st.write(f"✅ Fichier `{uploaded_file.name}` chargé :", df.shape)
        st.dataframe(df)

        # 2. Vérification du contrat
        validation = valider_contrat_donnees(
            nom_fichier=file_name,
            colonnes_df=df.columns,
            contrats=contrats,
        )

        # Affichage des résultats de la validation
        if not validation.contrat_trouve:
            st.warning("⚠️ Aucun contrat trouvé pour ce fichier. Impossible de valider le schéma.")
        elif validation.est_valide:
            st.success("🟢 Le fichier respecte parfaitement le contrat de données.")
        else:
            st.error("🔴 Le fichier ne respecte PAS le contrat de données.")
            if validation.colonnes_manquantes:
                st.error(f"Colonnes manquantes : {validation.colonnes_manquantes}")
            if validation.colonnes_en_trop:
                st.error(f"Colonnes en trop : {validation.colonnes_en_trop}")

        # --- NOUVEAU : Affichage de la destination ---
        target_path = get_target_path(file_name)
        st.info(f"📍 Destination prévue : `{target_path}`")

        # 3. Écriture
        if st.button("🔀 Charger dans snowflake"):
            # Sécurité optionnelle à décommenter si on veut bloquer l'upload :
            # if validation.contrat_trouve and not validation.est_valide:
            #     st.error("❌ Impossible de transformer : le contrat n'est pas respecté.")
            #     st.stop()

            with st.spinner(f"⏳ table en création - {df.height} lignes"):
                try:
                    session = st.connection("snowflake").session()

                    res = write_dataframe_to_snowflake(session, df, file_name)

                    if res.table_name:
                        st.success(f"✅ Fichier chargé avec succès dans la table `{target_path}` !")
                        st.balloons()
                        st.dataframe(res.collect())
                except Exception as e:
                    st.error(f"Oups, quelque chose a planté lors de l'écriture : {e}")
