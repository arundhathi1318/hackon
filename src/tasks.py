from crewai import Task
from crewai import Agent

class ClaimTasks:
    def __init__(self, agents: Agent):
        self.agents = agents

    def intake_claims(self, claims_json_string: str):
        return Task(
            description=(
                "Your task is to take the provided raw JSON string of claims data. "
                "Use the `ReadClaimsTool` to parse this string into a list of claim dictionaries. "
                "For each parsed claim, use the `CategorizeClaimTool` to assign a 'category'. "
                "Examine each claim for the presence of all essential fields: "
                "'claim_id', 'member_id', 'provider_id', 'procedure_code', 'diagnosis_code', 'cost', 'date_of_service', 'claim_type'. "
                "If any of these fields are missing, set 'initial_status' to 'needs_review_missing_fields' and add a 'reason'. "
                "Otherwise, set 'initial_status' to 'parsed'. "
                f"The input JSON string is: {claims_json_string}"
            ),
            expected_output=(
                "A JSON string representing a list of dictionaries, where each dictionary is a parsed claim. "
                "Each claim dict must include all original fields plus a 'category' field and an 'initial_status' field "
                "('parsed' or 'needs_review_missing_fields') and a 'reason' field if missing fields."
            ),
            agent=self.agents.claim_intake_agent(),
            output_file='intake_output.json'
        )

    def validate_claims(self, context: list):
        return Task(
            description=(
                "Process the list of structured claims. "
                "For each claim, if 'initial_status' is 'parsed': "
                "1. Validate 'procedure_code'. "
                "2. Validate 'diagnosis_code'. "
                "3. Check 'member_id' eligibility. "
                "4. If all checks pass, set 'validation_status' to 'valid'. "
                "If 'initial_status' was 'needs_review_missing_fields', set 'validation_status' to 'invalid_missing_fields'. "
                "Combine all validation reasons if multiple issues exist."
            ),
            expected_output=(
                "A JSON string representing a list of claim dictionaries, each updated with a 'validation_status' "
                "('valid', 'invalid_procedure_code', 'invalid_diagnosis_code', 'ineligible_member', 'invalid_missing_fields') "
                "and an optional 'validation_reason'."
            ),
            context=context,
            agent=self.agents.validation_agent(),
            output_file='validation_output.json'
        )

    def detect_anomalies(self, context: list):
        return Task(
            description=(
                "Analyze the validated claims. For each claim with 'validation_status' = 'valid': "
                "1. Record the claim. "
                "2. Compare 'cost' with the average for its 'procedure_code'. Flag if 3x higher. "
                "3. Check for duplicates. "
                "4. Check provider frequency. "
                "If multiple anomalies, list all reasons and assign the highest score. "
                "Invalid claims should have 'anomaly_score': 0 and 'anomaly_reason': 'not_applicable'."
            ),
            expected_output=(
                "A JSON string representing a list of claim dictionaries, each updated with 'anomaly_score' (0-100) "
                "and 'anomaly_reason'."
            ),
            context=context,
            agent=self.agents.anomaly_detection_agent(),
            output_file='anomaly_output.json'
        )

    def generate_explanations(self, context: list):
        return Task(
            description=(
                "For each claim, if 'anomaly_score' > 0 and 'anomaly_reason' is not 'none' or 'not_applicable', "
                "generate a clear explanation based on claim details. "
                "Add this as 'anomaly_explanation'. "
                "If no anomaly, set 'anomaly_explanation' to 'N/A'."
            ),
            expected_output=(
                "A JSON string representing a list of claim dictionaries, each updated with 'anomaly_explanation'."
            ),
            context=context,
            agent=self.agents.llm_explanation_agent(),
            output_file='explanation_output.json'
        )

    def route_claims(self, context: list):
        return Task(
            description=(
                "Based on 'validation_status' and 'anomaly_score', route claims. "
                "If 'validation_status' is 'valid' and 'anomaly_score' = 0, send to 'approved' queue. "
                "Otherwise, send to 'audit'. "
                "Update each claim with 'final_routing'."
            ),
            expected_output=(
                "A JSON string representing a list of claim dictionaries, each updated with 'final_routing'."
            ),
            context=context,
            agent=self.agents.routing_agent(),
            output_file='routing_output.json'
        )

    def summarize_audit(self, context: list):
        return Task(
            description=(
                "Filter claims with 'final_routing' = 'audit'. "
                "Use the tool to generate a comprehensive audit report in markdown, grouped by provider and anomaly type."
            ),
            expected_output=(
                "A markdown string with a detailed audit summary. If no claims were routed to audit, output 'No claims were flagged for audit'."
            ),
            context=context,
            agent=self.agents.audit_summary_agent(),
            output_file='audit_summary.md'
        )
