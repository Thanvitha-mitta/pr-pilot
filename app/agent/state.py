from typing import TypedDict, List, Dict, Any

class GraphState(TypedDict):
    """
    This is the 'memory' of our AI agent. 
    As the agent moves from step to step, it will fill in these variables.
    """
    repo_name: str
    pr_number: int
    
    # Populated by Node 1 (Fetch)
    diffs: List[Dict[str, str]]  # List of {"filename": "...", "patch": "..."}
    
    # Populated by Node 2 (Retrieve Context)
    context: str                 # The raw code chunks retrieved from Qdrant
    
    # Populated by Node 3 (Review)
    review_comments: List[Any]   # The final JSON structured output from Groq