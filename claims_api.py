# claims_api.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import json
import sys
import smtplib # For sending emails
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime # For dynamic subject line

from dotenv import load_dotenv

# Load environment variables from .env file for local development
# On Render, environment variables are injected directly.
load_dotenv()

# --- Security Check: Ensure OpenAI API Key is available ---
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("CRITICAL ERROR: OPENAI_API_KEY environment variable not set.")
    print("Please ensure it's configured in Render.com's environment variables or in your local .env file.")
    sys.exit(1) # Exit the process if key is missing

# --- Import your existing CrewAI logic ---
# This import assumes main.py is in the same directory or accessible via Python path.
try:
    from main import run_claims_triage_system
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import run_claims_triage_system from main.py: {e}")
    print("Please ensure main.py is in the correct directory and its content is structured for import.")
    sys.exit(1)

app = FastAPI()

# --- Configure CORS ---
# In a no-n8n scenario, who will be calling this API?
# If it's your React frontend, add its URL (e.g., "http://localhost:3000" for local dev)
# If it's another internal system, it might not need CORS or might need specific domains.
# For demo/testing, "*" is functional but REMEMBER to secure this in production.
origins = [
    "*", # WARNING: Only use "*" for development/testing!
         # For production, replace with specific frontend/client URLs, e.g.:
         # "https://your-react-app.com",
         # "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Email Sending Function ---
def send_audit_email(subject: str, body: str, receiver_email: str):
    """
    Sends an email with the audit summary.
    Email configuration should be in environment variables for security.
    """
    sender_email = os.getenv("EMAIL_SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_SENDER_PASSWORD") # Use App Password for Gmail/Outlook
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587)) # Default to 587 (STARTTLS)

    if not all([sender_email, sender_password, smtp_server, receiver_email]):
        print("CRITICAL ERROR: Email sending configuration missing. Email will not be sent.")
        print("Required: EMAIL_SENDER_EMAIL, EMAIL_SENDER_PASSWORD, SMTP_SERVER, RECEIVER_EMAIL")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain')) # Use 'plain' for markdown, 'html' for HTML

    try:
        print(f"INFO: Attempting to send email to {receiver_email} via {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("INFO: Audit email sent successfully!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP Authentication failed. Check username and password (or App Password).")
        return False
    except smtplib.SMTPConnectError:
        print("ERROR: SMTP Connection failed. Check SMTP server and port.")
        return False
    except Exception as e:
        print(f"ERROR: Failed to send audit email: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- API Request Models ---
# The endpoint will now directly expect a list of claims objects.
# This aligns with the structure of your data/claims.json file.
class ClaimItem(BaseModel):
    claim_id: str
    member_id: str
    provider_id: str
    procedure_code: str
    diagnosis_code: str
    cost: int
    date_of_service: str
    claim_type: str

class ClaimsProcessingRequest(BaseModel):
    # This directly represents the list of claims you'd find in claims.json
    claims: list[ClaimItem]
    # Optionally, you could add an email_receiver here if it's dynamic
    # receiver_email: str = os.getenv("DEFAULT_RECEIVER_EMAIL", "default.audit@example.com")

@app.get("/")
async def read_root():
    """
    A simple root endpoint to confirm the backend is running.
    Access it at your Render URL (e.g., https://perfexion-claims-api.onrender.com/)
    """
    return {"message": "Perfexion Claims Triage API is running and healthy!"}

@app.post("/process-claims")
async def process_claims_endpoint(request: ClaimsProcessingRequest):
    """
    Receives claims data, processes it using the CrewAI system,
    and sends the audit summary email directly.
    Access it via POST requests to your Render URL + /process-claims
    (e.g., https://perfexion-claims-api.onrender.com/process-claims)
    """
    # Convert the Pydantic model list of claims back to a JSON string
    # because run_claims_triage_system still expects a JSON string.
    claims_data_json_string = json.dumps([claim.model_dump() for claim in request.claims])

    print(f"INFO: Received {len(request.claims)} claims for processing.")
    print(f"DEBUG: Claims payload start: {claims_data_json_string[:500]}...")

    try:
        # Call your CrewAI system's main function
        audit_summary = run_claims_triage_system(claims_data_json_string)

        print("INFO: Claims processed successfully by CrewAI. Preparing email...")

        # --- Send Email Directly ---
        receiver_email = os.getenv("RECEIVER_EMAIL", "your.audit.team@perficient.com") # Default or from env
        email_subject = f"PERFIXION Claims Audit Report - {datetime.now().strftime('%Y-%m-%d')}"

        email_sent_success = send_audit_email(
            subject=email_subject,
            body=audit_summary,
            receiver_email=receiver_email
        )
        if not email_sent_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Claims processed, but failed to send audit email. Check server logs."
            )

        print("INFO: Workflow completed. Email sending initiated.")
        return {
            "status": "success",
            "message": "Claims processed successfully and audit email sent.",
            "audit_summary_preview": audit_summary[:200] + "..." # Send a preview, not full summary in API response
        }

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format received: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format in request body: {e}"
        )
    except HTTPException: # Re-raise HTTPExceptions (e.g., from email failure)
        raise
    except Exception as e:
        print(f"CRITICAL ERROR: An unexpected error occurred during claims processing: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred. Please check Render logs for details: {e}"
        )

if __name__ == "__main__":
    print("Starting FastAPI server locally...")
    uvicorn.run(app, host="0.0.0.0", port=8000)