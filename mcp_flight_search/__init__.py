"""
MCP Flight Search package.

A flight search service implementing Anthropic's Model Context Protocol (MCP).
This package provides MCP-compliant tools that allow AI models to search
for flight information using structured tool calls.
"""

__version__ = "0.2.0"

from mcp_flight_search.models.schemas import ContractAnalysis, SimilarContract