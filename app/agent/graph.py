import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph.graph import StateGraph, END
from app.agent.state import GraphState
from app.agent.nodes import fetch_pr_node, retrieve_context_node, llm_review_node
from app.agent.nodes import fetch_pr_node, retrieve_context_node, llm_review_node, post_comments_node

def build_agent_graph():
    workflow = StateGraph(GraphState)

    # Add the 4 nodes
    workflow.add_node("fetch", fetch_pr_node)
    workflow.add_node("retrieve", retrieve_context_node)
    workflow.add_node("review", llm_review_node)
    workflow.add_node("post", post_comments_node) # NEW

    # Define the flow
    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "retrieve")
    workflow.add_edge("retrieve", "review")
    workflow.add_edge("review", "post")           # MODIFIED
    workflow.add_edge("post", END)                # NEW

    return workflow.compile()


if __name__ == "__main__":
    agent = build_agent_graph()
    
    print("Starting LangGraph Agent Pipeline...\n")
    
    # TESTING ON A REAL PR
    initial_state = {
        "repo_name": "microsoft/TypeScript",
        "pr_number": 57610
    }
    
    final_state = agent.invoke(initial_state)
    
    print("\n" + "="*50)
    print("🎯 FINAL AI REVIEWS GENERATED:")
    print("="*50)
    
    for review in final_state.get('review_comments', []):
        print(f"[{review.severity.upper()}] Line {review.line_number} in {review.file_path}:")
        print(f"Comment: {review.comment}\n")