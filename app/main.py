import os
import hmac
import hashlib
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from dotenv import load_dotenv

# Import your LangGraph agent!
from app.agent.graph import build_agent_graph

load_dotenv()

app = FastAPI(title="AI PR Review Agent")
agent = build_agent_graph()

# ==========================================
# BACKGROUND TASK: RUN THE AI PIPELINE
# ==========================================
def run_review_pipeline(repo_name: str, pr_number: int):
    print(f"\n[BACKGROUND TASK] Waking up AI Agent for {repo_name} PR #{pr_number}...")
    
    initial_state = {
        "repo_name": repo_name,
        "pr_number": pr_number
    }
    
    # Run the state machine
    final_state = agent.invoke(initial_state)
    
    print("\n" + "="*50)
    print("🎯 AI REVIEW COMPLETE!")
    print("="*50)
    for review in final_state.get('review_comments', []):
        print(f"[{review.severity.upper()}] Line {review.line_number}: {review.comment}")
    print("="*50)
    
    # (In the next step, we will add the code here to post these comments directly back to GitHub!)

# ==========================================
# WEBHOOK ENDPOINT
# ==========================================
@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # 1. Get the raw payload
    payload = await request.body()
    
    # 2. SECURITY: Verify the HMAC signature from GitHub
    # This prevents random people from triggering your AI
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "super_secret_test_key").encode()
    signature = request.headers.get("x-hub-signature-256")
    
    if not signature:
        # We will bypass security JUST for our local testing right now, 
        # but in production, this would raise an error!
        print("Warning: No signature found, but proceeding for local testing.")
    else:
        expected_signature = "sha256=" + hmac.new(webhook_secret, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            raise HTTPException(status_code=401, detail="Invalid signature. Hacker detected!")
            
    # 3. Parse the JSON data sent by GitHub
    data = await request.json()
    
    # 4. Check if the event is a Pull Request being Opened or Updated
    if "pull_request" in data and data.get("action") in ["opened", "synchronize"]:
        repo_name = data["repository"]["full_name"]
        pr_number = data["pull_request"]["number"]
        
        print(f"🔔 WEBHOOK RECEIVED: PR #{pr_number} in {repo_name} was {data.get('action')}!")
        
        # 5. Hand the work to the LangGraph AI in the background
        # This allows the server to instantly return a response to GitHub without waiting for the LLM!
        background_tasks.add_task(run_review_pipeline, repo_name, pr_number)
        
        return {"status": "Success! AI Review queued in background."}
        
    return {"status": "Ignored. Event is not a PR creation/update."}


@app.get("/")
def home():
    return {
        "status": "🟢 Online",
        "message": "🤖 PR-Pilot AI Agent is actively listening for GitHub Webhooks.",
        "project_by": "Mitta Thanvitha"
    }