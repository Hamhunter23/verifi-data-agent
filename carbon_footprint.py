import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

# Global cache for carbon footprint data
carbon_footprint_cache = {}
CACHE_EXPIRY_SECONDS = 300  # 5 minutes for cache validity

def normalize_carbon_identifier(identifier: str) -> str:
    """
    Normalize carbon footprint identifiers to match the format used in the database.
    Converts identifiers to lowercase for case-insensitive matching.
    """
    if not identifier:
        return identifier
    
    # Convert to lowercase for case-insensitive matching
    return identifier.lower()

async def fetch_carbon_footprint(identifier: str, query_details: Optional[str], timestamp: str) -> Dict[str, Any]:
    """
    Fetches and verifies carbon footprint data for products, companies, or activities.
    
    In a real implementation, this would connect to verified environmental impact 
    data sources and carbon accounting systems.
    """
    # Normalize the identifier for case-insensitive matching
    normalized_identifier = normalize_carbon_identifier(identifier)
    
    # Simulated carbon footprint database - we need to access this first to determine entity type
    simulated_carbon_data = {
        "product": {
            "macbook_pro": {
                "name": "EcoBook Pro 2023",
                "manufacturer": "GreenTech Inc.",
                "totalFootprint": 185.3,  # kg CO2e
                "footprintBreakdown": {
                    "manufacturing": 142.8,
                    "transportation": 12.5,
                    "usage": 30.0,  # Over estimated product lifecycle
                    "endOfLife": 0.0  # Carbon neutral recycling program
                },
                "certifications": ["Carbon Trust", "Energy Star", "EPEAT Gold"],
                "methodology": "ISO 14067 / GHG Protocol",
                "verificationBody": "ClimateVerify Alliance",
                "verificationDate": "2023-07-15"
            },
            "sustainable_blend": {
                "name": "Sustainable Blend Coffee",
                "manufacturer": "EcoBeans Co.",
                "totalFootprint": 0.15,  # kg CO2e per cup
                "footprintBreakdown": {
                    "farming": 0.05,
                    "processing": 0.03,
                    "packaging": 0.02,
                    "transportation": 0.04,
                    "preparation": 0.01
                },
                "offsetting": "100% offset through verified reforestation projects",
                "certifications": ["Rainforest Alliance", "Carbon Neutral Product"],
                "methodology": "PAS 2050",
                "verificationBody": "GreenCertify DAO",
                "verificationDate": "2023-08-10"
            }
        },
        "company": {
            "greencorp": {
                "name": "GreenCorp Technologies",
                "industry": "Technology",
                "totalEmissions": 12500.0,  # metric tons CO2e
                "emissionsBreakdown": {
                    "scope1": 2000.0,  # Direct emissions
                    "scope2": 8000.0,  # Indirect emissions from energy
                    "scope3": 2500.0   # Value chain emissions
                },
                "reductionTarget": "50% by 2030, Net Zero by 2040",
                "verificationStandard": "GHG Protocol Corporate Standard",
                "verifier": "ClimateAccounting Consortium",
                "verificationDate": "2023-04-20"
            },
            "fashion_forward": {
                "name": "FashionX Sustainable Apparel",
                "industry": "Fashion",
                "totalEmissions": 18700.0,  # metric tons CO2e
                "emissionsBreakdown": {
                    "scope1": 1200.0,
                    "scope2": 4500.0,
                    "scope3": 13000.0  # Significant supply chain emissions
                },
                "reductionActions": [
                    "100% renewable energy in owned facilities",
                    "Sustainable materials sourcing",
                    "Supply chain optimization"
                ],
                "reductionTarget": "Net Zero by 2035",
                "verificationStandard": "Science Based Targets initiative (SBTi)",
                "verifier": "SustainableVerify Network",
                "verificationDate": "2023-03-15"
            }
        },
        "activity": {
            "london_nyc_flight": {
                "type": "Flight",
                "route": "London to New York (economy)",
                "distance": 5585,  # km
                "footprint": 986.0,  # kg CO2e
                "calculationMethod": "DEFRA 2023 emission factors",
                "verifier": "TravelImpact Verifiers",
                "offsetOptions": [
                    {"project": "Wind Energy India", "cost": "€12.50"},
                    {"project": "Reforestation Brazil", "cost": "€15.75"}
                ]
            },
            "california_electricity": {
                "type": "Electricity Consumption",
                "location": "California, USA",
                "amount": 1000,  # kWh
                "footprint": 210.0,  # kg CO2e
                "gridMix": {
                    "renewable": 33.0,  # percentage
                    "natural_gas": 40.0,
                    "nuclear": 15.0,
                    "coal": 10.0,
                    "other": 2.0
                },
                "calculationMethod": "eGRID 2022 (location-based)",
                "verifier": "GridImpact Alliance",
                "verificationDate": "2023-02-10"
            }
        }
    }
    
    # First, check if a specific scope was requested in query_details
    requested_scope = None
    if query_details:
        if "scope=company" in query_details:
            requested_scope = "company"
        elif "scope=product" in query_details:
            requested_scope = "product"
        elif "scope=activity" in query_details:
            requested_scope = "activity"
    
    # Auto-detect entity type by checking which scope the identifier exists in
    detected_scope = None
    for scope in ["product", "company", "activity"]:
        if normalized_identifier in simulated_carbon_data[scope]:
            detected_scope = scope
            break
    
    # Determine the final scope to use
    # Priority: 1) Explicitly requested scope (if entity exists there)
    #           2) Auto-detected scope
    #           3) Default to "product" if nothing else works
    data_scope = "product"  # Default fallback
    
    if requested_scope and normalized_identifier in simulated_carbon_data[requested_scope]:
        # Use explicitly requested scope if the entity exists in that scope
        data_scope = requested_scope
    elif detected_scope:
        # Use auto-detected scope if found
        data_scope = detected_scope
    
    # Cache key for carbon data
    cache_key = f"carbon_{data_scope}_{normalized_identifier}"
    
    # Check cache first
    if cache_key in carbon_footprint_cache and (datetime.utcnow() - carbon_footprint_cache[cache_key]["cached_at"]).total_seconds() < CACHE_EXPIRY_SECONDS:
        carbon_data = carbon_footprint_cache[cache_key]["data"]
    else:
        # Retrieve data for the determined scope
        carbon_data = None
        if normalized_identifier in simulated_carbon_data[data_scope]:
            carbon_data = simulated_carbon_data[data_scope][normalized_identifier]
            
            # Update cache
            carbon_footprint_cache[cache_key] = {
                "data": carbon_data,
                "cached_at": datetime.utcnow()
            }
    
    if carbon_data:
        # Generate verification proof (simulated)
        verification_proof = {
            "method": "Multi-Attestation Protocol",
            "hash": hashlib.sha256(json.dumps(carbon_data).encode()).hexdigest(),
            "timestamp": timestamp
        }
        
        # Format response based on scope
        if data_scope == "product":
            data_payload = {
                "productInfo": {
                    "name": carbon_data["name"],
                    "manufacturer": carbon_data["manufacturer"]
                },
                "carbonFootprint": {
                    "total": carbon_data["totalFootprint"],
                    "unit": "kg CO2e",
                    "breakdown": carbon_data["footprintBreakdown"]
                },
                "certifications": carbon_data.get("certifications", []),
                "verification": {
                    "methodology": carbon_data.get("methodology", ""),
                    "verifier": carbon_data.get("verificationBody", ""),
                    "date": carbon_data.get("verificationDate", ""),
                    "proof": verification_proof
                }
            }
        elif data_scope == "company":
            data_payload = {
                "companyInfo": {
                    "name": carbon_data["name"],
                    "industry": carbon_data["industry"]
                },
                "emissions": {
                    "total": carbon_data["totalEmissions"],
                    "unit": "metric tons CO2e",
                    "breakdown": carbon_data["emissionsBreakdown"]
                },
                "targets": carbon_data.get("reductionTarget", ""),
                "verification": {
                    "standard": carbon_data.get("verificationStandard", ""),
                    "verifier": carbon_data.get("verifier", ""),
                    "date": carbon_data.get("verificationDate", ""),
                    "proof": verification_proof
                }
            }
        else:  # activity
            data_payload = {
                "activityInfo": {
                    "type": carbon_data["type"],
                    "details": carbon_data.get("route", "") or carbon_data.get("location", "")
                },
                "carbonFootprint": {
                    "total": carbon_data["footprint"],
                    "unit": "kg CO2e",
                    "distance": carbon_data.get("distance", None),
                    "amount": carbon_data.get("amount", None)
                },
                "methodology": carbon_data.get("calculationMethod", ""),
                "verification": {
                    "verifier": carbon_data.get("verifier", ""),
                    "date": carbon_data.get("verificationDate", ""),
                    "proof": verification_proof
                }
            }
        
        return {
            "request_data_type": "carbon_footprint",
            "request_identifier": identifier,
            "source_description": "Verified Carbon Accounting Network",
            "data_payload": data_payload,
            "verification_summary": f"Carbon footprint data verified following {carbon_data.get('methodology', carbon_data.get('verificationStandard', 'international standards'))} by {carbon_data.get('verificationBody', carbon_data.get('verifier', 'accredited verifier'))}.",
            "timestamp": timestamp
        }
    else:
        # Provide a more helpful error message that lists the scopes we checked
        if requested_scope:
            error_message = f"No carbon footprint information found for {requested_scope} identifier '{identifier}'."
        elif detected_scope is None:
            scopes_checked = ", ".join(["product", "company", "activity"])
            error_message = f"No carbon footprint information found for identifier '{identifier}' in any scope ({scopes_checked})."
        else:
            # This should never happen (detected but not retrieved)
            error_message = f"Error retrieving carbon footprint information for {detected_scope} '{identifier}'."
            
        return {
            "request_data_type": "carbon_footprint",
            "request_identifier": identifier,
            "source_description": "Carbon Footprint Verification Network",
            "data_payload": {},
            "verification_summary": f"No carbon footprint data found.",
            "timestamp": timestamp,
            "error_message": error_message
        } 