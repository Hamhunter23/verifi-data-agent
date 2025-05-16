import asyncio
import httpx
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import specialized data handler modules
from education_credentials import fetch_education_credential
from supply_chain import fetch_supply_chain_status
from carbon_footprint import fetch_carbon_footprint
from reputation_score import fetch_reputation_score

# CoinGecko API base URL
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Global cache for data that doesn't change frequently
data_cache = {}
CACHE_EXPIRY_SECONDS = 300  # 5 minutes for cache validity

async def fetch_verifiable_data(
    data_type: str, 
    identifier: str, 
    query_details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Asynchronously fetches verifiable data.
    Routes requests to specialized data handlers based on data_type.
    
    Args:
        data_type: The type of data to fetch (e.g., "crypto_price", "education_credential").
        identifier: The ID of the entity (e.g., "bitcoin", "user123").
        query_details: Optional. Additional parameters for the query.
    
    Returns:
        A dictionary containing the fetched data or an error message.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Route to appropriate data handler based on data_type
    if data_type.lower() == "crypto_price":
        return await fetch_crypto_price(identifier, query_details, timestamp)
    elif data_type.lower() == "education_credential":
        return await fetch_education_credential(identifier, query_details, timestamp)
    elif data_type.lower() == "supply_chain_status":
        return await fetch_supply_chain_status(identifier, query_details, timestamp)
    elif data_type.lower() == "carbon_footprint":
        return await fetch_carbon_footprint(identifier, query_details, timestamp)
    elif data_type.lower() == "reputation_score":
        return await fetch_reputation_score(identifier, query_details, timestamp)
    else:
        return {
            "request_data_type": data_type,
            "request_identifier": identifier,
            "source_description": "Data Handler System",
            "data_payload": {},
            "verification_summary": "Data type not supported by this handler.",
            "timestamp": timestamp,
            "error_message": f"Unsupported data_type: '{data_type}'. Supported types: 'crypto_price', 'education_credential', 'supply_chain_status', 'carbon_footprint', 'reputation_score'."
        }

async def fetch_crypto_price(identifier: str, query_details: Optional[str], timestamp: str) -> Dict[str, Any]:
    """
    Fetches cryptocurrency price data from CoinGecko.
    """
    vs_currency = "usd"  # Default comparison currency
    if query_details and "vs_currency=" in query_details:
        vs_currency = query_details.split("vs_currency=")[-1]

    url = f"{COINGECKO_API_URL}/simple/price?ids={identifier}&vs_currencies={vs_currency}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            api_data = response.json()

        if identifier in api_data and vs_currency in api_data[identifier]:
            price = api_data[identifier][vs_currency]
            return {
                "request_data_type": "crypto_price",
                "request_identifier": identifier,
                "source_description": "CoinGecko API (https://www.coingecko.com/en/api)",
                "data_payload": {
                    "price": price,
                    "currency": vs_currency,
                    "asset_id": identifier
                },
                "verification_summary": "Data fetched live from CoinGecko API. Accuracy subject to API provider.",
                "timestamp": timestamp
            }
        else:
            return {
                "request_data_type": "crypto_price",
                "request_identifier": identifier,
                "source_description": "CoinGecko API",
                "data_payload": {},
                "verification_summary": "Data source did not return expected format or identifier not found.",
                "timestamp": timestamp,
                "error_message": f"Data not found for identifier '{identifier}' with currency '{vs_currency}' from CoinGecko. Response: {api_data}"
            }

    except httpx.HTTPStatusError as e:
        return {
            "request_data_type": "crypto_price",
            "request_identifier": identifier,
            "source_description": "CoinGecko API",
            "data_payload": {},
            "verification_summary": "Error communicating with data source.",
            "timestamp": timestamp,
            "error_message": f"HTTP error fetching data from CoinGecko: {e.response.status_code} - {e.response.text}"
        }
    except httpx.RequestError as e:
        return {
            "request_data_type": "crypto_price",
            "request_identifier": identifier,
            "source_description": "CoinGecko API",
            "data_payload": {},
            "verification_summary": "Error communicating with data source.",
            "timestamp": timestamp,
            "error_message": f"Request error fetching data from CoinGecko: {str(e)}"
        }
    except Exception as e:
        return {
            "request_data_type": "crypto_price",
            "request_identifier": identifier,
            "source_description": "CoinGecko API",
            "data_payload": {},
            "verification_summary": "An unexpected error occurred.",
            "timestamp": timestamp,
            "error_message": f"An unexpected error occurred while fetching data: {str(e)}"
        }

# Example usage (can be run directly for testing this module)
if __name__ == '__main__':
    async def main_test():
        # Test case 1: Fetch Bitcoin price in USD
        result1 = await fetch_verifiable_data("crypto_price", "bitcoin", "vs_currency=usd")
        print("Result 1 (Bitcoin price):")
        print(result1)

        # Test case 2: Fetch Ethereum price in EUR
        result2 = await fetch_verifiable_data("crypto_price", "ethereum", "vs_currency=eur")
        print("\nResult 2 (Ethereum price in EUR):")
        print(result2)

        # Test case 3: Fetch education credential
        result3 = await fetch_verifiable_data("education_credential", "user456")
        print("\nResult 3 (Education Credential):")
        print(result3)
        
        # Test case 4: Fetch supply chain status
        result4 = await fetch_verifiable_data("supply_chain_status", "product123")
        print("\nResult 4 (Supply Chain Status):")
        print(result4)
        
        # Test case 5: Fetch carbon footprint
        result5 = await fetch_verifiable_data("carbon_footprint", "laptop123")
        print("\nResult 5 (Carbon Footprint):")
        print(result5)
        
        # Test case 6: Fetch reputation score
        result6 = await fetch_verifiable_data("reputation_score", "developer123", "aspect=developer")
        print("\nResult 6 (Reputation Score):")
        print(result6)
        
        # Test case 7: Unsupported data type
        result7 = await fetch_verifiable_data("stock_price", "aapl")
        print("\nResult 7 (Unsupported data type):")
        print(result7)

    asyncio.run(main_test())