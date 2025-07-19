import asyncio
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv()
from mcp.client.stdio import stdio_client


client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))

server_params = StdioServerParameters(
    command = "mcp-flight-search", 
    args = ["--connection_type", "stdio"], 
    env = {"SERP_API_KEY": os.getenv("SERP_API_KEY")}
)

async def run():
    # Remove debug prints
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Sample legal contract text for testing
            contract_text = """
            EMPLOYMENT AGREEMENT
            
            This Employment Agreement ("Agreement") is entered into on January 15, 2024, 
            between TechCorp Inc., a corporation organized and existing under the laws of 
            the State of California ("Company"), and John Smith, an individual residing in 
            San Francisco, California ("Employee").
            
            1. POSITION AND DUTIES
            Employee shall serve as Senior Software Engineer and shall perform such duties 
            as are customarily associated with such position.
            
            2. COMPENSATION
            Company shall pay Employee a base salary of $120,000 per year, payable in 
            accordance with Company's standard payroll practices.
            
            3. TERM
            This Agreement shall commence on February 1, 2024, and shall continue until 
            terminated in accordance with the provisions hereof.
            
            4. GOVERNING LAW
            This Agreement shall be governed by and construed in accordance with the laws 
            of the State of California.
            """
            
            prompt = f"""Analyze this legal contract and find similar documents. 

When you receive the search results, please include specific clickable links in your response. Format each link as:
- Title with clickable description
- Direct URL
- Relevance score

Contract to analyze:
{contract_text}

Please provide a comprehensive analysis and include all found links with their specific URLs so users can click directly to access the documents."""
            await session.initialize()
            # Remove debug prints

            mcp_tools = await session.list_tools()

            print("Available tools:")
            for tool in mcp_tools.tools:
                print(f" - {tool.name}: {tool.description}")
            tools = [
                types.Tool(
                    function_declarations=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                k: v
                                for k, v in tool.inputSchema.items()
                                if k not in ["additionalProperties", "$schema"]
                            },
                        }
                    ]
                )
                for tool in mcp_tools.tools
            ]
            # Remove debug prints

            # Initial request to Gemini
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    tools=tools,
                ),
            )

            print("Initial Response:")
            for part in response.candidates[0].content.parts:
                print(f" - {part}")

            # Check if there are function calls to execute
            function_call = None
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break

            if function_call:
                print(f"\nExecuting function: {function_call.name}")
                print(f"Arguments: {function_call.args}")
                
                # Execute the function call using MCP session
                result = await session.call_tool(
                    function_call.name,
                    function_call.args
                )
                
                print(f"Function result: {result.content}")
                
                # Parse the result properly
                if result.content and len(result.content) > 0:
                    result_text = result.content[0].text
                    # Try to parse JSON if it's a JSON string, otherwise use as text
                    try:
                        import json
                        result_data = json.loads(result_text)
                        
                        # Extract and display clickable links if available
                        if isinstance(result_data, dict) and "similar_contracts" in result_data:
                            print("\n=== CLICKABLE LINKS FOUND ===")
                            for i, contract in enumerate(result_data["similar_contracts"][:10], 1):
                                if isinstance(contract, dict):
                                    title = contract.get("title", "Untitled")
                                    url = contract.get("url", "")
                                    clickable_desc = contract.get("clickable_description", "")
                                    relevance = contract.get("relevance_score", "Unknown")
                                    
                                    print(f"\n{i}. {clickable_desc}")
                                    print(f"   Title: {title}")
                                    print(f"   URL: {url}")
                                    print(f"   Relevance: {relevance}")
                            print("=== END CLICKABLE LINKS ===\n")
                        
                    except (json.JSONDecodeError, TypeError):
                        result_data = result_text
                else:
                    result_data = "No result returned"
                
                # Send the function result back to Gemini for final response
                # Prepare the response data as a dictionary for FunctionResponse
                if isinstance(result_data, dict) and "similar_contracts" in result_data:
                    # Create an enhanced response with formatted links
                    enhanced_response = {
                        "analysis": "Contract analysis completed successfully",
                        "similar_contracts": result_data.get("similar_contracts", []),
                        "clickable_links": []
                    }
                    
                    # Format the clickable links for Gemini
                    for i, contract in enumerate(result_data["similar_contracts"][:10], 1):
                        if isinstance(contract, dict):
                            title = contract.get("title", "Untitled")
                            url = contract.get("url", "")
                            clickable_desc = contract.get("clickable_description", "")
                            relevance = contract.get("relevance_score", "Unknown")
                            
                            enhanced_response["clickable_links"].append({
                                "number": i,
                                "title": title,
                                "url": url,
                                "clickable_description": clickable_desc,
                                "relevance_score": relevance
                            })
                else:
                    # If not the expected format, convert to dict
                    enhanced_response = {
                        "analysis": "Search completed",
                        "result": result_data if isinstance(result_data, str) else str(result_data)
                    }
                
                conversation = [
                    types.Content(role="user", parts=[types.Part(text=prompt)]),
                    response.candidates[0].content,  # Gemini's response with function call
                    types.Content(
                        role="function", 
                        parts=[types.Part(
                            function_response=types.FunctionResponse(
                                name=function_call.name,
                                response=enhanced_response
                            )
                        )]
                    ),
                    types.Content(role="user", parts=[types.Part(text="Please provide your analysis and make sure to include all the specific clickable links with their URLs from the search results. Format each link clearly with the title, URL, and relevance score. For each link, include: 1) The clickable description, 2) The full URL, 3) The relevance score.")])
                ]
                
                # Get final response from Gemini
                final_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=conversation,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        tools=tools,
                    ),
                )
                
                print("\nFinal Response:")
                for part in final_response.candidates[0].content.parts:
                    if part.text:
                        print(part.text)
            else:
                print("No function calls generated.")

if __name__ == "__main__":
    # prompt = f"Find Flights from Atlanta to Las Vegas 2025-05-05"

    # await session.initialize()
    import asyncio
    asyncio.run(run())