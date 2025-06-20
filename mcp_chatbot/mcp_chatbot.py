import os
from typing import List, TypedDict, Dict 
import asyncio
import nest_asyncio ##necessary for different OSs to work properly with python event loops 
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types 
from mcp.client.stdio import stdio_client
from anthropic import Anthropic
from contextlib import AsyncExitStack
import json

nest_asyncio.apply()

load_dotenv()
# We need to maintain a list of all of the sessions we will be connected to 
# Also a list of all of the tools and the particular session that tool is related to
class MCP_ChatBot:
    #Let's initialize session and client objects
    def __init__(self):
        self.sessions = {}  # dictionary maps tool/prompt names or resource URIs to MCP client sessions
        self.exit_stack = AsyncExitStack()  # to manage multiple context managers inside the async env
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # initialize the client
        self.available_tools = [] 
        self.available_prompts = []  # Prompts list for quick display
    
    async def connect_to_a_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single server"""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            
            try:
                # List available tools
                response = await session.list_tools()
                for tool in response.tools:
                    self.sessions[tool.name] = session
                    self.available_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    })
            
                # List available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append({
                            "name": prompt.name,
                            "description": prompt.description,
                            "arguments": prompt.arguments
                        })
                # List available resources
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        resource_uri = str(resource.uri)
                        self.sessions[resource_uri] = session
            
            except Exception as e:
                print(f"Error {e}")
      
        except Exception as e:
            print(f"Failed to connect to {server_name}: {str(e)}")

    async def connect_to_servers(self): 
        """Connect to all MCP servers configured in the server_config.json file"""
        try:
            with open("../server_config.json", "r") as file:
                data = json.load(file)
                #now let's turn our parsed data into a dictionary 
                servers = data.get("mcpServers", {})
        except Exception as e:
            print(f"Error loading server configuration: {str(e)}")
            return # Exit if the config can't be read
        for server_name, server_config in servers.items():
            for attempt in range(3): #try up to 3 times 
                try:
                    await self.connect_to_a_server(server_name, server_config)
                    break #if successful, move to the next one 
                except Exception as e:
                    print(f"Failed to connect to {server_name} (attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep(1) #wait for 1 second before retrying
            else:
                print(f"Failed to connect to {server_name} after 3 attempts. Skipping...")
        
    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        
        while True:
            response = self.anthropic_client.messages.create(
                max_tokens = 2024,
                model = 'claude-3-7-sonnet-20250219', 
                tools = self.available_tools,
                messages = messages
            )
            
            assistant_content = []
            has_tool_use = False
            
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                elif content.type == 'tool_use':
                    has_tool_use = True
                    assistant_content.append(content)
                    messages.append({'role':'assistant', 'content':assistant_content})
                    
                    # now let's get the session and call the tool needed
                    session = self.sessions.get(content.name)
                    if not session:
                        print(f"Tool '{content.name}' not found.") 
                        break
                        
                    result = await session.call_tool(content.name, arguments=content.input)
                    messages.append({
                        "role": "user", 
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": result.content
                            }
                        ]
                    })
            # Exit loop if no tool was used
            if not has_tool_use:
                break

    async def get_resource(self, resource_uri: str) -> str:
        session = self.sessions.get(resource_uri)
        # if not found, but it's a papers URI, use any available papers session as a fallback
        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break

        if not session:
            print(f"Resource {resource_uri} not found.")
            return
        
        try:
            result = await session.read_resource(uri = resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("Content:")
                print(result.contents[0].text) #for now let's just simply print the content of the resource
            else:
                print("No content available.")
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"

    async def list_prompts(self):
            """List all available prompts."""
            if not self.available_prompts:
               print("No prompts available.")
               return
            print("\nAvailable prompts:")
            for prompt in self.available_prompts:
                print(f"- {prompt['name']}: {prompt['description']}")
                if prompt['arguments']:
                    print(f"Prompt Arguments:")
                    for arg in prompt['arguments']:
                        arg_name = arg.name if hasattr(arg, "name") else arg.get("name", "")
                        print (f"    - {arg_name}")

    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        # first let's check if we have a connection for this prompt
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return
        
        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                prompt_content = result.messages[0].content
                
                # now extract text from content and handle different possible content formats
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, 'text'):
                    text = prompt_content.text
                else:
                    #if it’s a list of items, join them into a single text string
                    text = " ".join(item.text if hasattr(item, 'text') else str(item) 
                                  for item in prompt_content)
                
                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text) #let's feed our chat bot, just like a user query
        except Exception as e:
            print(f"Error when executing prompt: {e}") 

    async def chat_loop(self):
        # let's print a friendly welcome and usage hints for the user 
        print("\nMCP ChatBot Started!")
        print("Type your queries and start your research")
        print("Use @folders to see available topics")
        print("Use @<topic> to search for papers on a specific topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <prompt_name> <arg1=value1> to execute a prompt")
        print("\nType 'exit' to end the chat.")

        # now keep chatting until the user types 'exit'.
        while True: 
            try:
                query = input("\nQuery: ").strip()
                if not query:
                    continue
                if query.lower() == "exit":
                    print("\nThank you for using MCP ChatBot! ^_^ Goodbye and see you soon!")
                    break
                if query.startswith("@"):
                    # remove @ sign
                    topic = query[1:]
                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"
                    await self.get_resource(resource_uri)
                    continue 

                #check for / command syntax
                if query.startswith("/"):
                    parts = query.split()
                    command = parts[0].lower()
                    if command == "/prompts":
                        await self.list_prompts()
                    elif command == "/prompt":
                        if len(parts) < 2:
                            print("Usage: /prompt <prompt_name> <arg1=value1>...")
                            continue

                        prompt_name = parts[1]
                        args = {}

                        #now parse arguments
                        for arg in parts[2:]:
                            if "=" in arg:
                                key, value = arg.split("=", 1)
                                args[key] = value
                        await self.execute_prompt(prompt_name, args)
                    else:
                        print(f"Unknown command: {command}")
                        continue
                else:
                    await self.process_query(query)
                    print("\n")
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("\nPlease try again.")
        

    async def cleanup(self):
        await self.exit_stack.aclose()
        print("\nMCP ChatBot Stopped!")
      

async def main():
    chatbot = MCP_ChatBot() 
    # as we need our sessions to stay open and accessible beyond a single block for our assistant 
    # we cannot use the "with" or "async with" statements 
    # so we need to manually close all resources managed by the exit stack
    try: 
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
         
               


    

    