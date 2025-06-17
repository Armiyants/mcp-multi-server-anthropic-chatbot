import os
import json
import variables

PAPER_DIR = variables.PAPERS_DIR

def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
    if not os.path.exists(PAPER_DIR):
        return f"Papers directory '{PAPER_DIR}' does not exist. Please run a search first."
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
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

if __name__ == "__main__":
    print(extract_info("2401.17231v2"))

    