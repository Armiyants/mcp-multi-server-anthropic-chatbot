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

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCP_ChatBot:
    #Let's initialize session and client objects
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack() #to manage multiple context managers inside the async env
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) #initialize the client
        self.available_tools: List[ToolDefinition] =[] 
        self.tool_to_session: Dict[str, ClientSession] = {}
    
    async def connect_to_a_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single server"""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions.append(session)

            #now let's list the available tools 
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with available tools: ", [tool.name for tool in tools])

            #append the tools to the list and associate them with the session
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                )

        except Exception as e:
            print(f"Failed to connect to {server_name}: {str(e)}")

    async def connect_to_servers(self): 
        """Connect to all MCP servers configured in the server_config.json file"""
        try:
            with open("server_config.json", "r") as file:
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
        messages = [
            {
                "role": "user",
                "content": query
            } 
        ]
        #now let's get access to our model 
        response = self.anthropic_client.messages.create(
                    max_tokens = 2024,
                    model = 'claude-3-7-sonnet-20250219',
                    tools = self.available_tools,
                    messages = messages
                )
        #passing in information coming from the query and
        #if there is a tool that we need to use, we will go ahead, find it and call it using respective session 
        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == "text":
                    print(content.text)
                    assistant_content.append(content)
                    if(len(response.content) == 1):
                        process_query= False
                elif content.type == "tool_use":
                    assistant_content.append(content)
                    messages.append({"role": "assistant", "content": assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name 
                    if "start_index" in tool_args:
                        print(f"Fetching next chunk starting at index {tool_args['start_index']}")

                    print(f"Calling tool {tool_name} with arguments {tool_args}")

                    session = self.tool_to_session[tool_name] #getting the correct session 
                    result = await session.call_tool(tool_name, arguments=tool_args)

                    messages.append({
                        "role": "user",
                        "content": [
                            {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result.content }
                        ]
                    })
                    response = self.anthropic_client.messages.create(
                        max_tokens=2024,
                        model="claude-3-7-sonnet-20250219",
                        tools=self.available_tools,
                        messages=messages
                    )

                    if(len(response.content) == 1 and response.content[0].type == "text"):
                        print(response.content[0].text)
                        process_query = False
                    else: 
                        continue
    
    async def chat_loop(self):
        print("\nMCP ChatBot Started!")
        print("Type your queries and start your research")
        print("\nType 'exit' to end the chat.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "exit":
                    print("\nThank you for using MCP ChatBot! ^_^ Goodbye and see you soon!")
                    break
                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")
                print("\nPlease try again.")

    async def cleanup(self):
        """Cleaning resources using our context manager AsyncExitStack"""
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
         
               


    

    