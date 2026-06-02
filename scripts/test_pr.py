import os
import sys
from github import Github, Auth
from dotenv import load_dotenv

# Pydantic & Langchain for structured Groq output
from pydantic import BaseModel, Field
from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ==========================================
# 1. DEFINE STRUCTURED OUTPUT (PYDANTIC)
# ==========================================
class ReviewComment(BaseModel):
    file_path: str = Field(description="The path of the file being reviewed")
    line_number: int = Field(description="The exact line number where the issue occurs in the diff")
    severity: str = Field(description="Severity of the issue: 'low', 'medium', or 'high'")
    comment: str = Field(description="The review comment text explaining the issue and suggesting a fix")

class PRReview(BaseModel):
    comments: List[ReviewComment] = Field(description="List of review comments for the pull request")

# ==========================================
# 2. SETUP GROQ LLM & PROMPT
# ==========================================
# Using the massive 70-Billion parameter Llama 3 model for free!
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)

# This is the magic that forces Groq to return JSON matching our Pydantic classes
structured_llm = llm.with_structured_output(PRReview)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert software engineer reviewing code. You must identify bugs, security issues, style violations, and missing tests. Return the issues in the requested structured format."),
    ("human", "Review this code diff and point out issues:\n\nFile: {filename}\n\nDiff:\n{diff}")
])

review_chain = prompt | structured_llm

# ==========================================
# 3. FETCH PR & REVIEW (EXECUTION)
# ==========================================
def main():
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    g = Github(auth=auth)
    
    repo_name = "microsoft/TypeScript"
    pr_number = 57610
    
    print(f"Fetching PR {pr_number} from {repo_name}...")
    try:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        diffs =[]
        for file in pr.get_files():
            if file.patch:
                diffs.append({"filename": file.filename, "patch": file.patch})
                
    except Exception as e:
        print(f"ERROR fetching PR: {e}")
        sys.exit(1)

    if not diffs:
        print("No diffs found.")
        sys.exit(1)

    print("-" * 50)
    print("AI REVIEW (Structured JSON via Groq):")
    print("-" * 50)
    
    # Let's just review the first file to test
    file_diff = diffs[0]
    print(f"\nReviewing file: {file_diff['filename']}...\n")
    
    try:
        # Pass the data to Groq
        response = review_chain.invoke({
            "filename": file_diff['filename'],
            "diff": file_diff['patch']
        })
        
        # 'response' is a Python object parsed from Groq's JSON output
        for issue in response.comments:
            print(f"[{issue.severity.upper()}] Line {issue.line_number}: {issue.comment}")
            
    except Exception as e:
        print(f"Failed to parse LLM response: {e}")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()