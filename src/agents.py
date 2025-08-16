import os
from crewai import Agent
from crewai_tools import Tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from tools import ClaimTools

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    temperature=0.0
)

read_claims_tool = Tool(
    name="ReadClaimsTool",
    func=ClaimTools.read_claims_data,
    description="Reads and parses claim data from a JSON string input, returning a list of dictionaries."
)

categorize_claim_tool = Tool(
    name="CategorizeClaimTool",
    func=ClaimTools.categorize_claim,
    description="Categorizes a single claim (e.g., outpatient, inpatient, pharmacy)."
)

validate_procedure_code_tool = Tool(
    name="ValidateProcedureCodeTool",
    func=ClaimTools.validate_procedure_code,
    description="Validates a CPT procedure code against a mock reference list. Returns True or False."
)

validate_diagnosis_code_tool = Tool(
    name="ValidateDiagnosisCodeTool",
    func=ClaimTools.validate_diagnosis_code,
    description="Validates an ICD diagnosis code against a mock reference list. Returns True or False."
)

check_member_eligibility_tool = Tool(
    name="CheckMemberEligibilityTool",
    func=ClaimTools.check_member_eligibility,
    description="Checks a member's eligibility against mock data. Returns a dict {'eligible': bool, 'reason': str}."
)

get_average_cost_tool = Tool(
    name="GetAverageCostTool",
    func=ClaimTools.get_average_cost_for_procedure,
    description="Retrieves the average cost for a given procedure code from mock data. Returns a float."
)

record_claim_for_duplicate_tool = Tool(
    name="RecordClaimForDuplicateTool",
    func=ClaimTools.record_claim_for_duplicate_check,
    description="Records a claim's essential details for future duplicate checking within the current run."
)

check_for_duplicate_tool = Tool(
    name="CheckForDuplicateTool",
    func=ClaimTools.check_for_duplicate_claim,
    description="Checks if a claim is a duplicate based on member, provider, and procedure within a short timeframe (3 days). Returns True or False."
)

get_provider_claim_frequency_tool = Tool(
    name="GetProviderClaimFrequencyTool",
    func=ClaimTools.get_provider_claim_frequency,
    description="Retrieves the mock claim frequency for a given provider from claims processed so far. Returns an integer count."
)

save_to_approved_queue_tool = Tool(
    name="SaveToApprovedQueueTool",
    func=ClaimTools.save_claim_to_approved_queue,
    description="Saves a valid claim to a mock 'approved' queue. Prints confirmation."
)

save_to_audit_queue_tool = Tool(
    name="SaveToAuditQueueTool",
    func=ClaimTools.save_claim_to_audit_queue,
    description="Saves a flagged claim to a mock 'audit' queue. Prints confirmation."
)

generate_audit_report_tool = Tool(
    name="GenerateAuditReportTool",
    func=ClaimTools.generate_audit_report,
    description="Generates a comprehensive summary report of flagged claims for audit in markdown format. Takes a list of flagged claim dictionaries."
)

class ClaimAgents:
    def __init__(self):
        self.llm = llm

    def claim_intake_agent(self):
        return Agent(
            role="Claim Intake Agent",
            goal="Load and parse JSON claims, then categorize them for further processing.",
            backstory="You are an expert in handling healthcare claim data, responsible for ingesting raw JSON claim files and preparing them for validation.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[read_claims_tool, categorize_claim_tool]
        )

    def validation_agent(self):
        return Agent(
            role="Claim Validation Agent",
            goal="Validate claim fields for completeness and correctness, and simulate member eligibility.",
            backstory="You rigorously check each claim for missing fields, validate medical codes, and confirm member eligibility.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[validate_procedure_code_tool, validate_diagnosis_code_tool, check_member_eligibility_tool]
        )

    def anomaly_detection_agent(self):
        return Agent(
            role="Anomaly Detection Agent",
            goal="Identify suspicious or anomalous claims based on cost, duplicates, and provider behavior.",
            backstory="You analyze claim data to spot unusual patterns such as inflated costs, duplicate submissions, or high provider claim frequencies.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[get_average_cost_tool, record_claim_for_duplicate_tool, check_for_duplicate_tool, get_provider_claim_frequency_tool]
        )

    def llm_explanation_agent(self):
        return Agent(
            role="LLM-Powered Explanation Agent",
            goal="Generate clear, natural language explanations for flagged anomalous claims.",
            backstory="You translate complex anomaly detection findings into understandable explanations for auditors.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def routing_agent(self):
        return Agent(
            role="Claim Routing Agent",
            goal="Route claims to the appropriate queues (approved or audit) based on their validation and anomaly status.",
            backstory="You ensure each claim goes to the correct destination: approved for payout or audit for further investigation.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[save_to_approved_queue_tool, save_to_audit_queue_tool]
        )

    def audit_summary_agent(self):
        return Agent(
            role="Audit Summary Agent",
            goal="Aggregate flagged claims and generate comprehensive summary reports for compliance and auditing.",
            backstory="You compile detailed summaries of all claims flagged for audit, categorizing them by type, provider, or severity.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[generate_audit_report_tool]
        )
