from mcp import ClientSession, StdioServerParameters, types 
from mcp.client.stdio import stdio_client
import asyncio

# Let's create server parameters for stdio connection 
# specifying the command details to let our client know how to start the server 
server_params = StdioServerParameters(
    command="python3", #executable 
    args=["mcp_server.py"], #optional command line arguments 
    env=None, #optional environment variables 
)

#let's now start actually establishing that connection and launch the server as a subprocess 
#and as we do not want this to be blocking, we're gonna make it async 

async def run():
    #We're gonna set up a context manager to handle the server process.
    #Once we have established the server, we will have access to the read and write streams.
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Now let's establish the handshake and initialize the session (1:1 connection with the server)
            await session.initialize()

            #List available tools
            tools = await session.list_tools()
            print(f"Available tools: {tools}")

            #Client's job is to query for tools, take those tools and pass them to a LLM
            #We will cal our chatbot loop here 
            #....

            #Call a tool, this will be in the chatbot loop 




if __name__ == "__main__":
    asyncio.run(run())

            

           

