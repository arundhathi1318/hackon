# claims_api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn # Used for the __main__ block if running directly
import os
import json
import sys
from dotenv import load_dotenv

# Load environment variables from .env file for local development
# On Render, environment variables are injected directly and this line
# doesn't strictly load them, but it causes no harm.
load_dotenv()

# --- Security Check: Ensure OpenAI API Key is available ---
# This is a crucial check for deployment. agents.py also checks,
# but having it here provides immediate feedback if missing.
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    # Use a print statement for logs on Render, and raise an error to halt startup
    print("CRITICAL ERROR: OPENAI_API_KEY environment variable not set.")
    print("Please ensure it's configured in Render.com's environment variables or in your local .env file.")
    # Exit or raise an error to prevent the app from starting without the key
    sys.exit(1) # Exit the process if key is missing

# --- Import your existing CrewAI logic ---
# This import assumes main.py is in the same directory or accessible via Python path.
# Ensure that main.py's `run_claims_triage_system` function is indeed importable
# and that main.py itself doesn't execute core logic when imported (use if __name__ == "__main__":).
try:
    from main import run_claims_triage_system
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import run_claims_triage_system from main.py: {e}")
    print("Please ensure main.py is in the correct directory and its content is structured for import.")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI()

# --- Configure CORS (Cross-Origin Resource Sharing) ---
# IMPORTANT: For production, do NOT use ["*"] for allow_origins.
# Replace "*" with the specific URL(s) of your n8n Cloud instance and any other frontends.
# Example for n8n Cloud: "https://your-instance-name.app.n8n.cloud"
# If you have a React frontend, add its URL too: "http://localhost:3000" (for local dev)
# For this specific workflow with n8n Cloud, likely only one origin is needed.
specific_n8n_cloud_origin = os.getenv("N8N_CLOUD_ORIGIN", "https://arundhathi1318.app.n8n.cloud") # Example
# For better security, if only n8n is calling it:
# origins = [specific_n8n_cloud_origin]
# Or if you have other known origins:
origins = [
    specific_n8n_cloud_origin,
    # Add other origins as needed, e.g., "https://your-react-frontend.com"
]

# For local development, you might temporarily use:
# origins = ["*", "http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Your allowed client origins
    allow_credentials=True, # Allow cookies/auth headers
    allow_methods=["*"],    # Allows POST, GET, etc.
    allow_headers=["*"],    # Allows all headers in requests
)

# Define the request body model for incoming claims
# This expects a JSON string of claims from n8n
class ClaimsRequest(BaseModel):
    claims_data: str 

@app.get("/")
async def read_root():
    """
    A simple root endpoint to confirm the backend is running.
    Access it at your Render URL (e.g., https://perfexion-claims-api.onrender.com/)
    """
    return {"message": "Perfexion Claims Triage API is running and healthy!"}

@app.post("/process-claims")
async def process_claims_endpoint(request: ClaimsRequest):
    """
    Handles incoming claims data from n8n, processes it using the CrewAI system,
    and returns the audit summary.
    Access it via POST requests to your Render URL + /process-claims
    (e.g., https://perfexion-claims-api.onrender.com/process-claims)
    """
    claims_data_json_string = request.claims_data
    # Log the start of processing and the first part of the received data for debugging
    print(f"INFO: Received claims data from n8n. Processing initiated...")
    print(f"DEBUG: Claims payload start: {claims_data_json_string[:500]}...") # Log more for better debugging

    try:
        # Call your CrewAI system's main function
        # This function should return the final audit summary as a string.
        audit_summary = run_claims_triage_system(claims_data_json_string)

        # Log success before returning
        print("INFO: Claims processed successfully by CrewAI.")

        # Return the structured response to n8n
        return {
            "status": "success",
            "message": "Claims processed successfully",
            "audit_summary": audit_summary,
            # If you want to return other generated files (like routed_claims.json),
            # you would read them here and include them in the JSON response.
            # E.g., "routed_claims_data": json.loads(open('routed_claims.json', 'r').read())
        }

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format in claims_data: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=400, # Bad Request for invalid input JSON
            detail=f"Invalid JSON format in 'claims_data' field: {e}"
        )
    except Exception as e:
        # Catch any other unexpected errors during CrewAI processing
        print(f"CRITICAL ERROR: An unexpected error occurred during claims processing: {e}")
        import traceback
        traceback.print_exc() # Print full traceback to Render logs for debugging
        raise HTTPException(
            status_code=500, # Internal Server Error
            detail=f"An internal error occurred while processing your request. Please check server logs for details: {e}"
        )

# This block allows you to run the FastAPI app directly using 'python claims_api.py'
# for local development, which is convenient.
if __name__ == "__main__":
    print("Starting FastAPI server locally...")
    uvicorn.run(app, host="0.0.0.0", port=8000)