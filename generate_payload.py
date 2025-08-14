import json
import os

# Path to your original claims.json
claims_file_path = os.path.join('data', 'claims.json')
# Path for the new payload file
payload_file_path = os.path.join('data', 'request_payload.json')

try:
    with open(claims_file_path, 'r', encoding='utf-8') as f:
        claims_data = json.load(f)

    # Create the dictionary that matches your FastAPI model
    request_payload = {"claims": claims_data}

    with open(payload_file_path, 'w', encoding='utf-8') as f:
        json.dump(request_payload, f, indent=2)

    print(f"Successfully generated {payload_file_path}")
except FileNotFoundError:
    print(f"Error: {claims_file_path} not found.")
except json.JSONDecodeError:
    print(f"Error: Invalid JSON in {claims_file_path}.")