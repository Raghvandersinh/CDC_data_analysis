import requests 
from pathlib import Path
import json
base_cdc_url = 'https://data.cdc.gov/api/v3/views'

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
    Traverses through a dictionary(specically endpoint() function) by taking user inputs until it reaches the bottom most values.
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


def find_keys_by_value(data, target_value, current_path=None) -> list:
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
    if current_path is None:
        current_path = []
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_path =current_path = [key]
            if value == target_value:
                results.append(new_path)
            elif isinstance(value, dict):
                results.extend(find_keys_by_value(value, target_value, new_path))
    return results

def data_extraction(filter=''):
    """
    Connects to the API Endpoint of our selection(select endpoint), then extracts, then stores it in a json file. 
    Args:
        filter (str, optional): optional parameter to add filters to the API Endpoint
    """
    selected_value = select_endpoint()
    url = f'{base_cdc_url}/{selected_value}/query.json?{filter}'
    response = requests.get(url)
    endpoint_dict = endpoint()
    print('Selected Value: ', selected_value)
    paths = find_keys_by_value(endpoint_dict, selected_value)
    
    if paths:
        for path in paths:
            print(f"Key: {path[0]}")
    else:
        print(f"Value '{selected_value}' not found in dictionary")
    
    if response:
        print(response.status_code)
        data = response.json()
        print(type(data[0]))
        print(len(data[0]))
        with open(f"data/{path[0]}.json", "w") as file:
            json.dump(data, file, indent=4, sort_keys=True)
        #return data 
        # print(response.json())
    else:
        print(response.status_code)
        print(f"Failed to connect to the API Endpoint")
        


data = json.load(open('data/USDSS_ind.json'))
print(len(data))