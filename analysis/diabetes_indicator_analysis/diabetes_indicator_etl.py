import duckdb
from pathlib import Path

def connect_to_database():
    current_dir = Path(__file__).parent
    analysis_dir = current_dir.parent
    db_path = analysis_dir / "cdc_separate_indicator.duckdb"

    # Connect to the database
    return duckdb.connect(str(db_path))

conn = connect_to_database()
print(conn.sql("SELECT Year FROM cdc_health_data.diabetes_indicator LIMIT 10").df())