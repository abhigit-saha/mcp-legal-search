"""
Pydantic schemas for legal contract information.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict

class ContractAnalysis(BaseModel):
    """Contract analysis result model."""
    location: str
    contract_type: str
    key_terms: List[str]
    parties: List[str]
    subject_matter: str
    jurisdiction: Optional[str] = None

class SimilarContract(BaseModel):
    """Similar contract information model."""
    title: str
    url: str
    snippet: str
    contract_type: str
    location: Optional[str] = None
    relevance_score: Optional[str] = None
    source: str
    link_type: Optional[str] = None
    domain: Optional[str] = None
    clickable_description: Optional[str] = None 