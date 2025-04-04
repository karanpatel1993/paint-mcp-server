# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import subprocess
import Quartz
from AppKit import NSWorkspace, NSScreen
import asyncio


# instantiate an MCP server client
mcp = FastMCP("Paint AI Agent")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

@mcp.tool()
async def open_keynote() -> dict:
    """Open Apple Keynote with a single blank slide"""
    try:
        # Use a very simple AppleScript approach to avoid syntax errors
        simple_script = """
        tell application "Keynote"
            activate
            make new document
        end tell
        """
        subprocess.run(["osascript", "-e", simple_script])
        
        # Wait for Keynote to fully initialize
        await asyncio.sleep(1)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Keynote opened with a new document"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error opening Keynote: {str(e)}"
                }
            ]
        }

@mcp.tool()
async def add_rectangle_to_keynote(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Add a rectangle to the current Keynote slide using direct object creation"""
    try:
        # Calculate width and height from coordinates
        width = x2 - x1
        height = y2 - y1
        
        # Make the rectangle bigger (1.5x larger) while keeping the same center
        center_x = x1 + width/2
        center_y = y1 + height/2
        larger_width = width * 1.5
        larger_height = height * 1.5
        
        # First, make sure Keynote is active
        activate_script = """
        tell application "Keynote"
            activate
            delay 0.5
        end tell
        """
        subprocess.run(["osascript", "-e", activate_script])
        await asyncio.sleep(0.5)  # Allow time for Keynote to activate
        
        # Use direct object creation which is more reliable
        # We'll simplify the script to avoid color setting which is causing syntax errors
        create_shape_script = f"""
        tell application "Keynote"
            tell front document
                tell current slide
                    -- Create a new rectangle shape directly with basic properties
                    make new shape with properties {{width:{larger_width}, height:{larger_height}, position:{{{center_x}, {center_y}}}}}
                end tell
            end tell
        end tell
        """
        
        # Create the rectangle directly
        subprocess.run(["osascript", "-e", create_shape_script])
        await asyncio.sleep(0.5)  # Give time for the rectangle to be created
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Larger rectangle added to Keynote centered at ({center_x},{center_y}) with width {larger_width} and height {larger_height}"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error adding rectangle to Keynote: {str(e)}"
                }
            ]
        }

@mcp.tool()
async def add_text_to_keynote(text: str) -> dict:
    """Add text to the last created shape in the current Keynote slide"""
    try:
        # First, make sure Keynote is active
        activate_script = """
        tell application "Keynote"
            activate
            delay 0.5
        end tell
        """
        subprocess.run(["osascript", "-e", activate_script])
        await asyncio.sleep(0.5)  # Allow time for Keynote to activate
        
        # Use a simplified AppleScript that only sets the text content
        # without trying to modify any text properties
        add_text_script = f"""
        tell application "Keynote"
            tell front document
                tell current slide
                    -- Get the most recently added shape (last item in the shapes list)
                    set lastShape to last item of shapes
                    
                    -- Add text to the shape (only set the text, no formatting)
                    set object text of lastShape to "{text}"
                end tell
            end tell
        end tell
        """
        
        # Run the script to add text to the shape
        subprocess.run(["osascript", "-e", add_text_script])
        await asyncio.sleep(0.5)  # Give time for the text to be added
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Text '{text}' added to the most recent shape in Keynote"
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error adding text to Keynote shape: {str(e)}"
                }
            ]
        }

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
