import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.review import PRReview
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def run_evaluation():
    print("🚀 Starting AI Evaluation Harness...\n")
    
    # 1. Load the ground truth dataset
    with open("evals/test_prs.json", "r") as f:
        test_prs = json.load(f)
        
    # 2. Setup the LLM Chain (bypassing the GitHub fetcher for speed)
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0) # Temp 0.0 for deterministic testing
    structured_llm = llm.with_structured_output(PRReview)
    
    # We are making the prompt much stricter to eliminate False Positives
# THE NUCLEAR PROMPT
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Staff Engineer. 
        Your ONLY job is to catch CRITICAL logic bugs or security flaws.
        IF THE CODE IS FUNCTIONALLY CORRECT, YOU MUST RETURN AN EMPTY LIST.
        DO NOT report style issues. DO NOT report missing docstrings. DO NOT report missing type hints.
        If you invent a bug on perfect code, the system will crash.
        
        Example response for acceptable code:
        {{"comments": []}}
        """),
        ("human", "File: {filename}\nDiff:\n{diff}")
    ])
    
    review_chain = prompt | structured_llm

    total_prs = len(test_prs)
    passed_evals = 0

    for pr in test_prs:
        print(f"Testing {pr['pr_id']}...")
        response = review_chain.invoke({"filename": pr["filename"], "diff": pr["diff"]})
        ai_comments_text = " ".join([c.comment.lower() for c in response.comments])
        expected_keywords = pr["expected_issues_keywords"]
        
        if not expected_keywords:
            if len(response.comments) == 0:
                print("✅ PASS: AI correctly identified perfect code (No False Positives).")
                passed_evals += 1
            else:
                print("❌ FAIL: AI hallucinated a bug! (False Positive)")
                # THIS WILL PRINT EXACTLY WHAT THE AI HALLUCINATED
                print(f"   -> AI complained about: {response.comments[0].comment}")
        else:
            caught_keywords =[kw for kw in expected_keywords if kw in ai_comments_text]
            if len(caught_keywords) > 0:
                print(f"✅ PASS: AI caught the issue! (Keywords matched: {caught_keywords})")
                passed_evals += 1
            else:
                print(f"❌ FAIL: AI missed the issue. (Expected keywords: {expected_keywords})")
        print("-" * 40)

    # 4. Calculate Final Metrics
    accuracy = (passed_evals / total_prs) * 100
    print("\n" + "=" * 40)
    print("📊 EVALUATION RESULTS")
    print("=" * 40)
    print(f"Total PRs Evaluated : {total_prs}")
    print(f"Successful Evals    : {passed_evals}")
    print(f"System Accuracy     : {accuracy:.1f}%")
    print("=" * 40)

if __name__ == "__main__":
    run_evaluation()