import duckdb
from dotenv import load_dotenv
import os

load_dotenv()

con = duckdb.connect()

SCHEMA = os.getenv("CDC_DB_SCHEMA")
con.execute(f"ATTACH '{os.getenv("CDC_CONNECTION_STRING")}' AS cdc_pgdb (TYPE postgres, SCHEMA {SCHEMA});")

result = con.execute("SELECT * FROM cdc_pgdb.diabetes_ind").df()
