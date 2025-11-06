#!/usr/bin/env python3
"""
Test script for Coles Product Price API using RapidAPI
Converts the curl command to Python requests
"""

import json
from pprint import pprint

import requests


def search_coles_products(query="tomato"):
    """
    Search for products on Coles using RapidAPI
    
    Args:
        query (str): Product search query
    
    Returns:
        dict: API response data
    """
    url = "https://coles-product-price-api.p.rapidapi.com/coles/product-search/"
    
    # Query parameters
    params = {
        "query": query
    }
    
    # Headers for RapidAPI
    headers = {
        "x-rapidapi-host": "coles-product-price-api.p.rapidapi.com",
        "x-rapidapi-key": "c812b13e14msh9ed2d3a327cee38p17bfb0jsn7a2e22b13be3"
    }
    
    try:
        # Make the GET request
        response = requests.get(url, headers=headers, params=params)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        print(f"✅ Successfully fetched data for query: '{query}'")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📏 Response size: {len(response.text)} characters")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Raw response: {response.text}")
        return None


def scraper():
    try:
        url = 'https://api.coles.com.au/customer/v1/coles/products/search?limit=20&q=Drinks&start=40&storeId=7716&type=SKU'
        headers = {
            'Accept-Encoding': 'gzip',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': 'Shopmate/3.4.1 (iPhone; iOS 11.4.1; Scale/3.00)',
            'X-Coles-API-Key': '046bc0d4-3854-481f-80dc-85f9e846503d',
            'X-Coles-API-Secret': 'e6ab96ff-453b-45ba-a2be-ae8d7c12cadf',
            'Accept-Language': 'en-AU;q=1'
        }

        r = requests.get(url, headers=headers)

        j = r.json()
        results = j['Results']
        print(len(results))

        for x in results:
            print(x['Name'])

    except requests.exceptions.RequestException as e:
        print(f"❌ Error making request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Raw response: {response.text}")
        return None

def main():
    """Main function to test the API"""
    print("🛒 Testing Coles Product Price API")
    print("=" * 50)
    
    # # Test with tomato search
    # result = search_coles_products("tomato")
    
    # if result:
    #     print("\n📋 API Response:")
    #     print("-" * 30)
    #     pprint(result)
        
    #     # Extract some key information if available
    #     if isinstance(result, dict):
    #         if "products" in result:
    #             print(f"\n🎯 Found {len(result['products'])} products")
    #         elif "data" in result:
    #             print(f"\n📦 Data keys: {list(result['data'].keys()) if isinstance(result['data'], dict) else 'Non-dict data'}")
    # else:
    #     print("❌ Failed to fetch data")

    scraper()

if __name__ == "__main__":
    main()