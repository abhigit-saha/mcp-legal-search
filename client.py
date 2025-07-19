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
            
            prompt = f"Analyze this legal contract and find similar documents:\n\n{contract_text}"
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
                    except (json.JSONDecodeError, TypeError):
                        result_data = result_text
                else:
                    result_data = "No result returned"
                
                # Send the function result back to Gemini for final response
                conversation = [
                    types.Content(role="user", parts=[types.Part(text=prompt)]),
                    response.candidates[0].content,  # Gemini's response with function call
                    types.Content(
                        role="function", 
                        parts=[types.Part(
                            function_response=types.FunctionResponse(
                                name=function_call.name,
                                response=result_data
                            )
                        )]
                    )
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