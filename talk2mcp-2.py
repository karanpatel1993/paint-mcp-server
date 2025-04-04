import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# These will be set by user input
max_iterations = 5
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting AI Agent with Keynote integration...")
    print("This agent can solve mathematical problems and visualize results in Keynote.")
    print("It can perform calculations, manipulate text, and display results visually.")
    print("The agent can open applications, create visual elements, and add text to visualize results.")
    
    print("\nExample queries you can try:")
    print("1. Find the ASCII values of characters in HELLO and then return sum of exponentials of those values.")
    print("2. Calculate the fibonacci sequence for n=10 and create a visual presentation of the result.")
    print("3. Calculate 24 factorial and display the answer visually.")
    print("4. What is the sine of 45 degrees? Create a visual presentation of this result.")
    print("5. Find the remainder when 2^10 is divided by 7 and show it in a presentation.")
    print("6. Calculate the factorial of 10 and display it in a small centered visual element.")
    print("\nNote: For visualization queries, the agent will approach the task step by step:")
    print("- First performing calculations")
    print("- Then opening an appropriate application")
    print("- Creating a visual container for the result")
    print("- Adding informative text")
    print("For visualization queries, you need several iterations to complete all steps.")
    print("You can include presentation preferences in your query (e.g., 'small', 'centered', 'detailed').")
    
    # Get max iterations from user
    global max_iterations
    print("\nEnter maximum number of iterations (default: 5):")
    user_max_iter = input().strip()
    if user_max_iter.isdigit() and int(user_max_iter) > 0:
        max_iterations = int(user_max_iter)
    print(f"Maximum iterations set to: {max_iterations}")
    
    try:
        # Create a single MCP server connection
        print("\nConnecting to MCP server...")
        server_params = StdioServerParameters(
            command="python3",
            args=["example2.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a versatile agent solving problems and visualizing results. You have access to various mathematical tools and visualization capabilities in Apple Keynote.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [number]

Important:
- When a function returns multiple values, you need to process all of them
- Only give FINAL_ANSWER when you have completed all necessary calculations
- When visualizing results, consider a general approach:
  1. First open the appropriate application to host your visualization
  2. Find or create a suitable area to display the content (like a shape or container)
  3. Add the relevant information as text so the user can see the results
- When adding visual elements, try to make them:
  * Appropriately sized (not too large or small)
  * Well-positioned (centered or aligned properly)
  * Clear and readable (with descriptive text)
- Your available tools include functions to work with Apple Keynote
- When adding text, make sure it includes both the answer and any relevant explanation
- Do not repeat function calls with the same parameters

Examples:
- FUNCTION_CALL: add|5|3
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FUNCTION_CALL: open_keynote
- FUNCTION_CALL: add_rectangle_to_keynote|350|250|650|450
- FUNCTION_CALL: add_text_to_keynote|The factorial of 5 is 120
- FINAL_ANSWER: [42]

Query Analysis:
- If the query mentions visualization or presentation, consider how to visually represent the result
- If the query is only about calculations without mentioning visualization, use FINAL_ANSWER
- Always perform the necessary calculations first before attempting any visualization
- Listen for cues about presentation preferences:
  * Size preferences like "small" or "large"
  * Position preferences like "centered" or "at the top"
  * Style preferences like "simple" or "detailed"

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                # Get user query
                print("\nEnter your query (or use default if empty):")
                user_query = input().strip()
                query = user_query if user_query else "Find the ASCII values of characters in INDIA and then return sum of exponentials of those values and create a visual presentation of the result"
                print(f"\nProcessing query: {query}")
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            # Provide more context when Keynote functions are called
                            if func_name == "open_keynote":
                                print("\n=== Starting Visualization Process ===")
                                print("Opening presentation application...")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I opened a presentation application to prepare for visualization. "
                                    f"The function returned: {result_str}. "
                                    f"Next, I'll create an appropriate visual element to display the result."
                                )
                            elif func_name == "add_rectangle_to_keynote":
                                # Calculate rectangle size and position
                                x1 = arguments.get('x1', 0)
                                y1 = arguments.get('y1', 0)
                                x2 = arguments.get('x2', 0)
                                y2 = arguments.get('y2', 0)
                                width = x2 - x1
                                height = y2 - y1
                                center_x = x1 + width/2
                                center_y = y1 + height/2
                                
                                print("Creating visual container for the result...")
                                print(f"   Size: {width}x{height} pixels")
                                print(f"   Position: centered at ({center_x}, {center_y})")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I created a visual container with dimensions {width}x{height} "
                                    f"at position ({center_x}, {center_y}). "
                                    f"The function returned: {result_str}. "
                                    f"Now I'll add the result text to this container."
                                )
                            elif func_name == "add_text_to_keynote":
                                print("Adding result text to the visual container...")
                                print(f"   Text: '{arguments.get('text', '')}'")
                                print("\n=== Visualization Complete ===")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I added the text '{arguments.get('text', 'unknown')}' to the visual container. "
                                    f"The function returned: {result_str}. "
                                    f"The visualization is now complete and displays the result."
                                )
                            else:
                                # Default response for other function calls
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I called {func_name} with {arguments} parameters, "
                                    f"and the function returned {result_str}."
                                )
                            
                            last_response = iteration_result

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                        # Extract the final answer
                        _, answer = response_text.split(":", 1)
                        print(f"Final Answer: {answer}")
                        print("\nTo visualize this result, try a new query like:")
                        print(f"'Create a visual presentation of {answer.strip()}'")
                        print(f"'Display {answer.strip()} visually'")
                        print(f"'Show this result in a presentation'")
                        break
                    
                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
