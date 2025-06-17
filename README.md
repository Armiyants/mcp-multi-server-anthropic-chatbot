# ArXiv Paper Search Chatbot 💬🤖

A Python-based chatbot that uses the Anthropic Claude API for natural language processing and helps users search and retrieve information from arXiv papers. 

# What I Built 

I created two main tools:
1. **Paper Search**: Just tell it what you're interested in (like "quantum computing" or "human brain"), and it'll find relevant papers
2. **Paper Details**: Ask about a specific paper using its ID, and it'll give you all info

## arXiv SDK Integration    

The project uses the official arXiv Python SDK (`arxiv` package) to interact with arXiv's API. 
Key features:

- **Search Functionality**: Uses `arxiv.Search` for paper queries
- **Result Processing**: Handles paper metadata
- **Client Management**: Uses `arxiv.Client` for API requests

## Prerequisites

- Python 3.x
- Anthropic API key (Claude API access)
- Internet connection
- arXiv API access (no key required)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
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
python chatbot.py
```

2. Example queries:
   - "Search for papers about quantum computing"
   - "Get information about paper paper_id_here"
   - Type 'quit' to exit


## Contributing
Feel free to submit issues and enhancement requests! ☺️



## 
Fetch the content of this website: https://modelcontextprotocol.io/docs/concepts/architecture and save the content in the file "mcp_summary.md", create a visual diagram that summarizes the content of "mcp_summary.md" and save it in a text file

##
Resources are a core primitive in the MCP that allow servers to expose data and content that can be read by clients and used as context for LLM interactions.