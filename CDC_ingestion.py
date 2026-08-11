from pathlib import Path
import json
import duckdb
from dataclasses import field
from typing import List, Any, Generator, Dict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from sqlalchemy.orm import Session
import time 
import logging
import requests
import math
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os 
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float
load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL_SCHEMA'))
Session = sessionmaker(bind=engine)

metadata = MetaData()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt= '%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
logging.info('info')
logging.debug('debug')
logging.warning('warning')
logging.error('error')
logging.critical("critical")

def json_length(filename:str) -> int:
    json_path = json.load(open(filename))
    return len(json_path)

def endpoints_dict() -> dict:
    """
    Opens and reads the /endpoint/cdc_api_endpoint.json, which contains list of API endpoint identifier
    Returns:
        endpoint_datact: returns the content of the json file
    """
    endpoint_path = Path("endpoint/cdc_api_endpoint.json")
    with endpoint_path.open(mode="r", encoding = 'utf-8') as file:
        content = file.read()
        return json.loads(content)
    
def get_endpoint(key_target:str) -> list:
    endpoints = endpoints_dict()
    return endpoints[key_target.lower()]

def transform_single_diabetes_ind(endpoint_data):
    try:
        return{
                'year': endpoint_data.get('year'),
                'indicator':endpoint_data.get('indicator'),
                'unit':endpoint_data.get('unit'),
                'estimate': float(endpoint_data.get('estimate', 0)) or None,
                'se_estimate': float(endpoint_data.get('seestimate', 0)) or None,
                'lower_limit': float(endpoint_data.get('lowerlimit', 0)) or None,
                'upper_limit': float(endpoint_data.get('upperlimit',0)) or None,
                'population': endpoint_data.get('population'),
                'age': endpoint_data.get('age'),
                'race': endpoint_data.get('race'),
                'sex': endpoint_data.get('sex'),
                'education': endpoint_data.get('education'),
                'other_info': endpoint_data.get('other_stratification')
            }
    except Exception as e:
        logger.error(f"Error transforming")
        logger.debug(f"Problem record data: {endpoint_data}")
        return None 
    
def process_chunk(transform_func, chunk_data):
    
    logger.debug(f"Processing chunk of size {len(chunk_data)}")
    return [transform_func(endpoint_data) for endpoint_data in chunk_data]

def transform_endpoint_data(data:list = None, max_workers: int = None, chunk_size: int = 1000, transform_single_func=None) -> list:
    
    if not data or not transform_single_func:
        logger.warning("No data provided or No transformation function provided")
        return []
    
    logger.info(f'Starting transformation of {len(data)} records')
    logger.info(f"Using {max_workers or 'default'} workers and chunk size {chunk_size}")
    
    if data: 
        logger.debug(f"Sample keys: {data[0].keys()}")
        
    chunks = []
    num_chunks = math.ceil(len(data) / chunk_size)
    logger.info(f"Created {num_chunks} chunks")
     
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_inx = min((i + 1) * chunk_size, len(data))
        chunks.append(data[start_idx:end_inx])
    
    result = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        futures_to_chunck = {executor.submit(process_chunk, transform_single_func, chunk): i for i, chunk in enumerate(chunks)}
        
        completed_chunks = 0
        for future in as_completed(futures_to_chunck):
            chunk_idx = futures_to_chunck[future]
            try:
                chunk_results = future.result()
                result.extend(chunk_results)
                completed_chunks += 1
                logger.info(f"Completed chunk {chunk_idx + 1}/{num_chunks} ({completed_chunks/num_chunks*100:.1f}%)")
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_idx}: {e}")
    logger.info(f"Successfully transformed {len(result)} records")
    
    return result 

def upsert_data(transformed_data:list = None, table:str = None, engine=engine, conflict_columns = None, update_columns = None):
    
    if not transformed_data:
        logger.warning("No data to upsert")
        return 0
    if not db_table or not engine:
        logger.error("db_table and engine are required")
        return 0
    if conflict_columns is None:
        conflict_columns = ['id']
    
    logger.info(f"Upserting {len(transformed_data)} records into {db_table.name}")
    
    try:
    
def etl_pipeline(base_url:str, endpoints:list, pageSize:int, transform_data = None, transform_single_func = None):
    
    logger.info("=" * 60)
    logger.info(f"Starting the Main ETL Pipeline")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Endpoints: {endpoints}")
    logger.info(f"Page Size: {pageSize}")
    logger.info('=' * 60)
    
    all_transformed_data = []
    page = 1
    for endpoint_idx, endpoint in enumerate(endpoints):
        logger.info(f"\n--- Processing endpoint {endpoint_idx + 1}/{len(endpoints)}: {endpoint}---")
        endpoint_url = f"{base_url}{endpoint}"
        total_pages_processed = 0
        while True:
            parameter = {
                'pageSize': pageSize,
                'pageNumber': page
            }
            try:
                logger.debug(f"Requesting page{page} from {endpoint_url}")
                response = requests.get(endpoint_url, params=parameter)
                data = response.json()

                if not data or len(data) == 0:
                    logger.info(f"No more data at page {page}. Stopping endpoint {endpoint}")
                    break
                logger.info(f"page {page}: Retrieved {len(data)} records")
                endpoint_record_count = len(data)
                total_pages_processed += 1
                
                if transform_data and transform_single_func:
                    transformed_data = transform_data(
                        data= data,
                        max_workers = 4,
                        chunk_size = 1000,
                        transform_single_func = transform_single_func
                    )
                    transformed_data = [d for d in transformed_data if d is not None]
                    all_transformed_data.extend(transformed_data)
                    logger.info(f"Added {len(transformed_data)} transformed records")
                else: 
                    all_transformed_data.extend(data)
                    logger.warning(f"No transform funtion provided - using raw data")
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Requesting error for {endpoint_url}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                break
        logger.info(f"Completed endpoint {endpoint}: Retrieved {endpoint_record_count} records")
    
    logger.info('=' * 60)
    logger.info(f"ETL Pipeline Completed")
    logger.info(f"Total page processed: {total_pages_processed}")
    logger.info(f"Total records processed: {len(all_transformed_data)}")
    logger.info("=" * 60)
    return all_transformed_data

if __name__ == '__main__':
    logger.info("Starting script")
    logger.info("Initializing ETL pipeline...")
    
    base_url = 'https://data.cdc.gov/api/v3/views/'
    endpoints = get_endpoint(key_target="diabetes_ind")
    etl_pipeline(base_url=base_url, endpoints=endpoints, pageSize=10000, 
                 transform_data=transform_endpoint_data, transform_single_func=transform_single_diabetes_ind)
    