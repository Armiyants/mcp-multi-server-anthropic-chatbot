#define the schema for each tool that we will provide to the LLM
from get_paper import get_arxiv_papers
from extract_info import extract_info
import json

tools = [
    {
        "name": "get_arxiv_papers",
        "description": "Get papers from arXiv based on a topic and store their information in a directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to search for"},
                "max_results": {"type": "integer", "description": "The maximum number of results to return", "default": 5}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "extract_info",
        "description": "Search for information about a specific paper across all topic directories based on the paper's ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "The ID of the paper to extract information from"}
            },
            "required": ["paper_id"]
        }
    }
]   

# LLM itself is not going to call this tools. We need to write the code to call those functions and pass the data back to the model
# Tool mapping and execution
map_tool_name_to_function = {
    "get_arxiv_papers": get_arxiv_papers,
    "extract_info": extract_info
}

def call_tool(tool_name: str, arguments: dict):
    """
    Call a tool function based on the tool name and pass the arguments to the function.
    Return the result in a variety of data types that come in.
    """
    if tool_name not in map_tool_name_to_function:
        raise ValueError(f"Tool {tool_name} not found")
    
    result = map_tool_name_to_function[tool_name](arguments)
    if result is None:
        result = "No result found"
    elif isinstance(result, list):
        result = ', '.join(result) #convert the list to a string
    elif isinstance(result, dict):
        result = json.dumps(result, indent=2) #convert the dictionary to a JSON string
    else:
        result = str(result) #for any other data type, convert it to a string
        return result
