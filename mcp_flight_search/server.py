"""
Model Context Protocol (MCP) Flight Search Server implementation.

This module sets up an MCP-compliant server and registers flight search tools
that follow Anthropic's Model Context Protocol specification. These tools can be
accessed by Claude and other MCP-compatible AI models.
"""
from mcp.server.fastmcp import FastMCP
import argparse
from mcp_flight_search.utils.logging import logger
from mcp_flight_search.services.search_service import analyze_and_search_contracts
from mcp_flight_search.config import DEFAULT_PORT, DEFAULT_CONNECTION_TYPE

def create_mcp_server(port=DEFAULT_PORT):
    """
    Create and configure the Model Context Protocol server.
    
    Args:
        port: Port number to run the server on
        
    Returns:
        Configured MCP server instance
    """
    mcp = FastMCP("FlightSearchService", port=port)
    
    # Register MCP-compliant tools
    register_tools(mcp)
    
    return mcp

def register_tools(mcp):
    """
    Register all tools with the MCP server following the Model Context Protocol specification.
    
    Each tool is decorated with @mcp.tool() to make it available via the MCP interface.
    
    Args:
        mcp: The MCP server instance
    """
    @mcp.tool()
    async def analyze_legal_contract_tool(contract_text: str):
        """
        Analyze a legal contract and search for similar documents.
        
        This MCP tool allows AI models to analyze legal contract text and find similar
        contracts based on location, type, and content analysis.
        
        Args:
            contract_text: The full text of the legal contract to analyze
            
        Returns:
            A dictionary containing contract analysis and list of similar documents
        """
        return await analyze_and_search_contracts(contract_text)

    @mcp.tool()
    def server_status():
        """
        Check if the Model Context Protocol server is running.
        
        This MCP tool provides a simple way to verify the server is operational.
        
        Returns:
            A status message indicating the server is online
        """
        return {"status": "online", "message": "MCP Legal Search server is running"}
    
    logger.debug("Model Context Protocol tools registered")

def main():
    """
    Main entry point for the Model Context Protocol Flight Search Server.
    """
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Model Context Protocol Flight Search Service")
    parser.add_argument("--connection_type", type=str, default=DEFAULT_CONNECTION_TYPE, 
                        choices=["http", "stdio"], help="Connection type (http or stdio)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, 
                        help=f"Port to run the server on (default: {DEFAULT_PORT})")
    args = parser.parse_args()
    
    # Initialize MCP server
    mcp = create_mcp_server(port=args.port)
    
    # Determine server type
    server_type = "sse" if args.connection_type == "http" else "stdio"
    
    # Start the server
    logger.info(f"🚀 Starting Model Context Protocol Flight Search Service on port {args.port} with {args.connection_type} connection")
    mcp.run(server_type)

if __name__ == "__main__":
    main() 