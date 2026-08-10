from pathlib import Path
import json
import duckdb
from dataclasses import field
from typing import Dict, List, Any, Generator
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from sqlalchemy.orm import Session
import time 
import logging
import requests

logging.basicConfig(level=logging.INFO)

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
        dict: returns the content of the json file
    """
    endpoint_path = Path("endpoint/cdc_api_endpoint.json")
    with endpoint_path.open(mode="r", encoding = 'utf-8') as file:
        content = file.read()
        return json.loads(content)
    
def get_endpoint(key_target:str) -> list:
    endpoints = endpoints_dict()
    return endpoints[key_target.lower()]

def transform_diabetes_ind(data:list = None) -> list:
    res = []
    print(data[0].keys())
    for di in data:
        res.append({
            'year': di.get('year'),
            'indicator':di.get('indicator'),
            'unit':di.get('unit'),
            'estimate': float(di.get('estimate', 0)) or None,
            'se_estimate': float(di.get('seestimate', 0)) or None,
            'lower_limit': float(di.get('lowerlimit', 0)) or None,
            'upper_limit': float(di.get('upperlimit',0)) or None,
            'population': di.get('population'),
            'age': di.get('age'),
            'race': di.get('race'),
            'sex': di.get('sex'),
            'education': di.get('education'),
            'other_info': di.get('other_stratification')
        })
    return res 
def etl_pipeline(base_url:str, endpoints:list, pageSize:int, transform_data: list):
    page = 1
    for endpoint in endpoints:
        endpoint_url = f"{base_url}{endpoint}"
        loop_count = 10
        while loop_count != 0:
            parameter = {
                'pageSize': pageSize,
                'pageNumber': page
            }
            response = requests.get(endpoint_url, params=parameter)
            data = response.json()
            transformed_data = transform_data(data) 
            print(data[0:10])
            print(transformed_data[0:10])
            if len(data) <= pageSize:
                break
            

if __name__ == '__main__':
    base_url = 'https://data.cdc.gov/api/v3/views/'
    endpoints = get_endpoint(key_target="diabetes_ind")
    etl_pipeline(base_url=base_url, endpoints=endpoints, pageSize=10000, transform_data=transform_diabetes_ind)
    