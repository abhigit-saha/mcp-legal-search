"""
SerpAPI client for legal document searches.
"""
import asyncio
import json
from typing import Dict, Any
from serpapi import GoogleSearch
from mcp_flight_search.utils.logging import logger
from mcp_flight_search.config import SERP_API_KEY

async def run_search(params: Dict[str, Any]):
    """
    Run SerpAPI search asynchronously.
    
    Args:
        params: Parameters for the SerpAPI search
        
    Returns:
        Search results from SerpAPI
    """
    try:
        logger.debug(f"Sending SerpAPI request with params: {json.dumps(params, indent=2)}")
        result = await asyncio.to_thread(lambda: GoogleSearch(params).get_dict())
        logger.debug(f"SerpAPI response received, keys: {list(result.keys())}")
        return result
    except Exception as e:
        logger.exception(f"SerpAPI search error: {str(e)}")
        return {"error": str(e)}

def prepare_legal_search_params(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare parameters for a legal document search.
    
    Args:
        analysis: Contract analysis results containing location, type, and key terms
        
    Returns:
        Dictionary of parameters for SerpAPI Google search
    """
    # Build search query based on analysis
    query_parts = []
    
    # Add contract type with specific document formats
    contract_type = analysis.get("contract_type", "contract")
    query_parts.append(f'"{contract_type} contract" filetype:pdf OR filetype:doc OR filetype:docx')
    
    # Add location if specified
    location = analysis.get("location", "")
    if location and location != "Location not specified":
        query_parts.append(f'"{location}"')
    
    # Add key terms
    key_terms = analysis.get("key_terms", [])
    if key_terms and key_terms != ["Standard contract terms"]:
        # Add most relevant terms
        for term in key_terms[:2]:  # Limit to avoid too long query
            if len(term) > 3:  # Skip very short terms
                query_parts.append(f'"{term}"')
    
    # Add legal-specific search terms and document sources
    legal_terms = [
        "agreement template",
        "legal document sample",
        "contract form",
        "site:sec.gov OR site:courts.gov OR site:justia.com OR site:findlaw.com OR site:lawinsider.com OR site:contractstandards.com"
    ]
    query_parts.extend(legal_terms)
    
    # Build final query
    query = " ".join(query_parts)
    
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google",
        "q": query,
        "hl": "en",
        "gl": "us",
        "num": 15,  # Increase number of results
        "filter": "1"  # Enable filtering for better results
    }
    
    logger.debug(f"Legal search query: {query}")
    return params

# Keep the old function for backward compatibility (in case it's used elsewhere)
def prepare_flight_search_params(origin: str, destination: str, outbound_date: str, return_date: str = None) -> Dict[str, Any]:
    """
    Prepare parameters for a flight search (deprecated - kept for compatibility).
    
    Args:
        origin: Departure airport code
        destination: Arrival airport code
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round trips (YYYY-MM-DD)
        
    Returns:
        Dictionary of parameters for SerpAPI
    """
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "departure_id": origin.strip().upper(),
        "arrival_id": destination.strip().upper(),
        "outbound_date": outbound_date,
        "currency": "USD",
        "type": "2"  # One-way trip by default
    }
    
    # Add return date if provided (making it a round trip)
    if return_date:
        logger.debug("Round trip detected, adding return_date and setting type=1")
        params["return_date"] = return_date
        params["type"] = "1"  # Set to round trip
    else:
        logger.debug("One-way trip detected, type=2")
    
    return params 