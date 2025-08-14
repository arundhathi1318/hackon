# main.py
import os
import json
import argparse
from crewai import Crew, Process
from dotenv import load_dotenv
from agents import ClaimsAgents
from tasks import MOCK_CPT_CODES, MOCK_ICD_CODES, MOCK_MEMBERS, ClaimsTasks

load_dotenv()

def run_claims_triage_system(claims_data_json_string):
   
    agents = ClaimsAgents()
    tasks = ClaimsTasks()

    # --- DEFINE AGENT OBJECTS HERE ---
    # You need to call the methods on the 'agents' instance
    intake_agent = agents.intake_agent()
    validation_agent = agents.validation_agent()
    anomaly_detection_agent = agents.anomaly_detection_agent()
    llm_explanation_agent = agents.llm_explanation_agent()
    routing_agent = agents.routing_agent()
    audit_summary_agent = agents.audit_summary_agent()

    # --- DEFINE TASK OBJECTS HERE ---
    # You need to call the methods on the 'tasks' instance
    task_parse_categorize = tasks.parse_and_categorize_claims(
        agent=intake_agent
    )
    task_validate = tasks.validate_claims(
        agent=validation_agent,
        context=[task_parse_categorize]
    )
    task_detect_anomalies = tasks.detect_anomalies(
        agent=anomaly_detection_agent,
        context=[task_validate]
    )
    task_generate_explanation = tasks.generate_anomaly_explanation(
        agent=llm_explanation_agent,
        context=[task_detect_anomalies]
    )
    task_route_claims = tasks.route_claims(
        agent=routing_agent,
        context=[task_generate_explanation]
    )
    task_summarize_audit = tasks.summarize_audit_claims(
        agent=audit_summary_agent,
        context=[task_route_claims]
    )

    # --- Now the agents and tasks are defined and can be used in Crew ---
    claims_crew = Crew(
        agents=[
            intake_agent,
            validation_agent,
            anomaly_detection_agent,
            llm_explanation_agent,
            routing_agent,
            audit_summary_agent
        ],
        tasks=[
            task_parse_categorize,
            task_validate,
            task_detect_anomalies,
            task_generate_explanation,
            task_route_claims,
            task_summarize_audit
        ],
        process=Process.sequential,
        verbose=True,
        max_rpm=29
    )

    print("--- Starting the Claims Triage & Validation Process ---")

    # Kick off the process with the received claims data
    result = claims_crew.kickoff(inputs={'raw_claims_data': claims_data_json_string})

    print("\n\n--- Claims Triage & Validation Process Completed ---")
    print("Final Audit Summary:")
    print(result) # Still prints to console where FastAPI runs

    return result

if __name__ == "__main__":
    # This block only runs if main.py is executed directly, not when imported by claims_api.py
    parser = argparse.ArgumentParser(description="Run the Multi-Agent Claims Triage & Validation System.")
    parser.add_argument('--claims_file', type=str, help='Path to the JSON file containing claims data.')
    parser.add_argument('--claims_json_string', type=str, help='JSON string containing claims data.')
    args = parser.parse_args()

    claims_data_to_process = None
    if args.claims_file:
        try:
            with open(args.claims_file, 'r', encoding='utf-8') as f:
                claims_data_to_process = f.read()
        except FileNotFoundError:
            print(f"Error: Claims file not found at {args.claims_file}")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {args.claims_file}")
            exit(1)
    elif args.claims_json_string:
        claims_data_to_process = args.claims_json_string
    else:
        # Fallback to loading from data/claims.json if no argument provided (for local testing)
        claims_file_path = os.path.join(os.path.dirname(__file__), 'data', 'claims.json')
        try:
            with open(claims_file_path, 'r', encoding='utf-8') as f:
                claims_data_to_process = f.read()
        except FileNotFoundError:
            print(f"Error: Default claims file not found at {claims_file_path}. Please provide --claims_file or --claims_json_string.")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in default claims file {claims_file_path}.")
            exit(1)

    if claims_data_to_process:
        run_claims_triage_system(claims_data_to_process)