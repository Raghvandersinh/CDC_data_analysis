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


def grouped_endpoints() -> dict:
    endpoints = ''
    user_input = None
    
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
    
    return grouped_data
    
def data_extraction_streaming(filter=''):
    """
    Extracts 10,000 records from API, immediately inserts into DuckDB,
    then fetches the next batch. True streaming pipeline.
    """
    
    base_cdc_url = 'https://data.cdc.gov/api/v3/views'
    PAGE_SIZE = 100000  
    MAX_RETRIES = 3
    BATCH_SIZE = 50000
    
    grouped_data = grouped_endpoints()
    
    # Create pipeline
    pipeline = dlt.pipeline(
        pipeline_name="cdc_separate_indicator",
        destination="duckdb",
        dataset_name="cdc_health_data"
    )

    for indicator, endpoint_ids in grouped_data.items():
        print(f"\n{'='*60}")
        print(f"Processing: {indicator}")
        print(f"{'='*60}")
        
        # Process each endpoint
        for endpoint_id in endpoint_ids:
            print(f"\nStreaming endpoint: {endpoint_id}")
            
            page_number = 1
            has_more = True
            retry_count = 0
            total_extracted = 0
            
            while has_more:
                try:
                    # ===== STEP 1: EXTRACT =====
                    print(f" EXTRACTING: Page {page_number} from API...")
                    
                    url = f"{base_cdc_url}/{endpoint_id}/query.json"
                    params = {
                        'pageNumber': page_number,
                        'pageSize': PAGE_SIZE
                    }
                    if filter:
                        params['query'] = filter
                    
                    response = requests.get(url, params=params, timeout=60)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data or not isinstance(data, list) or len(data) == 0:
                        print(f"No more data to extract")
                        break
                    
                    # Enrich data with metadata
                    for record in data:
                        record['_indicator'] = indicator
                        record['_endpoint_id'] = endpoint_id
                        record['_page_number'] = page_number
                    
                    records_extracted = len(data)
                    total_extracted += records_extracted
                    print(f"EXTRACTED: {records_extracted:,} records (Total: {total_extracted:,})")
                    
                    # ===== STEP 2: INSERT IN BATCHES OF 10,000 =====
                    # Split extracted data into 10,000 record batches and insert each
                    for i in range(0, len(data), BATCH_SIZE):
                        batch = data[i:i + BATCH_SIZE]
                        batch_num = (i // BATCH_SIZE) + 1
                        
                        print(f"INSERTING: Batch {batch_num} ({len(batch):,} records)...")
                        
                        # Create temporary source for this batch
                        @dlt.source
                        def batch_source():
                            @dlt.resource(
                                name=indicator.lower().replace(' ', '_'),
                                write_disposition="append"
                            )
                            def batch_data():
                                yield batch
                            return batch_data
                        
                        # Run immediate insert
                        load_info = pipeline.run(batch_source())
                        print(f"INSERTED: Batch {batch_num} complete")
                    
                    # Check if we need more pages
                    if records_extracted < PAGE_SIZE:
                        has_more = False
                        print(f"Completed endpoint {endpoint_id}: {total_extracted:,} total records")
                    else:
                        page_number += 1
                        retry_count = 0
                    
                    # Small delay between pages
                    time.sleep(0.3)
                    
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count <= MAX_RETRIES:
                        print(f"Timeout, retry {retry_count}/{MAX_RETRIES}...")
                        time.sleep(2 * retry_count)
                    else:
                        print(f"Max retries exceeded")
                        break
                        
                except Exception as e:
                    print(f" Error: {e}")
                    break
        
        # Delay between endpoints
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("STREAMING EXTRACTION COMPLETE")
    print(f"{'='*60}")
    
if __name__ == "__main__":
    data_extraction_streaming()
