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

SCHEMA = os.getenv("CDC_DB_SCHEMA")
con.execute(f"ATTACH '{os.getenv("CDC_CONNECTION_STRING")}' AS cdc_pgdb (TYPE postgres, SCHEMA {SCHEMA});")
logger.info("Data Exploration and Quality Check...\n")

total_values = con.execute("SELECT COUNT(*) FROM cdc_pgdb.diabetes_ind").fetchall()
logger.info(f"Counting Total Numbers of Rows in our Database: {total_values}")

distinct_year = con.execute("SELECT DISTINCT year FROM cdc_pgdb.diabetes_ind").fetchall()
logger.info("\nDistinct years in our year column")
