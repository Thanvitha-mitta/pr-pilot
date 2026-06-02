import os
import sys
from github import Github, Auth
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agent.state import GraphState
from app.indexer.embedder import CodeEmbedder
from app.models.review import PRReview
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def fetch_pr_node(state: GraphState):
    print("-> [NODE 1] Fetching REAL PR diff from GitHub...")
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    g = Github(auth=auth)
    
    repo = g.get_repo(state["repo_name"])
    pr = repo.get_pull(state["pr_number"])
    
    diffs =[]
    # We will just fetch the first file for testing speed
    for file in pr.get_files()[:1]:
        if file.patch:
            diffs.append({"filename": file.filename, "patch": file.patch})
            
    return {"diffs": diffs}

def retrieve_context_node(state: GraphState):
    print("-> [NODE 2] Searching Qdrant Database for code context...")
    if not state.get("diffs"):
        return {"context": "No context found."}
        
    diff_text = state["diffs"][0]["patch"]
    
    # Connect to Qdrant and search using the diff text!
    embedder = CodeEmbedder()
    results = embedder.search_similar_code(query=diff_text, limit=2)
    
    # Combine the top 2 matching code chunks into a single string
    context = "\n\n".join([res.document for res in results])
    return {"context": context}

def llm_review_node(state: GraphState):
    print("->[NODE 3] Sending Diff + Qdrant Context to Groq Llama 3.3...")
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(PRReview)
    
    # Notice we now give the AI the context from the database!
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert code reviewer. Use the provided Codebase Context to understand the repository. Find bugs and issues in the PR Diff."),
        ("human", "Codebase Context from Qdrant:\n{context}\n\nFile: {filename}\nPR Diff:\n{diff}")
    ])
    
    review_chain = prompt | structured_llm
    
    file_diff = state["diffs"][0]
    response = review_chain.invoke({
        "context": state["context"],
        "filename": file_diff["filename"],
        "diff": file_diff["patch"]
    })
    
    return {"review_comments": response.comments}

def post_comments_node(state: GraphState):
    print("-> [NODE 4] Posting reviews directly to GitHub...")
    
    if not state.get("review_comments"):
        print("No comments to post.")
        return state
        
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    g = Github(auth=auth)
    
    try:
        repo = g.get_repo(state["repo_name"])
        pr = repo.get_pull(state["pr_number"])
        
        # Format the JSON reviews into a beautiful Markdown comment
        body = "### 🤖 AI PR Review Agent\n\n"
        body += "*I have analyzed this PR and found the following issues:*\n\n"
        
        for review in state["review_comments"]:
            emoji = "🔴" if review.severity.lower() == "high" else "🟡" if review.severity.lower() == "medium" else "🔵"
            body += f"{emoji} **[{review.severity.upper()}]** `File: {review.file_path}` (Line {review.line_number})\n"
            body += f"> {review.comment}\n\n"
            
        # Post the comment to the PR!
        pr.create_issue_comment(body)
        print("✅ SUCCESS! Review posted to GitHub!")
        
    except Exception as e:
        print(f"❌ Failed to post comment: {e}")
        
    return state