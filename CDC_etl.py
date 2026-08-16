from pathlib import Path
import json
import duckdb
from dataclasses import field
from typing import List, Any, Generator, Dict, Union
from threading import Lock
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

engine = create_engine(os.getenv('DATABASE_URL_SCHEMA'),
                       pool_size=10,
                       max_overflow=20,
                       pool_pre_ping=True,
                       pool_recycle=3600)
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
    """
    Reads the cdc_api_endpoint.json file and returns the value of the key containing list of endpoints

    Args:
        key_target (str): key value from the dict

    Returns:
        list: value of the key containing list of endpoints
    """
    endpoints = endpoints_dict()
    return endpoints[key_target.lower()]

def transform_single_diabetes_ind(endpoint_data, endpoint_id = None):
    """
    Transforms a single value from the raw CDC diabetes indicator data from the CDC REST API making it database insertion ready

    Args:
        endpoint_data (_type_): Raw data from the CDC diabetes indicator endpoint API data
        endpoint_id (_type_, optional): specfic endpoint id from the list(look at cdc_api_endpoint for example.)

    Returns:
        dict: transformed dict 
    """
    try:
        return{
                'api_id': endpoint_data.get(':id'),
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
def transform_single_stroke_mortality(endpoint_data, endpoint_id = None):
    """
    Transforms a single value from the raw CDC stroke mortaility data from the CDC REST API making it database insertion ready

    Args:
        endpoint_data (_type_): Raw data from the CDC storke mortaility endpoint API data
        endpoint_id (_type_, optional): specfic endpoint id from the list(look at cdc_api_endpoint for example.)

    Returns:
        dict: transformed dict 
    """
    try:
        # Handle value field - check for "NA" before converting to float
        raw_value = endpoint_data.get('data_value')
        
        # If it's "NA" or None, set to None
        if raw_value == "NA" or raw_value is None:
            clean_value = None
        else:
            try:
                clean_value = float(raw_value)
            except (ValueError, TypeError):
                clean_value = None
        result = {
                'api_id': endpoint_data.get(':id'),
                'year':endpoint_data.get('year'),
                'icd_class': endpoint_data.get('class'),
                'state':endpoint_data.get('locationabbr'),
                'location': endpoint_data.get('locationdesc'),
                'geo_level': endpoint_data.get('geographiclevel'),
                'value': clean_value,
                'rate':endpoint_data.get('data_value_unit'),
                'race': endpoint_data.get('stratification2'),
                'fips':endpoint_data.get('locationid')
        }
        if endpoint_id == '7b9s-s8ck':
            # For this endpoint, sex is in stratification3
            result['sex'] = endpoint_data.get('stratification3')
        else:
            # For other endpoints, sex is in stratification1
            result['sex'] = endpoint_data.get('stratification1')
        
        return result
    except Exception as e:
        logger.error(f"Error transforming")
        logger.debug(f"Problem record data: {endpoint_data}")
        return None 
    
def process_chunk(transform_func, chunk_data, endpoint_id = None):
    """
    Processes a batch(chunk) of data records by applying a transformation function(those transform_single_...() function above) to each record in the chunk
    Args:
        transform_func (_type_): one of the transform_single_...() from above
        chunk_data (_type_): raw API data in the chunk 
        endpoint_id (_type_, optional): Specific API endpoint from a key value in cdc_api_endpoint.json Defaults to None.

    Returns:
        list: Returns transformed dict chunk data in a list. 
    """
    logger.debug(f"Processing chunk of size {len(chunk_data)}")
    if endpoint_id:
        return [transform_func(record, endpoint_id) for record in chunk_data]
    else:
        return [transform_func(record) for record in chunk_data]

def transform_endpoint_data(data:list = None, 
                            max_workers: int = None, 
                            chunk_size: int = 1000, 
                            transform_single_func=None,
                            endpoint_id = None) -> list:
    """
    1. Gets the Raw API Data from the specfic endpoint_id.
    2. Breaks the large data in to chunks based on the chunk_size
    3. Uses Threading to split the work of transforming chunks between 4 workers 
    4. returns a transformed data dictionary
    Args:
        data (list, optional): Raw Api endpoint data. Defaults to None.
        max_workers (int, optional): Number of threads being used to transform chunks. Defaults to None.
        chunk_size (int, optional): _description_. Size of a single chunk data. Default 1000
        transform_single_func (_type_, optional): Transformation function being used depending on the endpoint. Defaults to None.
        endpoint_id (_type_, optional): What endpoint are extracting the data from. Defaults to None.

    Returns:
        list: list of transformed dict records
    """
    if not data or not transform_single_func:
        logger.warning("No data provided or No transformation function provided")
        return []
    
    logger.info(f'Starting transformation of {len(data)} records for endpoint {endpoint_id}')    
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
        
        futures_to_chunck = {
            executor.submit(process_chunk, transform_single_func, chunk,endpoint_id): i for i, chunk in enumerate(chunks)
            }
        
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

def upsert_data(transformed_data:list = None, 
                table: Union[Table, str] = None, 
                engine=engine, 
                conflict_columns = None, 
                update_columns = None,
                exclude_columns=None,
                batch_size = 1000,
                max_workers = 4):
    """
    1. gets the transformed data(From the transfomr_endpoint_data() most likely)
    2. Breaks the transformed data into batches for seemless data entry.
    3. Uses threading to split the work of "upserting data into the database" by max_workers
    4. old data get updated and new data gets inserted

    Args:
        transformed_data (list, optional): list containing transformed dict data. Defaults to None.
        table (Union[Table, str], optional): table we want to connect to in our database schema. Defaults to None.
        engine (_type_, optional): _description_. bridges the connection between database and python .Defaults to engine.
        conflict_columns (_type_, optional): checks if we have this column data in the database schema table. Defaults to None.
        update_columns (_type_, optional): _description_. columns we would like to update in our database schema table.
        exclude_columns (_type_, optional): _description_.columns we would like to exclude from upserting into our database schema table .Defaults to None.
        batch_size (int, optional): _description_. Batches we would like to split out transformed data into .Defaults to 1000.
        max_workers (int, optional): _description_. Amount of threads(workers) working on inserting data into the database .Defaults to 4.

    Returns:
        int: total amounted of data inserted into the database
    """
    
    if not transformed_data:
        logger.warning("No data to upsert")
        return 0
    if not table or not engine:
        logger.error("db_table and engine are required")
        return 0
    
    if isinstance(table, str):
        table = Table(table, metadata, autoload_with=engine)
        logger.info(f"Reflected table: {table.name}")
        
    if conflict_columns is None:
        conflict_columns = ['api_id']
    if exclude_columns is None:
        exclude_columns = ['id', 'created_at', 'updated_at', 'created_date', 'modified_date']
    if update_columns is None:
        update_columns = [col.name for col in table.columns
                         if col.name not in conflict_columns
                         and col.name not in exclude_columns]
    
    batches = [transformed_data[i:i + batch_size] for i in range(0, len(transformed_data), batch_size)]
    logger.info(f"Processing {len(batches)} batches with {max_workers} threads")
    def process_batch(batch_data, batch_id):
        """Process a single batch in a thread"""
        try:
            with engine.connect() as conn:
                with conn.begin():
                    stmt = insert(table).values(batch_data)
                    upsert_stmt = stmt.on_conflict_do_update(
                        index_elements=conflict_columns,
                        set_={col: getattr(stmt.excluded, col) for col in update_columns}
                    )
                    result = conn.execute(upsert_stmt)
                    conn.commit()
                    logger.debug(f"Batch {batch_id}: Upserted {len(batch_data)} records")
                    return len(batch_data)
        except Exception as e:
            logger.error(f"Batch {batch_id} failed: {e}")
            return 0
    
    # Execute in parallel
    total_upserted = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_batch, batch, idx): idx 
            for idx, batch in enumerate(batches)
        }
        
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                count = future.result()
                total_upserted += count
                logger.info(f"Batch {batch_idx + 1}/{len(batches)} completed - {count} records")
            except Exception as e:
                logger.error(f"Batch {batch_idx + 1} failed: {e}")
    
    logger.info(f"Total upserted: {total_upserted} records")
    return total_upserted
    
    
def etl_pipeline(base_url: str, 
                 endpoints: list, 
                 pageSize: int, 
                 transform_data=None, 
                 transform_single_func=None, 
                 table: str = None,
                 max_page: int = None):
    """
    The main pipeline that combines all the function above.
    1. Connects to the API source using the endpoint_id and brings in the raw data
    2. Transforms data by chunks and returns a transformed list of dicts. 
    3. Upserts the transformed data into the database using batches. 
    Args:
        base_url (str): base url of the API
        endpoints (list): endpoint of the API url
        pageSize (int): size of each API url page. 
        transform_data (_type_, optional): transformed data from transform_endpoint_data() function. Defaults to None.
        transform_single_func (_type_, optional): _description_. One of the transform single function .Defaults to None.
        table (str, optional): _description_. table in the database where we went to upsert data into .Defaults to None.
        max_page (int, optional): _description_. Maximum number of page we went to traverse in our API .Defaults to None.

    Returns:
        dict: the transformed data inserted into the database
    """
    logger.info("=" * 60)
    logger.info(f"Starting the Main ETL Pipeline")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Endpoints: {endpoints}")
    logger.info(f"Page Size: {pageSize}")
    if max_page:
        logger.info(f"Max Page Limit: {max_page}")
    logger.info('=' * 60)
    
    all_transformed_data = []
    total_pages_processed = 0  # Initialize once
    
    for endpoint_idx, endpoint in enumerate(endpoints):
        logger.info(f"\n--- Processing endpoint {endpoint_idx + 1}/{len(endpoints)}: {endpoint}---")
        endpoint_url = f"{base_url}{endpoint}"
        page = 1
        endpoint_record_count = 0  # nitialize per endpoint
        
        while True:
            #  Check max_page before making the request
            if max_page and page > max_page:
                logger.info(f"Max page {max_page} reached. Stopping endpoint {endpoint}")
                break
                
            parameter = {
                'pageSize': pageSize,
                'pageNumber': page
            }
            
            try:
                logger.debug(f"Requesting page {page} from {endpoint_url}")
                response = requests.get(endpoint_url, params=parameter)
                response.raise_for_status()
                data = response.json()

                if not data or len(data) == 0:
                    logger.info(f"No more data at page {page}. Stopping endpoint {endpoint}")
                    break
                    
                logger.info(f"Page {page}: Retrieved {len(data)} records")
                endpoint_record_count += len(data)  # Accumulate
                total_pages_processed += 1  # Accumulate
                
                if transform_data and transform_single_func:
                    endpoint_id = endpoint.split('/')[0]
                    transformed_data = transform_data(
                        data=data,
                        max_workers=4,
                        chunk_size=1000,
                        transform_single_func=transform_single_func,
                        endpoint_id=endpoint_id
                    )
                    transformed_data = [d for d in transformed_data if d is not None]
                    all_transformed_data.extend(transformed_data)
                    logger.info(f"Added {len(transformed_data)} transformed records")
                else: 
                    all_transformed_data.extend(data)
                    logger.warning(f"No transform function provided - using raw data")
                    
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {endpoint_url}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                break
                
        logger.info(f"Completed endpoint {endpoint}: Retrieved {endpoint_record_count} records")
    
    # Only upsert if we have data
    if all_transformed_data:
        logger.info(f"\nStarting data Loading... ({len(all_transformed_data)} records)")
        upsert_data(
            transformed_data=all_transformed_data,
            table=table,
            conflict_columns=['api_id'],
            exclude_columns=['id'], 
            batch_size=10000
        )
    else:
        logger.warning("No data to upsert!")
    
    logger.info('=' * 60)
    logger.info(f"ETL Pipeline Completed")
    logger.info(f"Total pages processed: {total_pages_processed}")
    logger.info(f"Total records processed: {len(all_transformed_data)}")
    logger.info("=" * 60)
    
    return all_transformed_data

if __name__ == '__main__':
    logger.info("Starting script")
    logger.info("Initializing ETL pipeline...")
    
    table = "diabetes_ind"
    base_url = 'https://data.cdc.gov/api/v3/views/'
    endpoints = get_endpoint(key_target=table)
    etl_pipeline(base_url=base_url, endpoints=endpoints, pageSize=50000, 
                 transform_data=transform_endpoint_data, transform_single_func=transform_single_diabetes_ind, table=table, max_page=None)
    