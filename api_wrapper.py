"""
REST API wrapper for MCP Legal Search functionality.
Deploy this as a separate microservice and call from your main app.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import your MCP components
from mcp_flight_search.services.search_service import analyze_and_search_contracts

load_dotenv()

app = FastAPI(title="Legal Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class ContractAnalysisRequest(BaseModel):
    contract_text: str

class ContractAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    similar_contracts: List[Dict[str, Any]]

@app.post("/api/legal/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(request: ContractAnalysisRequest):
    """
    Analyze a legal contract and find similar documents.
    """
    try:
        # Validate input
        if not request.contract_text or len(request.contract_text.strip()) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Contract text must be at least 50 characters long"
            )
        
        # Perform analysis
        result = await analyze_and_search_contracts(request.contract_text)
        
        return ContractAnalysisResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/legal/health")
async def health_check():
    return {"status": "healthy", "service": "legal-search-api"}

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Legal Search API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/legal/analyze",
            "health": "/api/legal/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
