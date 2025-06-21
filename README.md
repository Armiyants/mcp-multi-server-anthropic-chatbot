# ArXiv Paper Search and MCP Chatbot 💬🤖

A Python-based chatbot that uses the Anthropic Claude API for natural language processing to help users search and interact with arXiv papers. The project combines direct arXiv integration with MCP (Model Context Protocol) capabilities for enhanced functionality.

## Features

### Paper Search and Management
- **Paper Search**: Natural language queries to find papers (e.g., "quantum computing" or "human brain")
- **Paper Details**: Get detailed information about specific papers using their IDs
- **Topic Navigation**: Browse papers by topic using `@folders` and `@<topic>` commands

### arXiv SDK Integration    
The project uses the official arXiv Python SDK (`arxiv` package) to interact with arXiv's API:
- **Search Functionality**: Uses `arxiv.Search` for paper queries
- **Result Processing**: Handles paper metadata
- **Client Management**: Uses `arxiv.Client` for API requests

### MCP Integration (Experimental)
- Resource-based paper access
- Prompt management system
- Command interface:
  - `/prompts` - List available prompts
  - `/prompt <name>` - Execute specific prompts

## Project Structure
```
mcp_project_anthropic_arxiv_chatbot/
├── mcp_chatbot/
│   ├── __init__.py
│   ├── chatbot.py
│   └── research_server.py
├── variables.py
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.x
- Anthropic API key (Claude API access)
- Internet connection
- arXiv API access (no key required)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp_project_anthropic_arxiv_chatbot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

1. Run the chatbot:
```bash
python -m mcp_chatbot.chatbot
```

2. Available commands:
   - Natural language queries: "Search for papers about quantum computing"
   - Paper ID lookup: "Get information about paper [ID]"
   - Topic browsing: `@folders`, `@<topic>`
   - Prompt system: `/prompts`, `/prompt <name>`
   - Exit: Type 'exit' to quit

3. Example queries:
   ```
   "Search for papers about quantum computing"
   "Get information about paper 2103.12345"
   @folders
   @quantum_computing
   /prompts
   ```

## Error Handling

The chatbot includes error handling for:
- API connection issues
- Invalid paper IDs
- Search query errors
- Resource access failures

## Contributing

Feel free to submit issues and enhancement requests! ☺️

## License

[Your chosen license]