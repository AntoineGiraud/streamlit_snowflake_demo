import polars as pl
import snowflake.connector
import toml

# Load Snowflake connection details from snow.toml
config = toml.load(".streamlit/secrets.toml")["connections"]["snowflake"]

# Establish Snowflake connection
conn = snowflake.connector.connect(
    account=config["account"],
    warehouse=config["warehouse"],
    database=config["database"],
    schema=config["schema"],
    user=config["user"],
    private_key_file=config["private_key_file"],
)
session = conn.cursor()

# Execute SQL query to list tables in the current schema
query = """-- list tables
    select table_schema, table_name, table_type, row_count, bytes, created, last_ddl_by, table_owner, comment
    from bikeshare.information_schema.tables
    where table_schema not ilike 'information_schema'
    order by 1,2
"""
session.execute(query)

# Récupérer les noms de colonnes automatiquement
columns = [desc[0] for desc in session.description]
rows = session.fetchall()

# Créer le DataFrame Polars
df = pl.DataFrame(rows, schema=columns)
print(f"{df=}")

# Close the cursor and connection
session.close()
conn.close()
