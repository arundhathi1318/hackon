import os
from crewai import Crew, Process
from dotenv import load_dotenv

from agents import ClaimAgents
from tasks import ClaimTasks
from tools import ClaimTools

load_dotenv()

def run_claims_crew(claims_data_json: str):
    ClaimTools._MOCK_CLAIMS_DB = []

    agents = ClaimAgents()
    tasks = ClaimTasks(agents)

    intake_task = tasks.intake_claims(claims_json_string=claims_data_json)
    validate_task = tasks.validate_claims(context=[intake_task])
    detect_anomalies_task = tasks.detect_anomalies(context=[validate_task])
    generate_explanations_task = tasks.generate_explanations(context=[detect_anomalies_task])
    route_claims_task = tasks.route_claims(context=[generate_explanations_task])
    summarize_audit_task = tasks.summarize_audit(context=[route_claims_task])

    claims_crew = Crew(
        agents=[
            agents.claim_intake_agent(),
            agents.validation_agent(),
            agents.anomaly_detection_agent(),
            agents.llm_explanation_agent(),
            agents.routing_agent(),
            agents.audit_summary_agent()
        ],
        tasks=[
            intake_task,
            validate_task,
            detect_anomalies_task,
            generate_explanations_task,
            route_claims_task,
            summarize_audit_task
        ],
        verbose=True,
        process=Process.sequential,
        output_log_file='crew_output.log'
    )

    print("## Starting Claims Processing Crew...")
    result = claims_crew.kickoff()

    print("\n\n########################")
    print("## Claims Processing Finished")
    print("########################\n")
    print(result)

if __name__ == "__main__":
    sample_claims_json = """
[
 {
   "claim_id": "CLM001",
   "member_id": "MBR001",
   "provider_id": "PRV001",
   "procedure_code": "99285",
   "diagnosis_code": "M54.5",
   "cost": 1200,
   "date_of_service": "2025-07-15",
   "claim_type": "outpatient"
 },
 {
   "claim_id": "CLM002",
   "member_id": "MBR002",
   "provider_id": "PRV001",
   "procedure_code": "99285",
   "diagnosis_code": "M54.5",
   "cost": 400,
   "date_of_service": "2025-07-16",
   "claim_type": "outpatient"
 },
 {
   "claim_id": "CLM003",
   "member_id": "MBR001",
   "provider_id": "PRV002",
   "procedure_code": "INVALID_CPT",
   "diagnosis_code": "M54.5",
   "cost": 300,
   "date_of_service": "2025-07-17",
   "claim_type": "inpatient"
 },
 {
   "claim_id": "CLM004",
   "member_id": "MBR003",
   "provider_id": "PRV003",
   "procedure_code": "99213",
   "diagnosis_code": "J06.9",
   "cost": 100,
   "date_of_service": "2025-07-18",
   "claim_type": "pharmacy"
 },
 {
   "claim_id": "CLM005",
   "member_id": "MBR002",
   "provider_id": "PRV001",
   "procedure_code": "99285",
   "diagnosis_code": "M54.5",
   "cost": 400,
   "date_of_service": "2025-07-17",
   "claim_type": "outpatient"
 },
 {
   "claim_id": "CLM006",
   "member_id": "MBR001",
   "provider_id": "PRV001",
   "procedure_code": "99213",
   "diagnosis_code": "I10",
   "cost": 120,
   "date_of_service": "2025-07-19",
   "claim_type": "outpatient"
 }
]
    """

    run_claims_crew(sample_claims_json)
