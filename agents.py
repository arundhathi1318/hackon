# agents.py
import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=openai_api_key) # gpt-4o-mini is cost-effective

class ClaimsAgents:
    def __init__(self):
        self.llm = llm

    def intake_agent(self):
        return Agent(
            role='Intake Agent',
            goal='Parse and categorize raw healthcare claims data from JSON format.',
            backstory=(
                "You are responsible for the initial processing of healthcare claims. "
                "Your task is to accurately read and categorize each claim, ensuring all essential "
                "fields are identified for downstream processing. You are meticulous and precise."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def validation_agent(self):
        return Agent(
            role='Validation Agent',
            goal='Validate the completeness, correctness, and eligibility of healthcare claims.',
            backstory=(
                "You are a meticulous claims validator. Your primary responsibility is to "
                "ensure that all claim data (CPT/ICD codes, member eligibility) is accurate and complete "
                "according to established rules and mock reference data. You identify any discrepancies."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def anomaly_detection_agent(self):
        return Agent(
            role='Anomaly Detection Agent',
            goal='Identify and flag suspicious or anomalous patterns in healthcare claims.',
            backstory=(
                "You are an expert in fraud and anomaly detection. You analyze claim data "
                "for unusual costs, duplicate submissions, and abnormal provider behavior. "
                "Your keen eye helps flag potential issues for further investigation."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def llm_explanation_agent(self):
        return Agent(
            role='LLM Explanation Agent',
            goal='Generate clear, human-readable justifications for detected claim anomalies.',
            backstory=(
                "You are a skilled communicator specializing in translating complex anomaly "
                "flags into understandable explanations. Your goal is to provide concise and "
                "actionable reasons for why a claim was flagged, aiding auditors."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def routing_agent(self):
        return Agent(
            role='Routing Agent',
            goal='Direct processed claims to the appropriate downstream queues (approved or audit).',
            backstory=(
                "You are the claims traffic controller. Based on validation and anomaly "
                "statuses, you efficiently route each claim to its correct destination, "
                "ensuring a smooth flow through the system."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def audit_summary_agent(self):
        return Agent(
            role='Audit Summary Agent',
            goal='Aggregate flagged claims and generate a comprehensive summary report for auditors.',
            backstory=(
                "You are an analytical reporting specialist. Your job is to compile all "
                "flagged claims, group them by relevant criteria, and produce a clear, "
                "actionable summary that highlights key issues for the audit team."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )