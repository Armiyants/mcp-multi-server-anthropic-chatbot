import arxiv
import json
import os
from typing import List
import variables

PAPERS_DIR = variables.PAPERS_DIR

def get_arxiv_papers(topic: str, max_results: int = 5) -> List[arxiv.Result]:
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

if __name__ == "__main__":
    print(get_arxiv_papers("human brain"))