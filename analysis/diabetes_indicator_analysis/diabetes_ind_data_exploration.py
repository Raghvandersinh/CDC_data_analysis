import duckdb
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt= '%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
logging.info('info')
logging.debug('debug')
logging.warning('warning')
logging.error('error')
logging.critical("critical")


load_dotenv()

con = duckdb.connect()
table = "cdc_pgdb.diabetes_ind"
SCHEMA = os.getenv("CDC_DB_SCHEMA")
con.execute(f"ATTACH '{os.getenv("CDC_CONNECTION_STRING")}' AS cdc_pgdb (TYPE postgres, SCHEMA {SCHEMA});")
logger.info("Data Exploration and Quality Check...\n")

total_values = con.execute(f"SELECT COUNT(*) FROM {table}").fetchdf()
logger.info(f"Counting Total Numbers of Rows in our Database: {total_values}")
print("=" * 100)
distinct_year = con.execute(f"SELECT DISTINCT year FROM {table} ORDER BY year ASC").fetchdf()
logger.info(f"\nDistinct years in our year column:\n {distinct_year}")
print("=" * 100)
distinct_indicators = con.execute(f"SELECT DISTINCT indicator FROM {table}").fetchdf()
logger.info(f"\n Distinct indicators for diabetes: \n {distinct_indicators}")
print("=" * 100)
population_by_group = con.execute(f"SELECT population, COUNT(*) FROM {table} GROUP BY population").fetchdf()
logger.info(f"\n Population by group:\n {population_by_group}")
print("=" * 100)

missing_values = con.execute(f"SELECT COUNT(*) AS total, COUNT(estimate) AS has_estimates, COUNT(*) - COUNT(estimate) as missing_estimates FROM {table}").fetchdf()
logger.info(f"\nMissing Estimates:\n {missing_values}")

combination_records = con.execute(f"Select age, sex, education, race, COUNT(*) FROM {table} GROUP BY age, sex, education, race ORDER BY COUNT(*) DESC LIMIT 20").fetchdf()
logger.info(f"Combination of age, sex, education, and race:\n {combination_records}")