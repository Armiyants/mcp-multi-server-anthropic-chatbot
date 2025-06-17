from mcp.server.fastmcp import FastMCP
import arxiv
from typing import List
import variables
import os
import json

PAPERS_DIR = variables.PAPERS_DIR

# Initialize the MCP server with explicit configuration
mcp = FastMCP(
    name="research_mcp",
    description="A server for searching and extracting information from arXiv papers",
    version="1.0.0"
)

#let's now define our tools 
#it's as easy as using the @mcp.tool decorator

@mcp.tool()
def get_arxiv_papers(topic: str, max_results: int = 5) -> List[arxiv.Result]:
    """
    Search for papers on arXiv based on a given topic.
    
    Args:
        topic: The topic to search for
        max_results: The maximum number of results to return

    Returns:
        List of paper objects
    """
    
    client = arxiv.Client() 
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance,
    )
    
    papers = client.results(search)
    
    # Create directory for the eachtopic, if it doesn't exist
    topic_dir = os.path.join(PAPERS_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(topic_dir, exist_ok=True)

    papers_metadata = variables.papers_metadata

    # load exsisting papers metadata with try-except block
    try:
        with open(os.path.join(topic_dir, "papers.json"), "r") as file:
            papers_metadata = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        paper_metadata = {}

    # Process each paper and save metadata to papers_metadata and append to paper_ids
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_metadata = {
            "id": paper.get_short_id(),
            "title": paper.title,
            "summary": paper.summary,
            "authors": [author.name for author in paper.authors],
            "published": str(paper.published.strftime("%Y-%m-%d")),
            "updated": str(paper.updated.strftime("%Y-%m-%d")),
            "pdf_url": paper.pdf_url
        }
        papers_metadata[paper.get_short_id()] = paper_metadata

        #save metadata to json file in topic directory
        paper_path = os.path.join(topic_dir, f"{paper.get_short_id()}.json")

        try: 
            with open(paper_path, "w") as json_file:
                json.dump(paper_metadata, json_file, indent=2)
        except Exception as e:
            print(f"Error saving paper metadata: {e}")
            continue

        print(f"Results are saved in: {topic_dir}")

    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
    if not os.path.exists(PAPERS_DIR):
        return f"Papers directory '{PAPERS_DIR}' does not exist. Please run a search first."
 
    for item in os.listdir(PAPERS_DIR):
        item_path = os.path.join(PAPERS_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, f"{paper_id}.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as papers_metadata:
                        papers_info = json.load(papers_metadata)
                        return json.dumps(papers_info, indent=4)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"Paper {paper_id} not found. Try searching for it first using 'get_arxiv_papers'."

#now let's write a command to start running the server by specifying the transport protocol
if __name__ == "__main__":
    try:
        print("Starting MCP server...")
        import asyncio
        asyncio.run(mcp.run(transport="stdio"))
    except Exception as e:
        print(f"Error starting server: {str(e)}")

