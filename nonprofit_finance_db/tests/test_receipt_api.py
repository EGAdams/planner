#!/usr/bin/env python3
"""
Test script to directly call the receipt parsing API endpoint.
This allows us to test receipt OCR accuracy without browser UI limitations.
"""
import requests
import json
import base64

def test_receipt_parsing():
    # Read the receipt image
    image_path = "/mnt/c/Users/NewUser/Documents/meijer_vander_vilet_feb_09.jpeg"
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Prepare the multipart form data
    files = {
        'file': ('receipt.jpg', image_data, 'image/jpeg')
    }
    
    # Call the API
    url = "http://localhost:8080/api/parse-receipt"
    print(f"Testing receipt parsing at {url}...")
    print(f"Image: {image_path}\n")
    
    try:
        response = requests.post(url, files=files, timeout=120)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}\n")
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Receipt parsed successfully.\n")
            print(json.dumps(result, indent=2))
            
            # Check for FROZEN PIZZA specifically
            if 'parsed_data' in result and 'items' in result['parsed_data']:
                print("\n" + "="*60)
                print("CHECKING FROZEN PIZZA PRICE:")
                print("="*60)
                for item in result['parsed_data']['items']:
                    if 'FROZEN' in item.get('description', '').upper() and 'PIZZA' in item.get('description', '').upper():
                        price = item.get('unit_price')
                        print(f"Found: {item['description']}")
                        print(f"  Unit Price: ${price}")
                        print(f"  Line Total: ${item.get('line_total')}")
                        
                        if price == 3.99:
                            print("\n[CORRECT] Price is $3.99")
                        elif price == 4.49:
                            print("\n[WRONG] Price is $4.49 (should be $3.99)")
                            print("   OCR still confusing 9 with 4")
                        else:
                            print(f"\n[UNEXPECTED] Price is ${price}")
                        break
                else:
                    print("[WARNING] FROZEN PIZZA not found in items")
        else:
            print(f"[ERROR] Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to API server at http://localhost:8080")
        print("   Make sure the server is running: python api_server.py")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_receipt_parsing()
