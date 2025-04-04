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
    print("Starting AI Agent...")
    print("This agent can solve mathematical problems and create visual presentations.")
    print("It analyzes and selects from available tools to accomplish each task.")
    print("For visualization, it will identify appropriate tools for each step of the process.")
    
    print("\nExample queries you can try:")
    print("1. Find the ASCII values of characters in HELLO and then return sum of exponentials of those values.")
    print("2. Calculate the fibonacci sequence for n=10 and create a visualization of the result.")
    print("3. Calculate 24 factorial and find a way to display the answer visually.")
    print("4. What is the sine of 45 degrees? Create a visual presentation.")
    print("5. Find the remainder when 2^10 is divided by 7 and create a nice visualization.")
    print("6. Calculate the factorial of 10 and display it visually in a small centered element.")
    print("\nHow the agent works:")
    print("1. It analyzes your query to understand what you're asking")
    print("2. It examines all available tools to identify the most appropriate ones")
    print("3. For each step, it selects and executes a specific tool")
    print("4. For visualization tasks, it will:")
    print("   - Select tools for mathematical calculations first")
    print("   - Identify and select a tool to open a presentation application")
    print("   - Find appropriate tools to create visual elements")
    print("   - Select tools to add content to the visualization")
    print("You may need several iterations (5+) to complete all the steps.")
    print("You can include preferences in your query (e.g., 'small', 'centered', 'detailed').")
    
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
                            
                            # Enhance descriptions for visualization-related tools
                            if name == "open_keynote":
                                desc = "Opens a presentation software with a blank slide, perfect for starting a visual presentation"
                            elif name == "add_rectangle_to_keynote":
                                desc = "Creates a visual container (rectangle) on the current presentation slide at specified coordinates (x1,y1,x2,y2) - useful for framing content"
                            elif name == "add_text_to_keynote":
                                desc = "Adds text to the most recently created shape in the presentation - ideal for displaying results with explanations"
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_desc = ""
                                    
                                    # Add parameter descriptions for visualization tools
                                    if name == "add_rectangle_to_keynote":
                                        if param_name in ["x1", "y1"]:
                                            param_desc = " (top-left corner)"
                                        elif param_name in ["x2", "y2"]:
                                            param_desc = " (bottom-right corner)"
                                    elif name == "add_text_to_keynote" and param_name == "text":
                                        param_desc = " (content to display)"
                                        
                                    param_details.append(f"{param_name}: {param_type}{param_desc}")
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
                
                system_prompt = f"""You are a versatile agent solving problems and creating visualizations. You have access to various mathematical tools and visualization applications through available functions.

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
- When visualizing results, explore the available tools to find those that can:
  * Open presentation applications
  * Create visual elements
  * Add text or other content
- Choose the best tools for the task based on their descriptions
- Remember that good visualizations typically involve:
  * A suitable application to host the content
  * Visual elements of appropriate size and position
  * Clear text that explains the result
- Do not repeat function calls with the same parameters

Examples:
- FUNCTION_CALL: add|5|3
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FINAL_ANSWER: [42]

Query Analysis:
- Carefully examine all available tools to understand their capabilities
- If the query mentions visualization or presentation, look for tools that can help with creating visuals
- If the query is only about calculations without mentioning visualization, use FINAL_ANSWER
- Always perform the necessary calculations first before attempting any visualization
- Pay attention to specific requirements in the query like size, position, or style preferences

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                # Get user query
                print("\nEnter your query (or use default if empty):")
                user_query = input().strip()
                query = user_query if user_query else "Find the ASCII values of characters in INDIA and then return sum of exponentials of those values and create a visual presentation of the result"
                print(f"\nProcessing query: {query}")
                print("Starting the agent's decision-making process...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                        print("Agent is deciding which tool to use for the initial task...")
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"
                        print("Agent is deciding which tool to select next based on previous results...")

                    # Get model's response with timeout
                    print("Preparing to generate decision...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"Agent's decision: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get agent's decision: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Tool chosen by agent: {func_name}")
                        print(f"DEBUG: Parameters for execution: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools that could have been chosen: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Preparing to execute tool: {tool.name}")
                            print(f"DEBUG: Tool schema for parameter validation: {tool.inputSchema}")

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
                            print(f"DEBUG: Executing tool now: {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Execution completed, processing result...")
                            
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
                            
                            # Provide more context when visualization functions are called
                            if func_name == "open_keynote":
                                print(f"\n=== In Iteration {iteration + 1} ===")
                                print(f"Agent selected and executed: {func_name}")
                                print("Result: Presentation application opened")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I analyzed the available tools and selected '{func_name}' to begin visualization. "
                                    f"After executing this tool, the result was: {result_str}. "
                                    f"I'll now examine the remaining tools to find one suitable for creating a visual element."
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
                                
                                print(f"\n=== In Iteration {iteration + 1} ===")
                                print(f"Agent selected and executed: {func_name}")
                                print("Result: Visual container created")
                                print(f"   Size: {width}x{height} pixels")
                                print(f"   Position: centered at ({center_x}, {center_y})")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, after reviewing the available tools, I selected '{func_name}' to create a visual container. "
                                    f"I configured a shape with dimensions {width}x{height} at position ({center_x}, {center_y}). "
                                    f"After execution, the result was: {result_str}. "
                                    f"Next, I'll review the available tools to find one that can add textual content."
                                )
                            elif func_name == "add_text_to_keynote":
                                print(f"\n=== In Iteration {iteration + 1} ===")
                                print(f"Agent selected and executed: {func_name}")
                                print("Result: Text added to the visual element")
                                print(f"   Text: '{arguments.get('text', '')}'")
                                print("\n=== Visualization Process Complete ===")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I analyzed the remaining tools and selected '{func_name}' to add content. "
                                    f"I applied the text '{arguments.get('text', 'unknown')}' to display the result. "
                                    f"After execution, the result was: {result_str}. "
                                    f"With this step complete, the visualization now contains all the necessary information."
                                )
                            else:
                                # Default response for other function calls
                                print(f"\n=== In Iteration {iteration + 1} ===")
                                print(f"Agent selected and executed: {func_name}")
                                print(f"Parameters used: {arguments}")
                                print(f"Result: Operation completed")
                                
                                iteration_response.append(
                                    f"In iteration {iteration + 1}, I selected the '{func_name}' tool with parameters {arguments}. "
                                    f"After execution, the result was: {result_str}."
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
                        print(f"\n=== In Iteration {iteration + 1} ===")
                        print("Agent decided to provide a final answer")
                        # Extract the final answer
                        _, answer = response_text.split(":", 1)
                        print(f"Result: {answer}")
                        print("\nTo visualize this result, you could start a new query such as:")
                        print(f"'Create a visualization for {answer.strip()}'")
                        print(f"'Display {answer.strip()} visually using available tools'")
                        print(f"'Visualize {answer.strip()} in a presentation'")
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
    
    
