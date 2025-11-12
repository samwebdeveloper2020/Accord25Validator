from docx import Document
def extract_text_from_docx(file):
    file.seek(0)
    from io import BytesIO
    doc = Document(BytesIO(file.read()))
    text = "\n".join([para.text for para in doc.paragraphs])
    file.seek(0)
    return text


from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import json
import openai
import anthropic  # legacy, keep for reference
import os
import json
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from dotenv import load_dotenv





load_dotenv()

app = FastAPI()
from typing import List, Dict, Any, Optional

# Helper to build chat prompt with context
def build_chat_prompt(chat_history: List[Dict[str, str]], agreement=None, accord=None, compliance=None):
    prompt = "You are an expert insurance compliance assistant chatbot.\n"
    if agreement:
        prompt += f"\nEmployee Agreement (JSON):\n{json.dumps(agreement, indent=2)}\n"
    if accord:
        prompt += f"\nCertificate (Accord25) (JSON):\n{json.dumps(accord, indent=2)}\n"
    if compliance:
        prompt += f"\nCompliance Summary:\n{compliance if isinstance(compliance, str) else json.dumps(compliance, indent=2)}\n"
    prompt += "\nChat History (most recent last):\n"
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt += f"{role.title()}: {content}\n"
    prompt += "\nReply as a helpful assistant."
    return prompt
# ...existing code...

# Chatbot endpoint
@app.post("/chat")
async def chat_endpoint(request: Request):
    print("chat endpoint called")
    data = await request.json()
    chat_history = data.get("chat_history", [])
    agreement = data.get("agreement_extracted")
    accord = data.get("accord_extracted")
    compliance = data.get("compliance")
    # Build prompt with context and chat history
    prompt = build_chat_prompt(chat_history, agreement, accord, compliance)
    # Use Claude for chat
    reply = call_claude(prompt)
    return {"reply": reply}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model: str = "claude"
# Load agreement test data from JSON file for testing
agreement_json_path = os.path.join(os.path.dirname(__file__), 'agreement_PeterParker.json')
def load_agreement_test_json():
    with open(agreement_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_text_from_pdf_pymupdf(file):
    file.seek(0)
    pdf_bytes = file.read()
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    file.seek(0)
    return text

def extract_key_value_pairs_from_pdf_form(file):
    file.seek(0)
    pdf_bytes = file.read()
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    form_data = {}
    for page in doc:
        widgets = page.widgets()
        if widgets:
            for field in widgets:
                key = field.field_name
                val = field.field_value
                if key:
                    form_data[key] = val
    file.seek(0)
    return form_data

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_pdf_ocr(file):
    file_bytes = file.read()
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    file.seek(0)
    return text

def call_openai(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key not set."
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# Use custom Claude API integration
from claude_api import call_claude_custom

def call_claude(prompt):
    # Use the custom Claude API integration
    return call_claude_custom(prompt)


def safe_json_parse(text):
    try:
        return json.loads(text)
    except Exception:
        # Try to extract JSON substring if LLM output is not pure JSON
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return json.loads(text[start:end])
        except Exception:
            return None

def check_compliance(agreement_data, accord_data):
    summary = {"compliant": True, "issues": [], "checks": {}}
    if not isinstance(agreement_data, dict) or not isinstance(accord_data, dict):
        summary["compliant"] = False
        summary["issues"].append("Could not parse extracted data as JSON.")
        return summary

    # 1. Insured Name and Holder Name
    insured_agreement = agreement_data.get("insured_name")
    insured_accord = accord_data.get("insured_name")
    holder_agreement = agreement_data.get("holder_name")
    holder_accord = accord_data.get("holder_name")
    if insured_agreement and insured_accord:
        if insured_agreement.strip().lower() == insured_accord.strip().lower():
            summary["checks"]["insured_name"] = "match"
        else:
            summary["compliant"] = False
            summary["checks"]["insured_name"] = "mismatch"
            summary["issues"].append(f"Insured name mismatch: Agreement='{insured_agreement}', Accord25='{insured_accord}'")
    if holder_agreement and holder_accord:
        if holder_agreement.strip().lower() == holder_accord.strip().lower():
            summary["checks"]["holder_name"] = "match"
        else:
            summary["compliant"] = False
            summary["checks"]["holder_name"] = "mismatch"
            summary["issues"].append(f"Holder name mismatch: Agreement='{holder_agreement}', Accord25='{holder_accord}'")

    # 2. Policy Types and Coverages
    required_policies = set(map(str.lower, agreement_data.get("policy_types", [])))
    accord_policies = set(map(str.lower, accord_data.get("policy_types", [])))
    missing_policies = required_policies - accord_policies
    if missing_policies:
        summary["compliant"] = False
        summary["checks"]["policy_types"] = "missing: " + ", ".join(missing_policies)
        summary["issues"].append(f"Missing required policy types in Accord25: {', '.join(missing_policies)}")
    else:
        summary["checks"]["policy_types"] = "all present"

    # 3. Coverage Limits
    required_coverages = agreement_data.get("coverages", {})
    accord_coverages = accord_data.get("coverages", {})
    for cov, req_limit in required_coverages.items():
        acc_limit = accord_coverages.get(cov)
        if acc_limit is None:
            summary["compliant"] = False
            summary["issues"].append(f"Coverage '{cov}' required in agreement but missing in Accord25.")
        elif float(acc_limit) < float(req_limit):
            summary["compliant"] = False
            summary["issues"].append(f"Coverage '{cov}' limit in Accord25 ({acc_limit}) is less than required ({req_limit}).")

    # 4. Dates
    contract_start = agreement_data.get("contract_start_date")
    contract_end = agreement_data.get("contract_end_date")
    policy_start = accord_data.get("policy_start_date")
    policy_end = accord_data.get("policy_end_date")
    if contract_start and policy_start and contract_start < policy_start:
        summary["compliant"] = False
        summary["issues"].append(f"Contract start date {contract_start} is before policy start date {policy_start}.")
    if contract_end and policy_end and contract_end > policy_end:
        summary["compliant"] = False
        summary["issues"].append(f"Contract end date {contract_end} is after policy end date {policy_end}.")

    return summary

def generate_compliance_prompt(agreement_json, accord_json):
    """
    Generate a prompt for an LLM to compare agreement and accord JSONs for insurance compliance.
    """
    # prompt = (
    #     "You are an expert insurance compliance assistant. You will be given two JSON objects:\n\n"
    #     "1. agreement_json: Contains the required insurance information from an employee agreement.\n"
    #     "2. accord_json: Contains the extracted data from an Accord25 certificate.\n\n"
    #     "Important: The attribute (key) names in the two JSONs may not always match exactly. You must use your best judgment and context to map and compare the correct fields (e.g., policy types, coverage limits, dates, names, etc.), even if the keys are different.\n\n"
    #     "Your task is to:\n"
    #     "- Carefully compare all relevant fields between the two JSONs, including but not limited to: policy types, coverages, coverage limits, holder information, named insured information, policy dates, and any other compliance requirements.\n"
    #     "- Pay special attention to differences in attribute names and match the information based on meaning, not just key names.\n"
    # "- Provide a detailed comparison for the following:\n"
    # "    * Policy Types: List which required policy types from the agreement are missing or mismatched in the Accord25.\n"
    # "    * Policy Dates: Identify any policy dates in the Accord25 that do not fully cover the contract dates in the agreement.\n"
    # "    * Coverages and Limits: For each required coverage in the agreement, compare the corresponding coverage and limit in the Accord25. For each coverage type, provide a value-by-value comparison limit(s) in the agreement and the actual limit(s) in the certificate. Clearly state which coverages and limits are different, missing, or insufficient, and summarize the differences for each coverage in the policies.\n"
    #     "- Identify and clearly list any discrepancies, missing information, or mismatches.\n"
    #     "- Provide a concise summary stating whether the Accord25 certificate is in compliance with the agreement, and highlight any issues found.\n\n"
    #     "Here are the JSONs:\n\n"
    #     "agreement_json:\n"
    #     f"{json.dumps(agreement_json, indent=2)}\n\n"
    #     "accord_json:\n"
    #     f"{json.dumps(accord_json, indent=2)}\n\n"
    #     "Please return your answer as a well-structured summary, including:\n"
    # "- A detailed comparison table or list for Named insured, Holder information, Policy types(LOB), dates, and for each coverage and Limit(s) under a policy, a value-by-value comparison of coverages and limits that are different, missing or insufficient, and other relevant details with their discrepancies.\n"
    #     "- A list of any discrepancies or compliance issues found.\n"
    #     "- A final summary statement on overall compliance."
    #     "Highlight the issues and compliance gaps clearly with red color."
    #     "In the summary, mention or title agreement_json as 'Employee Agreement' and accord_json as 'Certificate'.\n"
    #     "Highlight the headers in bold."
    # )


    prompt_detail = (
       f"""You are an expert insurance compliance analyst specializing in ACORD25 form verification.
        You will be given two JSON objects:
        1. agreement_json – Contains the required insurance requirements as per the Employee Agreement.
        2. accord_json – Contains the actual insurance coverage details extracted from the ACORD25 certificate.

        Here are the JSONs:
        agreement_json:
        {json.dumps(agreement_json, indent=2)}
        accord_json:
        {json.dumps(accord_json, indent=2)}

        Your Objectives
        You must perform a detailed, field-by-field compliance comparison between the two JSONs and produce a structured compliance report.
        Attribute names (keys) between the two JSONs may differ — your job is to intelligently map fields by meaning and context (not just key names).
        For example, “General Liability” in the agreement may appear as “Commercial General Liability” or “CGL” in the certificate — treat them as equivalent where contextually correct.

        Comparison Requirements
        1. Named Insured and Certificate Holder
        Compare Named Insured details: names, addresses, and entity types.
        Compare Certificate Holder information: names, addresses, and holder references.
        Highlight discrepancies (e.g., name mismatches, missing address components, incomplete holder details).

        2. Policy Types (Lines of Business / LOBs)
        Identify and list all required policy types from the Employee Agreement (e.g., General Liability, Automobile Liability, Umbrella, Workers Compensation, Professional Liability).
        Match each policy type with the corresponding entry in the ACORD25 Certificate.
        Clearly list:
        ✅ Policies that are present and matched
        ❌ Policies that are missing or mismatched

        3. Policy Dates
        For each matched policy, compare Effective Dates and Expiration Dates.
        Verify whether the policy fully covers the contract period required in the Employee Agreement.
        Flag any gaps (e.g., coverage starts after or ends before contract term).

        4. Coverages and Limits
        For each policy type, generate a detailed comparison table with a row for every required coverage and limit. The table must include:
        - Policy Type
        - Coverage Name
        - Agreement Limit(s)
        - Certificate Limit(s)
        - Status (Compliant/Non-Compliant)
        - Remarks / Discrepancy

        For every required coverage in the Employee Agreement, compare with the corresponding coverage in the certificate. If a coverage or limit is missing, lower than required, ambiguous, or named differently but equivalent, clearly indicate this in the table. There must be a row for every coverage and limit under each policy type, even if missing in the certificate.

        5. Other Relevant Fields
        Compare any additional applicable sections, such as:
        - Waiver of Subrogation
        - Additional Insured status
        - Policy Number format
        - Insurer names and AM Best ratings (if available)
        - Description of Operations or special endorsements

        ⚠️ Discrepancies and Compliance Issues
        List all discrepancies in a clear, itemized format:
        - Missing or mismatched policy types
        - Insufficient coverage limits
        - Coverage dates not aligned with agreement
        - Named insured or holder mismatches
        - Missing required endorsements or clauses
        Each discrepancy should be marked with a red highlight (🟥 or <span style="color:red">red text</span> in markdown/HTML).

        ✅ Final Summary
        At the end of your analysis, provide a concise compliance summary stating:
        - Whether the Certificate (ACORD25) meets all insurance requirements from the Employee Agreement.
        - Explicitly mention if the certificate is: Fully Compliant, Partially Compliant, or Non-Compliant, and list key reasons.

        🧩 Formatting and Output
        - Use bold headers for major sections.
        - Use tables for comparisons (policy types, coverages, limits, dates).
        - For each policy type, include a table with a row for every coverage and limit.
        - Use color highlights (red for gaps, green for compliance) to clearly distinguish compliant vs. non-compliant items.
        - Ensure your output is readable, professional, and structured like a compliance report.

        🧠 Example Emphasis for Value-by-Value Comparison
        When comparing coverages, ensure every numeric and textual value is checked:
        If the Agreement says "Each Occurrence": "$1,000,000"
        and Certificate says "Each Occurrence": "$500,000",
        show:
        Mismatch: Agreement requires $1,000,000; Certificate provides $500,000.
        Do this for all coverage limits under each policy, and ensure every required coverage/limit is represented as a row in the table, even if missing in the certificate.
        """

    )
    return prompt_detail

def call_LLM(prompt):
    if model == "claude":
        print("Using Claude model for extraction.")
        response_text = call_claude(prompt)
    else:
        response_text = call_openai(prompt)
    return response_text

def check_compliance_LLM(agreement_data, accord_data):
    
    prompt = generate_compliance_prompt(agreement_data, accord_data)
    response_text = call_LLM(prompt)
    # if model == "claude":
    #     print("Using Claude model for extraction.")
    #     response_text = call_claude(prompt)
    # else:
    #     response_text = call_openai(prompt)
    return response_text

@app.post("/upload")
async def upload_files(
    agreement: UploadFile = File(...),
    accord: UploadFile = File(...),
    model2: str = Form("claude")
):
    # Extract agreement text (support PDF and DOCX)
    agreement_text = ""
    if agreement.filename.lower().endswith(".pdf"):
        agreement_text = extract_text_from_pdf(agreement.file)
    elif agreement.filename.lower().endswith(".docx"):
        agreement_text = extract_text_from_docx(agreement.file)
    else:
        agreement_text = ""  # Or raise error/return message for unsupported format
      
    #print("Agreement text extracted:", agreement_text)
    # Extract Accord25 text using PyMuPDF (fitz), fallback to OCR if needed
    accord_text = ""#extract_text_from_pdf_pymupdf(accord.file)
    accord_form_data_json = extract_key_value_pairs_from_pdf_form(accord.file)
    #print("Accord25 text extracted (PyMuPDF):", accord_text)
    #print(type(accord_form_data_json))
    #print("Accord25 form data extracted:", accord_form_data_json)
    # if len(accord_text.strip()) < 100:
    #     accord.file.seek(0)
    #     accord_text = extract_text_from_pdf_ocr(accord.file)
    #     print("Accord25 text extracted (OCR fallback):", accord_text)

    prompt_agreement = (
        "You are an expert insurance compliance assistant. Carefully read the following Employee Agreement and extract ALL relevant information that could be used to verify insurance compliance. "
        "Return your answer as a well-formatted JSON object with as many fields as possible. "
        "Include (if present): insured_name, holder_name, contract_start_date, contract_end_date, policy_types (list), coverages (object with coverage type and required limit), insurance requirements, additional requirements, endorsements, waiver of subrogation, policy numbers, and any other relevant details. "
        "If a field is not found, use null or an empty value.\n\nEmployee Agreement Document:\n" + agreement_text
    )
    # prompt_accord = (
    #     "You are an expert insurance compliance assistant. Carefully read the following Accord25 Certificate and extract ALL relevant information including policy information, effective dates, coverages and limits, holder information, insured Names, descriptio of operations, and other information that could be used to verify insurance compliance. "
    #     "Return your answer as a well-formatted JSON object with as many fields as possible. \n" + accord_text
    # )
    agreement_result = call_LLM(prompt_agreement)

    # if model == "claude":
    #     print("Using Claude model for extraction.")
    #     agreement_result = call_claude(prompt_agreement)
    #     # accord_result = call_claude(prompt_accord)
    # else:
    #     agreement_result = "{}" #call_openai(prompt_agreement)
    #     # accord_result = "{}" #call_openai(prompt_accord)
    #     # print("Accord25 text extracted:", accord_result)

    #agreement_data = load_agreement_test_json()
    agreement_data = safe_json_parse(agreement_result)
   
    # print("agreement data :", agreement_data)
    accord_form_data_json_str = json.dumps(accord_form_data_json, indent=4)
    accord_data = safe_json_parse(accord_form_data_json_str)
    # compliance = check_compliance(agreement_data, accord_data)
    # print(compliance)

    compliance_str = """
    **Named Insured and Certificate Holder Comparison:**

    - Named Insured:
    - **Agreement (Employee Agreement): Peter Parker**
    - **Certificate (ACORD25): Peter Parker**
    - **Status: Fully Compliant**

    - Certificate Holder:
    - **Agreement (Employee Agreement): The Daily Bugle**
    - **Certificate (ACORD25): The Daily Bugle**
    - **Status: Fully Compliant**

    ---

    **Policy Types Comparison:**

    - Required Policy Types from Agreement:
    1. Commercial General Liability
    2. Automobile Liability
    3. Workers' Compensation and Employers Liability
    4. Umbrella/Excess Liability
    5. Cyber Liability

    - Matched Policies in Certificate:
    1. Commercial General Liability
    2. Automobile Liability
    3. Workers' Compensation and Employers Liability
    4. Umbrella/Excess Liability
    5. Cyber Liability

    **Status**: All required policy types are present and matched.

    ---

    **Policy Dates Comparison:**

    - Effective Dates and Expiration Dates Comparison:
    1. Commercial General Liability: Effective from 10/01/2025 to 10/02/2026 (Compliant)
    2. Automobile Liability: Effective from 10/01/2025 to 10/02/2026 (Compliant)
    3. Workers' Compensation: Effective dates missing (Non-Compliant)
    4. Umbrella/Excess Liability: Effective from 10/01/2025 to 10/02/2026 (Compliant)
    5. Cyber Liability: Effective from 10/01/2025 to 10/02/2026 (Compliant)

    ---

    **Coverages and Limits Comparison:**

    | Policy Type | Coverage Name | Agreement Limit | Certificate Limit | Status | Remarks |
    |-------------|---------------|-----------------|-------------------|--------|---------|
    | Commercial General Liability | Bodily Injury | $1,000,000 per occurrence | $200,000 | Non-Compliant | Limit Insufficient |
    | Commercial General Liability | Property Damage | $1,000,000 per occurrence | N/A | Non-Compliant | Missing Coverage |
    | Commercial General Liability | General Aggregate | $2,000,000 | $1,000,000 | Non-Compliant | Limit Insufficient |
    | Automobile Liability | Bodily Injury & Property Damage | $1,000,000 combined single limit | N/A | Non-Compliant | Missing Coverage |
    | Workers' Compensation | Workers' Compensation | Statutory limits per New York law | N/A | Non-Compliant | Effective Dates Missing |
    | Umbrella/Excess Liability | Limit | $2,000,000 per occurrence | $100,000 | Non-Compliant | Limit Insufficient |
    | Cyber Liability | Data Breach Response | $500,000 per incident | $2,000,000 | Non-Compliant | Limit Exceeds Requirement |

    ---

    **Other Relevant Fields Comparison:**

    - Waiver of Subrogation:
    - **Agreement (Employee Agreement): Included**
    - **Certificate (ACORD25): Included**
    - **Status: Fully Compliant**

    - Additional Insured:
    - **Agreement (Employee Agreement): The Daily Bugle**
    - **Certificate (ACORD25): The Daily Bugle (per CG 20 10 endorsement)**
    - **Status: Compliant**

    - Policy Number Format:
    - **Agreement (Employee Agreement): Not specified**
    - **Certificate (ACORD25): POLICY_12345**
    - **Status: Non-Compliant**

    ---

    **Compliance Summary:**

    Based on the detailed comparison, the ACORD25 Certificate partially meets the insurance requirements from the Employee Agreement. The certificate is non-compliant in areas such as coverage limits, missing coverages, and insufficient policy dates. It is recommended to address the discrepancies and provide an updated certificate for full compliance.

    ---

    This structured compliance report provides a comprehensive analysis of the ACORD25 Certificate against the insurance requirements outlined in the Employee Agreement. Each section is meticulously reviewed to identify compliance status and discrepancies."""

    #compliance = compliance_str #check_compliance_LLM(agreement_data, accord_data)
    compliance = check_compliance_LLM(agreement_data, accord_data)
    #print("Compliance result:", compliance)

    return JSONResponse({
        "model": model,
        "agreement_extracted": agreement_data,
        "accord_extracted": accord_data,
        "compliance": compliance
    })
