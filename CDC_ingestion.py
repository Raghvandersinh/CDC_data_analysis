import requests 
from pathlib import Path
import json
base_cdc_url = 'https://data.cdc.gov/api/v3/views'


def endpoint():
    endpoint_path = Path("endpoint/cdc_api_endpoint.json")
    with endpoint_path.open(mode="r", encoding = 'utf-8') as file:
        content = file.read()
        return json.loads(content)

def select_endpoint():
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

def api_connection(filter=''):
    url = f'{base_cdc_url}/{select_endpoint()}/query.json?{filter}'
    response = requests.get(url)
    
    if response:
        print(response.status_code)
        data = response.json()
        print(type(data[0]))
        # print(response.json())
    else:
        print(response.status_code)
        print(f"Failed to connect to the API Endpoint")
        

# api_connection(base_url=base_cdc_url, endpoint=)
print(api_connection())