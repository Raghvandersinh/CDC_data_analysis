from pathlib import Path
import json
import dlt
from dlt.sources.helpers import requests
import duckdb
from dataclasses import field
from typing import Dict, List, Any
import time 


def json_length(filename:str) -> int:
    json_path = json.load(open(filename))
    return len(json_path)

def endpoint() -> dict:
    """
    Opens and reads the /endpoint/cdc_api_endpoint.json, which contains list of API endpoint identifier
    Returns:
        dict: returns the content of the json file
    """
    endpoint_path = Path("endpoint/cdc_api_endpoint.json")
    with endpoint_path.open(mode="r", encoding = 'utf-8') as file:
        content = file.read()
        return json.loads(content)


def select_endpoint() -> str:
    """
    Traverses through a endpoint/cdc_api_endpoint.json by taking user inputs until it reaches the bottom most values.
    The bottom most value being API endpoints identifier
    Returns:
        str: returns the API endpoint identifier 
    """
    current_level = endpoint()
    path = []
    
    while isinstance(current_level, dict):
        keys = list(current_level.keys())
        
        print(f"\n{'='*50}")
        print(f"Current path: {' -> '.join(path) if path else 'Root'}")
        print(f"\nAvailable options: ")
        
        for idx, key in enumerate(keys, 1):
            value_preview = current_level[key]
            if isinstance(value_preview, dict):
                preview = f"{{...}} {len(value_preview)} key(s)"
            else:
                preview = f"'{value_preview}'"
            print(f" {idx}, {key} -> {preview}")

        user_choice = input("Enter a key to explore endpoints deeper(or type 'exit'): ").strip()
        
        if user_choice.lower() == 'exit':
            print("Exiting traversal")
            break
        
        if user_choice.isdigit():
            choice_idx = int(user_choice) - 1
            if 0 <= choice_idx < len(keys):
                selected_key = keys[choice_idx]
                print(f"Selected: {selected_key}")
            else:
                print(f"Invaild Number! Please choose 1-{len(keys)}")
                continue
        else:
            selected_key = user_choice
            
        if selected_key in current_level:
            path.append(selected_key)
            current_level = current_level[selected_key]
            
            if not isinstance(current_level, dict):
                # Leaf node reached
                print(f"\n{'='*50}")
                print(f"Final reached value!")
                print(f"Path: {' -> '.join(path)}")
                print(f"Value: {current_level}")
                print(f"{'='*50}")
                return current_level
        else:
            print(f"❌ Invalid selection! Please choose from the options above.")
            continue
    
    return current_level

def get_all_endpoint(res = [], d = None) -> list: 
    """
    Traverse through "endpoint/cdc_api_endpoint.json" and returns all the API endpoint identifiers

    Args:
        res (list, optional): keep it empty, stores our outputs.
        d (dict, optional): Keep it None, it gets the "endpoint/cdc_api_endpoint.json" dict.

    Returns:
        list: returns list of API indentifier endpoints. 
    """
    if d is None:
        d = endpoint()
        
    for k, v in d.items():
        if isinstance(v, dict):
            get_all_endpoint(d = v)
        else:
            res.append(v)
    return res
    

def find_keys_by_value(data = None, target_value = None, current_path=None) -> list:
    """
    Traverse the dictionary(endpoint() function) to find the key of the targeted_value.
    Uses Recursion since we are working with a nested dictionary, hence the current_path comes in handy.
    
    e.g 
    Top_Layer(data) -> If not found -> go one level down new_path(current_path) -> start all over

    Args:
        data (dict): dictionary we are working with 
        target_value (str): the dict value which will help us find its key
        current_path (dict, optional): current location of the traversal. 

    Returns:
        list: returns list of keys
    """
    if data is None:
        data = endpoint()
    if current_path is None:
        current_path = []
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = current_path + [key]
            if isinstance(value, dict):
                if target_value in value.values():
                    results.append(key)
                results.extend(find_keys_by_value(value, target_value, new_path))
    return results


def data_extraction(filter=''):
    """
    Connects to the API Endpoint of our selection, then extracts and stores it in DuckDB.
    Uses pageNumber and pageSize for pagination.
    """
    endpoints = ''
    user_input = None
    base_cdc_url = 'https://data.cdc.gov/api/v3/views'
    
    # Pagination settings - confirmed working format
    PAGE_SIZE = 10000  # Number of records per page
    MAX_RETRIES = 3

    # Get user selection
    while user_input is None: 
        print("1. Select a endpoint")
        print("2. All endpoints")
        print("Type 'exit' to leave")
        user_input = input("Select(by number): ")
        print('\n')
        
        if user_input == '1':
            endpoint = select_endpoint()
            endpoints = [endpoint]
            break
        elif user_input == '2':
            endpoints = get_all_endpoint()
            break
        elif user_input.lower() == "exit":
            return
        else: 
            print("Thats not an option.")
            user_input = None
            continue
    
    # Create key-value pairs
    endpoint_key_pair = []
    for i in endpoints:
        key = find_keys_by_value(target_value=i)
        if key:
            endpoint_key_pair.append([key[0], i])
    
    # Group by indicator
    grouped_data: Dict[str, List[str]] = {}
    for indicator, endpoint_id in endpoint_key_pair:
        if indicator not in grouped_data:
            grouped_data[indicator] = []
        grouped_data[indicator].append(endpoint_id)
    
    # Create pipeline once
    pipeline = dlt.pipeline(
        pipeline_name="cdc_separate_indicator",
        destination="duckdb",
        dataset_name="cdc_health_data"
    )
    
    # Process each indicator separately
    for indicator, endpoint_ids in grouped_data.items():
        print(f"\n{'='*60}")
        print(f"Processing: {indicator}")
        print(f"Endpoints: {endpoint_ids}")
        print(f"{'='*60}")
        
        # Create source for this specific indicator
        @dlt.source
        def indicator_source():
            
            @dlt.resource(
                name=indicator.lower().replace(' ', '_'),
                write_disposition="replace"
            )
            def fetch_indicator_data():
                for endpoint_id in endpoint_ids:
                    print(f"\n  → Fetching endpoint: {endpoint_id}")
                    
                    page_number = 1
                    total_records = 0
                    has_more = True
                    retry_count = 0
                    
                    while has_more:
                        try:
                            # Build URL with working pagination format
                            url = f"{base_cdc_url}/{endpoint_id}/query.json"
                            
                            # Correct pagination parameters
                            params = {
                                'pageNumber': page_number,
                                'pageSize': PAGE_SIZE
                            }
                            
                            # Add any filter if provided
                            if filter:
                                params['query'] = filter
                            
                            print(f"Fetching page {page_number} (pageSize: {PAGE_SIZE})")
                            
                            response = requests.get(url, params=params, timeout=60)
                            response.raise_for_status()
                            data = response.json()
                            
                            # Check if we got data
                            if not data or not isinstance(data, list):
                                print(f"No more data at page {page_number}")
                                has_more = False
                                break
                            
                            records_in_page = len(data)
                            
                            # If we got 0 records, we're done
                            if records_in_page == 0:
                                print(f"No more data")
                                has_more = False
                                break
                            
                            total_records += records_in_page
                            
                            # Yield each record with metadata
                            for record in data:
                                record['_indicator'] = indicator
                                record['_endpoint_id'] = endpoint_id
                                record['_page_number'] = page_number
                                yield record
                            
                            print(f"Page {page_number}: {records_in_page} records (total: {total_records:,})")
                            
                            # If we got fewer records than page size, we're done
                            if records_in_page < PAGE_SIZE:
                                has_more = False
                                print(f"Completed {endpoint_id}: {total_records:,} total records")
                            else:
                                page_number += 1
                                retry_count = 0  # Reset retry count on success
                            
                        except requests.exceptions.Timeout:
                            retry_count += 1
                            if retry_count <= MAX_RETRIES:
                                print(f"Timeout on page {page_number}, retry {retry_count}/{MAX_RETRIES}...")
                                time.sleep(2 * retry_count)
                            else:
                                print(f"Max retries exceeded for page {page_number}")
                                has_more = False
                                yield {
                                    '_indicator': indicator,
                                    '_endpoint_id': endpoint_id,
                                    '_page': page_number,
                                    '_error': 'Max retries exceeded'
                                }
                            
                        except Exception as e:
                            print(f"Error on page {page_number}: {e}")
                            has_more = False
                            yield {
                                '_indicator': indicator,
                                '_endpoint_id': endpoint_id,
                                '_page': page_number,
                                '_error': str(e)
                            }
                        
                        # Small delay between requests
                        if has_more:
                            time.sleep(0.3)
            
            return fetch_indicator_data
        
        # Load this indicator's data
        try:
            print(f"\nLoading {indicator} to DuckDB...")
            load_info = pipeline.run(indicator_source())
            print(f"Successfully loaded {indicator}")
            
        except Exception as e:
            print(f"Failed to load {indicator}: {e}")
            continue
        
        # Delay between indicators
        time.sleep(2)
    
    # Display final results
    print(f"\n{'='*60}")
    print("LOADING COMPLETE - Summary")
    print(f"{'='*60}")
    
    try:
        with pipeline.sql_client() as client:
            # Execute the query and get results
            result = client.execute_query("SHOW TABLES")
            tables = result.fetchall()
            
            print("\nCreated tables:")
            total_rows = 0
            for table in tables:
                table_name = table[0]
                count_result = client.execute_query(f"SELECT COUNT(*) FROM {table_name}")
                count = count_result.fetchone()[0]
                total_rows += count
                print(f"  - {table_name}: {count:,} rows")
            
            print(f"\nTOTAL RECORDS LOADED: {total_rows:,}")
            
            # Show sample data
            print("\nSample data (first 3 rows):")
            for table in tables:
                table_name = table[0]
                print(f"\n  {table_name}:")
                sample_result = client.execute_query(f"SELECT * FROM {table_name} LIMIT 3")
                sample = sample_result.fetchall()
                print(sample)
                
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    data_extraction()
