# claims_api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import json
from dotenv import load_dotenv

# Load environment variables (ensure .env is in your backend folder or parent)
load_dotenv()

# --- Import your existing CrewAI logic ---
# Ensure the path is correct if claims_api.py is not in the root of your CrewAI project
# For simplicity, assuming claims_api.py is alongside main.py, agents.py, tasks.py
# If main.py is in 'perfixion_claims_system/' and claims_api.py is in 'perfixion_claims_system/backend'
# you might need sys.path adjustments or careful relative imports.
# For this example, let's assume all these files are in the same 'backend' directory.
# OR, more cleanly, adjust your imports in `main.py` so that `run_claims_triage_system` is importable.
# Let's modify main.py slightly to make it a callable function.

# --- IMPORTANT: Update main.py to be importable ---
# BEFORE proceeding, open your current `main.py` and modify it.
# Change the `if __name__ == "__main__":` block to be just a direct call if you only run it via API,
# or better, keep the `if __name__` and make `run_claims_triage_system` a standard function.
# The `run_claims_triage_system` function as I provided it previously is already good for importing!
# So you can just import it directly.

from main import run_claims_triage_system # Import the function directly
# Make sure your main.py DOES NOT run anything when imported.
# It should look like:
# def run_claims_triage_system(claims_data_json_string):
#    ... your crewai logic ...
# if __name__ == "__main__":
#    # This block only runs when main.py is executed directly, not when imported
#    parser = argparse.ArgumentParser(...)
#    ... handle args and call run_claims_triage_system ...


# Initialize FastAPI app
app = FastAPI()

# Configure CORS (Important for n8n to talk to your local/self-hosted service)
# If your n8n Cloud instance has a fixed domain, you should specify it here for better security.
# For local testing, '*' or your n8n Cloud instance URL is fine.
origins = [
    "*", # WARNING: Use specific origin(s) in production for security!
    # "https://your-n8n-cloud-instance.n8n.cloud", # Example for n8n Cloud
    # "http://localhost:5678", # If you run n8n locally for testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Define the request body model for incoming claims
class ClaimsRequest(BaseModel):
    claims_data: str # Expects a JSON string of claims

@app.get("/")
async def read_root():
    """
    A simple root endpoint to confirm the backend is running.
    """
    return {"message": "Perfexion Claims Triage API is running!"}

@app.post("/process-claims")
async def process_claims_endpoint(request: ClaimsRequest):
    """
    Receives claims data, processes it using the CrewAI system,
    and returns the audit summary and other results.
    """
    claims_data_json_string = request.claims_data
    print(f"Received claims data from n8n: {claims_data_json_string[:100]}...") # Log first 100 chars

    try:
        # Call your CrewAI system's main function
        # Ensure run_claims_triage_system returns the desired output (e.g., the audit summary string)
        audit_summary = run_claims_triage_system(claims_data_json_string)

        # You might also want to read the generated JSON files (routed_claims.json, etc.) here
        # and include them in the response if n8n needs them directly.
        # For simplicity, let's assume the audit summary is enough for now.
        # If you need other files, you'd read them here:
        # with open('routed_claims.json', 'r') as f:
        #    routed_claims = json.load(f)

        return {
            "status": "success",
            "message": "Claims processed successfully",
            "audit_summary": audit_summary,
            # "routed_claims": routed_claims # Add if needed
        }

    except Exception as e:
        print(f"Error during claims processing: {e}")
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during claims processing: {e}"
        )

# To run this FastAPI application:
# uvicorn claims_api:app --reload --host 0.0.0.0 --port 8000