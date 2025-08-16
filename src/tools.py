import json
from datetime import datetime
import pandas as pd

class ClaimTools:
    _MOCK_CPT_CODES = {"99285", "99213", "81002"}
    _MOCK_ICD_CODES = {"M54.5", "J06.9", "I10"}
    _MOCK_MEMBERS = {"MBR001": {"eligible": True}, "MBR002": {"eligible": True}, "MBR003": {"eligible": False, "reason": "Inactive policy"}}
    _MOCK_AVERAGE_COSTS = {"99285": 500, "99213": 100, "81002": 50}
    _MOCK_CLAIMS_DB = []

    @staticmethod
    def read_claims_data(claims_json_string: str) -> list:
        try:
            claims = json.loads(claims_json_string)
            print(f"Tool: Successfully read {len(claims)} claims from input string.")
            return claims
        except json.JSONDecodeError as e:
            print(f"Tool: Error decoding JSON: {e}")
            return []

    @staticmethod
    def categorize_claim(claim: dict) -> str:
        claim_type = claim.get('claim_type', 'unknown').lower()
        if claim_type in ['outpatient', 'inpatient', 'pharmacy']:
            return claim_type
        return 'other'

    @staticmethod
    def validate_procedure_code(code: str) -> bool:
        is_valid = code in ClaimTools._MOCK_CPT_CODES
        print(f"Tool: Validating procedure code '{code}': {is_valid}")
        return is_valid

    @staticmethod
    def validate_diagnosis_code(code: str) -> bool:
        is_valid = code in ClaimTools._MOCK_ICD_CODES
        print(f"Tool: Validating diagnosis code '{code}': {is_valid}")
        return is_valid

    @staticmethod
    def check_member_eligibility(member_id: str) -> dict:
        member_info = ClaimTools._MOCK_MEMBERS.get(member_id, {"eligible": False, "reason": "Member ID not found"})
        print(f"Tool: Checking eligibility for member '{member_id}': {member_info['eligible']}")
        return member_info

    @staticmethod
    def get_average_cost_for_procedure(procedure_code: str) -> float:
        avg_cost = ClaimTools._MOCK_AVERAGE_COSTS.get(procedure_code, 0.0)
        print(f"Tool: Average cost for '{procedure_code}': ${avg_cost}")
        return avg_cost

    @staticmethod
    def record_claim_for_duplicate_check(claim_data: dict):
        ClaimTools._MOCK_CLAIMS_DB.append({
            'claim_id': claim_data['claim_id'],
            'member_id': claim_data['member_id'],
            'provider_id': claim_data['provider_id'],
            'procedure_code': claim_data['procedure_code'],
            'date_of_service': claim_data['date_of_service']
        })
        print(f"Tool: Claim '{claim_data['claim_id']}' recorded for duplicate check. Current DB size: {len(ClaimTools._MOCK_CLAIMS_DB)}")

    @staticmethod
    def check_for_duplicate_claim(current_claim: dict) -> bool:
        for existing_claim in ClaimTools._MOCK_CLAIMS_DB:
            if existing_claim['claim_id'] == current_claim['claim_id']:
                continue
            if (existing_claim['member_id'] == current_claim['member_id'] and
                existing_claim['provider_id'] == current_claim['provider_id'] and
                existing_claim['procedure_code'] == current_claim['procedure_code']):
                try:
                    date1 = datetime.strptime(existing_claim['date_of_service'], '%Y-%m-%d')
                    date2 = datetime.strptime(current_claim['date_of_service'], '%Y-%m-%d')
                    if abs((date2 - date1).days) <= 3:
                        print(f"Tool: Duplicate detected: {current_claim['claim_id']} is similar to {existing_claim['claim_id']}.")
                        return True
                except ValueError:
                    print(f"Tool: Date parsing error for duplicate check for claim {current_claim['claim_id']}.")
                    continue
        print(f"Tool: No duplicate found for claim '{current_claim['claim_id']}'.")
        return False

    @staticmethod
    def get_provider_claim_frequency(provider_id: str) -> int:
        count = sum(1 for claim in ClaimTools._MOCK_CLAIMS_DB if claim['provider_id'] == provider_id)
        print(f"Tool: Provider '{provider_id}' has submitted {count} claims.")
        return count

    @staticmethod
    def save_claim_to_approved_queue(claim: dict):
        print(f"\n--- APPROVED CLAIM: {claim['claim_id']} ---\n")

    @staticmethod
    def save_claim_to_audit_queue(claim: dict):
        print(f"\n--- FLAGGED FOR AUDIT: {claim['claim_id']} --- Reason(s): {claim.get('anomaly_reason', 'N/A')} ---\n")

    @staticmethod
    def generate_audit_report(flagged_claims: list) -> str:
        if not flagged_claims:
            return "No claims were flagged for audit."
        report_summary = "# Audit Summary Report\n\n"
        provider_grouping = {}
        anomaly_type_counts = {}
        for claim in flagged_claims:
            provider_id = claim.get('provider_id', 'Unknown Provider')
            anomaly_reason = claim.get('anomaly_reason', 'General Anomaly').replace('_', ' ').title()
            if provider_id not in provider_grouping:
                provider_grouping[provider_id] = []
            provider_grouping[provider_id].append(claim)
            anomaly_type_counts[anomaly_reason] = anomaly_type_counts.get(anomaly_reason, 0) + 1
        report_summary += "## Grouped by Provider\n"
        for provider, claims in provider_grouping.items():
            report_summary += f"### Provider ID: {provider}\n"
            for claim in claims:
                report_summary += (f"- Claim ID: `{claim['claim_id']}`\n"
                                   f"  - Cost: ${claim.get('cost', 'N/A')}\n"
                                   f"  - Reason: {claim.get('anomaly_reason', 'N/A').replace('_', ' ').title()}\n"
                                   f"  - Explanation: {claim.get('anomaly_explanation', 'N/A')}\n")
            report_summary += "\n"
        report_summary += "## Anomaly Type Summary\n"
        for anomaly_type, count in anomaly_type_counts.items():
            report_summary += f"- **{anomaly_type}**: {count} claims\n"
        return report_summary
