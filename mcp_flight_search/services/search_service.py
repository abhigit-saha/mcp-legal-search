"""
Legal contract search service implementation.
"""
from typing import List, Dict, Optional, Any
from mcp_flight_search.utils.logging import logger
from mcp_flight_search.services.serpapi_client import run_search, prepare_legal_search_params
from mcp_flight_search.config import SERP_API_KEY
import re

async def analyze_and_search_contracts(contract_text: str) -> Dict[str, Any]:
    """
    Analyze a legal contract and search for similar documents.
    
    Args:
        contract_text: The full text of the legal contract to analyze
        
    Returns:
        A dictionary containing contract analysis and similar documents
    """
    logger.info(f"Analyzing contract text of length: {len(contract_text)}")
    
    # Step 1: Analyze the contract
    analysis = analyze_contract(contract_text)
    logger.info(f"Contract analysis complete: Type={analysis['contract_type']}, Location={analysis['location']}")
    
    # Step 2: Search for similar contracts
    similar_contracts = await search_similar_contracts(analysis)
    
    return {
        "analysis": analysis,
        "similar_contracts": similar_contracts
    }

def analyze_contract(contract_text: str) -> Dict[str, Any]:
    """
    Analyze contract text to extract key information.
    
    Args:
        contract_text: The contract text to analyze
        
    Returns:
        Dictionary containing extracted contract information
    """
    # Extract location information
    location = extract_location(contract_text)
    
    # Determine contract type
    contract_type = determine_contract_type(contract_text)
    
    # Extract key terms and parties
    key_terms = extract_key_terms(contract_text)
    parties = extract_parties(contract_text)
    
    # Extract subject matter
    subject_matter = extract_subject_matter(contract_text, contract_type)
    
    # Extract jurisdiction
    jurisdiction = extract_jurisdiction(contract_text)
    
    return {
        "location": location,
        "contract_type": contract_type,
        "key_terms": key_terms,
        "parties": parties,
        "subject_matter": subject_matter,
        "jurisdiction": jurisdiction
    }

def extract_location(text: str) -> str:
    """Extract location information from contract text."""
    # Look for common location patterns
    location_patterns = [
        r"(?:State of|Province of|in the (?:city|state|province) of)\s+([A-Z][a-zA-Z\s]+)",
        r"(?:located in|situated in|based in)\s+([A-Z][a-zA-Z\s]+)",
        r"([A-Z][a-z]+,\s*[A-Z]{2})",  # City, State format
        r"([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)"  # Country format
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Location not specified"

def determine_contract_type(text: str) -> str:
    """Determine the type of contract based on content."""
    contract_types = {
        "employment": ["employment", "employee", "employer", "job", "salary", "wages", "position"],
        "lease": ["lease", "rent", "tenant", "landlord", "premises", "property"],
        "purchase": ["purchase", "buy", "sell", "sale", "buyer", "seller", "goods"],
        "service": ["service", "services", "provider", "client", "work", "perform"],
        "partnership": ["partnership", "partner", "joint venture", "collaborate"],
        "nda": ["confidential", "non-disclosure", "proprietary", "trade secret"],
        "license": ["license", "licensing", "intellectual property", "copyright", "patent"]
    }
    
    text_lower = text.lower()
    type_scores = {}
    
    for contract_type, keywords in contract_types.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            type_scores[contract_type] = score
    
    if type_scores:
        return max(type_scores, key=type_scores.get)
    
    return "general contract"

def extract_key_terms(text: str) -> List[str]:
    """Extract key terms from contract text."""
    # Look for common contract terms
    term_patterns = [
        r"(?:term|duration|period)(?:\s+of)?\s*:\s*([^.]+)",
        r"(?:payment|fee|amount)(?:\s+of)?\s*:\s*([^.]+)",
        r"(?:effective|start|begin)(?:\s+date)?\s*:\s*([^.]+)",
        r"(?:termination|end|expir)(?:\s+date)?\s*:\s*([^.]+)"
    ]
    
    terms = []
    for pattern in term_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        terms.extend([match.strip() for match in matches])
    
    # Limit to most relevant terms
    return terms[:5] if terms else ["Standard contract terms"]

def extract_parties(text: str) -> List[str]:
    """Extract party names from contract text."""
    # Look for party definitions
    party_patterns = [
        r"(?:between|by and between)\s+([^,]+),?\s+(?:and|&)\s+([^,]+)",
        r"(?:party|parties)(?:\s+named)?\s*:\s*([^.]+)",
        r"(?:contractor|client|company|corporation|individual)(?:\s+named)?\s*:\s*([^.]+)"
    ]
    
    parties = []
    for pattern in party_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                parties.extend([p.strip() for p in match])
            else:
                parties.append(match.strip())
    
    # Clean and limit parties
    cleaned_parties = [p for p in parties if len(p) > 2 and len(p) < 100]
    return cleaned_parties[:3] if cleaned_parties else ["Parties not specified"]

def extract_subject_matter(text: str, contract_type: str) -> str:
    """Extract the main subject matter of the contract."""
    # Create a summary based on contract type and key phrases
    if contract_type == "employment":
        return f"Employment agreement - {contract_type} contract"
    elif contract_type == "lease":
        return f"Property lease agreement - {contract_type} contract"
    elif contract_type == "purchase":
        return f"Purchase/sale agreement - {contract_type} contract"
    else:
        return f"{contract_type.replace('_', ' ').title()} agreement"

def extract_jurisdiction(text: str) -> Optional[str]:
    """Extract jurisdiction information from contract text."""
    jurisdiction_patterns = [
        r"(?:governed by|under the laws of|jurisdiction of)\s+([^.]+)",
        r"(?:courts of|in the courts of)\s+([^.]+)",
        r"(?:laws of the (?:State|Province) of)\s+([^.]+)"
    ]
    
    for pattern in jurisdiction_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

async def search_similar_contracts(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Search for similar contracts based on analysis.
    
    Args:
        analysis: Contract analysis results
        
    Returns:
        List of similar contracts found
    """
    logger.info(f"Searching for similar contracts: type={analysis['contract_type']}, location={analysis['location']}")
    
    # Prepare primary search parameters
    params = prepare_legal_search_params(analysis)
    
    # Execute primary search
    logger.debug("Executing primary SerpAPI search...")
    search_results = await run_search(params)
    
    # Prepare additional targeted search for direct documents
    targeted_params = prepare_targeted_document_search(analysis)
    
    # Execute targeted search
    logger.debug("Executing targeted document search...")
    targeted_results = await run_search(targeted_params)
    
    # Combine and process results
    combined_results = combine_search_results(search_results, targeted_results)
    
    # Check for errors
    if "error" in combined_results:
        logger.error(f"Legal search error: {combined_results['error']}")
        return {"error": combined_results["error"]}
    
    # Process search results
    return format_legal_results(combined_results, analysis)

def prepare_targeted_document_search(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a targeted search specifically for downloadable documents and templates.
    """
    contract_type = analysis.get("contract_type", "contract")
    location = analysis.get("location", "")
    
    # Build a more targeted query
    query_parts = [
        f'"{contract_type} contract template"',
        'filetype:pdf OR filetype:doc',
        'site:lawinsider.com OR site:contractstandards.com OR site:sec.gov OR site:docracy.com'
    ]
    
    if location and location != "Location not specified":
        query_parts.append(f'"{location}"')
    
    query = " ".join(query_parts)
    
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google",
        "q": query,
        "hl": "en",
        "gl": "us",
        "num": 10,
        "filter": "1"
    }
    
    logger.debug(f"Targeted document search query: {query}")
    return params

def combine_search_results(primary_results: Dict[str, Any], targeted_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine results from multiple searches, removing duplicates.
    """
    if "error" in primary_results:
        return primary_results
    if "error" in targeted_results:
        return primary_results
    
    primary_organic = primary_results.get("organic_results", [])
    targeted_organic = targeted_results.get("organic_results", [])
    
    # Combine results and remove duplicates based on URL
    seen_urls = set()
    combined_organic = []
    
    # Add targeted results first (they're more specific)
    for result in targeted_organic:
        url = result.get("link", "")
        if url not in seen_urls:
            seen_urls.add(url)
            combined_organic.append(result)
    
    # Add primary results that aren't duplicates
    for result in primary_organic:
        url = result.get("link", "")
        if url not in seen_urls:
            seen_urls.add(url)
            combined_organic.append(result)
    
    # Return combined results in the same format
    combined_results = primary_results.copy()
    combined_results["organic_results"] = combined_organic
    
    return combined_results

def format_legal_results(search_results: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Format raw search results into standardized legal document format.
    
    Args:
        search_results: Raw search results from SerpAPI
        analysis: Original contract analysis
        
    Returns:
        Formatted list of similar legal documents
    """
    organic_results = search_results.get("organic_results", [])
    logger.debug(f"Search complete. Found {len(organic_results)} organic results")
    
    if not organic_results:
        logger.warning("No legal documents found in search results")
        return []
    
    # Format legal document data
    formatted_docs = []
    
    # Prioritize direct document links
    prioritized_results = prioritize_document_links(organic_results)
    
    for i, result in enumerate(prioritized_results[:12]):  # Increase to 12 results
        logger.debug(f"Processing result {i+1} of {len(prioritized_results)}")
        
        # Extract relevant information
        title = result.get("title", "Untitled Document")
        url = result.get("link", "")
        snippet = result.get("snippet", "No description available")
        
        # Determine relevance based on analysis
        relevance_score = calculate_relevance(result, analysis)
        
        # Determine link type (direct document or webpage)
        link_type = determine_link_type(url, title)
        
        # Extract domain and create source info
        domain = extract_domain(url)
        source_info = get_source_info(domain, link_type)
        
        formatted_docs.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "contract_type": analysis["contract_type"],
            "location": result.get("location", analysis["location"]),
            "relevance_score": relevance_score,
            "source": source_info,
            "link_type": link_type,
            "domain": domain,
            "clickable_description": create_clickable_description(title, link_type, domain)
        })
    
    logger.info(f"Returning {len(formatted_docs)} formatted legal documents")
    return formatted_docs

def prioritize_document_links(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize results that are likely to be direct document links.
    """
    direct_docs = []
    web_pages = []
    
    for result in results:
        url = result.get("link", "").lower()
        title = result.get("title", "").lower()
        
        # Check if it's likely a direct document
        if (is_direct_document_link(url, title)):
            direct_docs.append(result)
        else:
            web_pages.append(result)
    
    # Return direct documents first, then web pages
    return direct_docs + web_pages

def is_direct_document_link(url: str, title: str) -> bool:
    """
    Determine if a URL/title likely points to a direct document.
    """
    url_lower = url.lower()
    title_lower = title.lower()
    
    # Check for direct file extensions
    if any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.txt']):
        return True
    
    # Check for document-indicating keywords in URL
    doc_indicators = [
        'download', 'document', 'file', 'attachment', 'forms',
        'templates', 'samples', 'examples', 'contracts'
    ]
    if any(indicator in url_lower for indicator in doc_indicators):
        return True
    
    # Check for document-indicating keywords in title
    title_indicators = [
        'download', 'pdf', 'template', 'form', 'sample',
        'example', 'document', '[pdf]', '(pdf)', '.pdf'
    ]
    if any(indicator in title_lower for indicator in title_indicators):
        return True
    
    # Check for legal document repositories
    legal_sites = [
        'sec.gov', 'courts.gov', 'lawinsider.com', 'contractstandards.com',
        'findlaw.com', 'justia.com', 'docracy.com', 'lawdepot.com'
    ]
    if any(site in url_lower for site in legal_sites):
        return True
    
    return False

def determine_link_type(url: str, title: str) -> str:
    """
    Determine the type of link (direct document, template, or webpage).
    """
    url_lower = url.lower()
    title_lower = title.lower()
    
    # Direct document files
    if any(ext in url_lower for ext in ['.pdf', '.doc', '.docx']):
        return "Direct Document"
    
    # Template or form pages
    if any(word in url_lower or word in title_lower for word in ['template', 'form', 'sample']):
        return "Template/Form"
    
    # Legal database entries
    if any(site in url_lower for site in ['sec.gov', 'lawinsider.com', 'contractstandards.com']):
        return "Legal Database"
    
    # Court documents
    if 'courts.gov' in url_lower or 'court' in title_lower:
        return "Court Document"
    
    return "Legal Resource"

def get_source_info(domain: str, link_type: str) -> str:
    """
    Get descriptive source information.
    """
    source_descriptions = {
        'sec.gov': 'SEC Filing',
        'courts.gov': 'Court System',
        'lawinsider.com': 'Law Insider Database',
        'contractstandards.com': 'Contract Standards',
        'findlaw.com': 'FindLaw Resource',
        'justia.com': 'Justia Legal Portal',
        'docracy.com': 'Docracy Templates',
        'lawdepot.com': 'LawDepot Forms'
    }
    
    if domain in source_descriptions:
        return f"{source_descriptions[domain]} ({link_type})"
    
    return f"{domain} ({link_type})"

def create_clickable_description(title: str, link_type: str, domain: str) -> str:
    """
    Create a user-friendly description for the clickable link.
    """
    if link_type == "Direct Document":
        return f"📄 Direct Download: {title}"
    elif link_type == "Template/Form":
        return f"📝 Template/Form: {title}"
    elif link_type == "Legal Database":
        return f"🏛️ Legal Database Entry: {title}"
    elif link_type == "Court Document":
        return f"⚖️ Court Document: {title}"
    else:
        return f"🔗 Legal Resource: {title}"

def calculate_relevance(result: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Calculate relevance score for a search result."""
    score = 0
    text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    
    # Check for contract type match
    if analysis["contract_type"] in text:
        score += 3
    
    # Check for location match
    if analysis["location"].lower() in text:
        score += 2
    
    # Check for key terms
    for term in analysis.get("key_terms", []):
        if term.lower() in text:
            score += 1
    
    if score >= 4:
        return "High"
    elif score >= 2:
        return "Medium"
    else:
        return "Low"

def extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return domain.replace("www.", "") if domain else "Unknown"
    except:
        return "Unknown" 