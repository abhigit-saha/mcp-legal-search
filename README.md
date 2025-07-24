# MCP LEGAL Search
# A legal search system that is built on top of the existing MCP flight search, and searches for the most similar contracts fitting the context based on Location, Keywords, Topics etc. 

## What is Model Context Protocol?

The Model Context Protocol (MCP) is a standard developed by Anthropic that enables AI models to use tools by defining a structured format for tool descriptions, calls, and responses. This project implements MCP tools that can be used by Claude and other MCP-compatible models.


Start the MCP server:

```bash
# Using the command-line entry point
mcp-flight-search --connection_type http

# Or run directly
python main.py --connection_type http
```

You can also specify a custom port:
```bash
python main.py --connection_type http --port 5000
```

## Environment Variables

Set the SerpAPI key as an environment variable:
```bash
export SERP_API_KEY="your-api-key-here"
```

