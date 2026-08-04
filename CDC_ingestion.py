from pathlib import Path
import json
import dlt
from dlt.sources.helpers import requests
import duckdb
from dataclasses import field
from typing import Dict, List, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from sqlalchemy.orm import Session

def json_length(filename:str) -> int:
    json_path = json.load(open(filename))
    return len(json_path)

def endpoints_dict() -> dict:
    """
    Opens and reads the /endpoint/cdc_api_endpoint.json, which contains list of API endpoint identifier
    Returns:
        dict: returns the content of the json file
    """
    endpoint_path = Path("endpoint/cdc_api_endpoint.json")
    with endpoint_path.open(mode="r", encoding = 'utf-8') as file:
        content = file.read()
        return json.loads(content)
    
def get_endpoint(key_target:str) -> list:
    endpoints = endpoints_dict()
    return  endpoints[key_target.lower()]

@dlt.source
def cdc_api(base_url: str = "https://data.cdc.gov/api/v3/views"):
    """
    Source that combines multiple API endpoints. 
    Returns multiple resources that create separate tables. 
    Args:
        base_url (_type_, optional): base CDC API URL. Defaults to "https://data.cdc.gov/api/v3/views".
    """
    return[
        diabetes_indicator(base_url=base_url)
    ]

@dlt.resource(
    table_name= "diabetes_ind",
    write_disposition="replace"
)
def diabetes_indicator(base_url: str):
    diabetes_ind_endpoint = get_endpoint(key_target="diabetes_indicator")
    PAGE_SIZE = 10000
    page = 1
    endpoint = f"{base_url}/{diabetes_ind_endpoint[0]}/query.json"
    
    while True:
        parameter = {
                "pageNumber":page,
                "pageSize":PAGE_SIZE
        }
        response = requests.get(
            endpoint,
            params=parameter
        )
        response.raise_for_status()
        data = response.json()
        
        if not data:
            break
        print(page)
        for di in data:
            yield{
                'year': di.get('year'),
                'indicator': di.get("indicator"),
                'unit': di.get('unit'),
                'estimates': di.get("estimate"),
                'se_estimates': di.get("seestimate"),
                'lower_limit': di.get('lowerlimit'),
                'upper_limit': di.get('upperlimit'),
                'population': di.get('population'),
                'age': di.get('age'),
                'race': di.get('race'),
                'sex': di.get('sex'),
                'education': di.get('education'),
                'other_info': di.get('other_stratification')
            }
            
        page += 1
if __name__ == "__main__":
    
    
    # Run dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="cdc_analysis_pipeline",
        destination='postgres',
        dataset_name="cdc_analysis"
    )
    load_info = pipeline.run(cdc_api())
    print(load_info)
    