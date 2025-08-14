# tasks.py
import json
import os
from crewai import Task
from datetime import datetime

# --- Mock Data Loading (In-Memory for PoC Speed) ---
def load_mock_data(filename):
    file_path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

MOCK_CPT_CODES = load_mock_data('mock_cpt_codes.json')
MOCK_ICD_CODES = load_mock_data('mock_icd_codes.json')
MOCK_MEMBERS = load_mock_data('mock_members.json')
MOCK_CLAIMS_DATA = load_mock_data('claims.json')

class ClaimsTasks:
    def __init__(self):
        self.processed_claims = [] # To store claims throughout the pipeline
        self.flagged_claims = [] # To store claims flagged for audit

    def parse_and_categorize_claims(self, agent):
        return Task(
            description=(
                "Parse the raw claims data from the `data/claims.json` file. "
                "For each claim, extract 'claim_id', 'member_id', 'provider_id', "
                "'procedure_code', 'diagnosis_code', 'cost', 'date_of_service', and 'claim_type'. "
                "Categorize each claim based on its 'claim_type' (e.g., inpatient, outpatient, pharmacy). "
                "Return a list of dictionaries, where each dictionary represents a parsed claim "
                "and includes its determined category. Ensure all fields are present for each claim."
            ),
            expected_output="A JSON string representing a list of parsed claim dictionaries, "
                            "each with a 'category' field added, and 'status': 'parsed'. "
                            "Example: [{..., 'claim_type': 'outpatient', 'status': 'parsed'}, ...]",
            agent=agent,
            output_file='parsed_claims.json' # Save intermediate output
        )

    def validate_claims(self, agent, context):
        return Task(
            description=(
                "Validate the parsed claims from the previous step. "
                "For each claim: "
                "- Check for completeness (ensure all expected fields are present: claim_id, member_id, etc.). "
                "- Validate 'procedure_code' against MOCK_CPT_CODES. "
                "- Validate 'diagnosis_code' against MOCK_ICD_CODES. "
                "- Simulate 'member_id' eligibility check against MOCK_MEMBERS. "
                "Annotate each claim with a 'validation_status' (e.g., 'valid', 'invalid_cpt', 'invalid_icd', 'ineligible_member', 'incomplete_data') "
                "and add a 'validation_notes' field if any issues are found. "
                "Return the updated list of claims."
                f"\n\nMOCK_CPT_CODES: {MOCK_CPT_CODES}"
                f"\nMOCK_ICD_CODES: {MOCK_ICD_CODES}"
                f"\nMOCK_MEMBERS: {MOCK_MEMBERS}"
            ),
            expected_output="A JSON string representing a list of claims, each updated with 'validation_status' "
                            "and 'validation_notes' fields. Claims with issues should have a status other than 'valid'. "
                            "Example: [{..., 'validation_status': 'invalid_cpt', 'validation_notes': 'Procedure code not found'}, ...]",
            agent=agent,
            context=context, # Takes output from parse_and_categorize_claims
            output_file='validated_claims.json'
        )

    def detect_anomalies(self, agent, context):
        return Task(
            description=(
                "Analyze the validated claims to detect anomalies. "
                "For each claim: "
                "- **Cost Anomaly:** Compare 'cost' against the 'avg_cost' in MOCK_CPT_CODES for its 'procedure_code'. "
                "  Flag if cost is more than 2.5 times the average. "
                "- **Duplicate Claim:** Check for claims with the same 'member_id', 'provider_id', 'procedure_code', 'cost', and 'date_of_service'. "
                "  Mark subsequent identical claims as duplicates. (Consider only exact matches for PoC). "
                "- **High Frequency Provider (Simplified):** If any single 'provider_id' appears more than 3 times in the current batch, "
                "  flag all claims from that provider in this batch. "
                "Add an 'anomaly_flag' (boolean) and 'anomaly_types' (list of strings: 'high_cost', 'duplicate', 'high_frequency_provider') "
                "and 'anomaly_details' (string) to each claim. "
                "Return the updated list of claims."
                f"\n\nMOCK_CPT_CODES: {MOCK_CPT_CODES}"
            ),
            expected_output="A JSON string representing a list of claims, each updated with 'anomaly_flag' (true/false), "
                            "'anomaly_types' (list of strings), and 'anomaly_details' (string) if flagged. "
                            "Example: [{..., 'anomaly_flag': true, 'anomaly_types': ['high_cost', 'duplicate'], 'anomaly_details': 'Cost significantly high; potential duplicate'}, ...]",
            agent=agent,
            context=context, # Takes output from validate_claims
            output_file='anomalous_claims.json'
        )

    def generate_anomaly_explanation(self, agent, context):
        return Task(
            description=(
                "For each claim that has 'anomaly_flag': true, generate a concise, human-readable explanation "
                "for why it was flagged. The explanation should be based on the 'anomaly_types' and 'anomaly_details' fields. "
                "If no claims are flagged, indicate that. "
                "For example: 'Claim CLM001 was flagged because its cost ($1200) for procedure 99285 is significantly higher than the average ($450).' "
                "Add a new field 'anomaly_explanation' to each flagged claim."
                "Return a JSON string representing the list of claims, with explanations added for flagged ones."
            ),
            expected_output="A JSON string representing a list of claims, with 'anomaly_explanation' added to each flagged claim. "
                            "Example: [{..., 'anomaly_flag': true, 'anomaly_explanation': 'Claim CLM001 was flagged for high cost.'}, ...]",
            agent=agent,
            context=context, # Takes output from detect_anomalies
            output_file='explained_anomalies.json'
        )

    def route_claims(self, agent, context):
        return Task(
            description=(
                "Route claims based on their 'validation_status' and 'anomaly_flag'. "
                "Claims with 'validation_status': 'valid' AND 'anomaly_flag': false should be routed to the 'Approved' queue. "
                "All other claims (invalid validation, or anomaly_flagged) should be routed to the 'Audit' queue. "
                "Add a 'routing_destination' field ('Approved' or 'Audit') to each claim. "
                "Return a JSON string representing the list of claims, with their routing destination."
            ),
            expected_output="A JSON string representing a list of claims, each updated with a 'routing_destination' field. "
                            "Example: [{..., 'routing_destination': 'Approved'}, {..., 'routing_destination': 'Audit'}, ...]",
            agent=agent,
            context=context, # Takes output from generate_anomaly_explanation
            output_file='routed_claims.json'
        )

    def summarize_audit_claims(self, agent, context):
        return Task(
            description=(
                "From the routed claims, identify all claims that were routed to the 'Audit' queue. "
                "Aggregate and summarize these claims, grouping them by 'provider_id' and 'anomaly_types'. "
                "For each group, provide a count of claims and list the 'claim_id's. "
                "Include the 'anomaly_explanation' for each specific flagged claim. "
                "If no claims are routed to 'Audit', state that clearly. "
                "Generate a markdown formatted report as the final output, suitable for an auditor."
            ),
            expected_output="A markdown formatted summary report of all claims routed to the 'Audit' queue, "
                            "grouped by provider and anomaly type, with counts and detailed explanations for each flagged claim. "
                            "Example:\n\n# Audit Summary Report\n\n## Provider: PRV001\n- High Cost Anomalies: 2 claims (CLM001, CLM004)\n  - CLM001: Cost significantly higher.\n  - CLM004: Cost significantly higher.\n...",
            agent=agent,
            context=context, # Takes output from route_claims
            output_file='audit_summary.md'
        )