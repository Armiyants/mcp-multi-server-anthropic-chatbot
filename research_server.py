from mcp.server.fastmcp import FastMCP
import arxiv
from typing import List
import os
import json 

PAPERS_DIR = os.path.join(os.path.dirname(__file__), "papers")

# Initialize the MCP server with explicit configuration
mcp = FastMCP(
    name="research",
    description="A server for searching and extracting information from arXiv papers",
    version="1.0.0",
    port=8001,
)

#let's now define our tools 
#it's as easy as using the @mcp.tool decorator
@mcp.tool()
def get_arxiv_papers(topic: str, max_results: int = 2) -> List[str]:
    """
    Search for papers on arXiv based on a given topic.
    
    Args:
        topic: The topic to search for
        max_results: The maximum number of results to return

    Returns:
        List of paper objects
    """
    
    # Use arxiv to find the papers 
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # Create directory for this topic
    path = os.path.join(PAPERS_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"Results are saved in: {file_path}")
    
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
        content += "\nUse @<topic> to access papers in this topic.\n"
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
        
        # let's now create a markdown content with paper details to return 
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

# "prompt" is meant to be user controlled, and the server can also provide a "prompt template" to the client 
# so that the user can use the template and not have todo the whole prompt engineering themselves, 
# but provide only the dynamic values needed to be filled in the template 
# let's now add a prompt template to our server 
@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """
    Generate a prompt for Claude to search, find and then discuss the papers on a specific topic.
    """ 
    return f"""
    You are an experienced and very helpful assistant that can search for papers on a specific topic.
    Search for {num_papers} academic papers about '{topic}' using the get_arxiv_papers tool. 

    Follow these steps: 
    1. First, search for the papers using get_arxiv_papers(topic='{topic}', max_results={num_papers})
    2. For each paper found, extract and organize the following information using the extract_info tool:
   - Paper title
   - Authors
   - Publication date
   - Brief summary of the key findings
   - Main contributions or innovations
   - Methodologies used
   - Relevance to the topic '{topic}'

    3. Once you have the information for all papers, provide a comprehensive summary that includes:
   - Overview of the current state of research in '{topic}'
   - Common themes and trends across the papers
   - Key research gaps or areas for future investigation
   - Most impactful or influential papers in this area

   4. Organize your findings in a clear, to the point and concise manner, structured in a format with headings and bullet points for easy readeability. 

   Please present both detailed information about each paper and a high level summary of the current research state in {topic}."""

if __name__ == "__main__":
    # Initialize and run the server
    try:
        print("Starting MCP server...")
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"Error starting server: {str(e)}")

