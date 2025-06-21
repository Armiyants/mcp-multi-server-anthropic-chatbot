# Multi-Server MCP Research Assistant

This chatbot helps you discover and understand research papers from arXiv using natural language and the Model Context Protocol (MCP).

## What it has/does

-  Multi-Server Architecture**: Connects to multiple MCP servers simultaneously
-  Resources**: Access organized paper collections by topic -- > read-only data
-  Prompts**: Pre-built prompt templates so the user doesn't have to do the whole prompt engineering themselves
-  Tools**: Servers' capabilities

## Multi-Server Architecture
### Connected Servers

1. **Research Server** (`mcp_chatbot/research_server.py`)
   - **Tools**: `get_arxiv_papers`, `extract_info`
   - **Resources**: `papers://folders`, `papers://{topic}`
   - **Prompts**: `generate_search_prompt`
   - **Purpose**: arXiv paper search and analysis

2. **Fetch Server** (`mcp-server-fetch`)
   - **Purpose**: Web content retrieval and processing (see "Example Queries" section to play around)

3. **Filesystem Server** (`@modelcontextprotocol/server-filesystem`)
   - **Purpose**: File system operations and management

### Server Configuration

The system uses `server_config.json` to manage multiple server connections.
Feel free to add your preffered ones too. :))

## Start

1. **(Recommended) Create and activate a virtual environment**

   This keeps dependencies isolated and avoids conflicts.
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key** (create a `.env` file):
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Start the chatbot**:
   ```bash
   uv run mcp_chatbot.py
   ```
   
### Example Queries: 
** - Fetch the content of this website: https://modelcontextprotocol.io/docs/concepts/architecture and save the content in the file "mcp_summary.md"
- Create a visual diagram that summarizes the content of "mcp_summary.md"

### Example Workflow:

1. **Search for papers**: *"Find papers about neural networks"*
2. **Browse topics**: `@folders` to see available topics
3. **Explore specific topic**: `@neural_networks_brain_functions`
4. **Get comprehensive analysis**: `/prompt generate_search_prompt topic=neural_networks num_papers=10`

## Contributing

Feel free to submit issues and enhancement requests! ☺️
