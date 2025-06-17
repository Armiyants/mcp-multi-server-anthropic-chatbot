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
        paper_path = os.path.join(topic_dir, "papers_info.json")
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
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    return f"There's no saved information related to paper {paper_id}."

#resources are read-only data that applications can choose to use or we can give to a model 
#let's now add resources to our server 
@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the papers directory.
    """
    folders = []
    #let's now get all topic directories 
    if os.path.exists(PAPERS_DIR):
        for topic_dir in os.listdir(PAPERS_DIR):
            topic_path = os.path.join(PAPERS_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)

    #Let's create a simple markdown list
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += "\nUse @{folder} to access papers in this topic.\n"
    else:
        content += "No topics found.\n"
    return content


@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """ 
    Get detailed information about papers on a specific topic.
    
    Required Arguments:
        "topic": The research topic to retrieve papers for. 
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPERS_DIR, topic_dir, "papers_info.json")
    
    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nPlease try searching for papers on this topic first."
    
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        
        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"
        
        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            content += f"### Summary\n{paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"
        
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."


if __name__ == "__main__":
    # Initialize and run the server
    try:
        print("Starting MCP server...")
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"Error starting server: {str(e)}")

