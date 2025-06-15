"""
Filename: invoice_processing.py
Author: Ashish Sharma
Date created: 15/06/2025
License: MIT License
Description: This file contains invoice processing related functions.
"""
from fastapi import UploadFile
from utils.logs import logger
from config.config import upload_directory_path
from utils.general import get_file_type,extract_text_based_on_file_type, clean_currency
from datetime import date
import json
import shutil
from pathlib import Path
from config.config import gemini_model_name, upload_directory_path
import google.generativeai as genai # 👈 Add this import

# Define the prompts for invoice and bill separately
def fetch_invoice_details(text):
    prompt = f'''
    You are an advanced data extraction system specialized in parsing invoice documents. Your task is to extract specific details from the provided text and output them in a structured JSON format. The details to extract include:
    
    - invoice_number: The unique number identifying the invoice.
    - invoice_date: The date the invoice was issued.
    - invoice_due_date: The date or number of days by which the payment should be made. If the due_date is given in number of days, add those many days to the invoice_date and get the new calendar due_date. For example if the invoice date is 03/10/2024 and the due days/date is 15 days the new calendar due date will be 03/15/2024.
    - invoice_to: The entity/company to which the invoice is addressed or in other words the entity which will pay.
    - contact_number: The contact number of the company to which the invoice is raised.
    - email: The email of the company to which the invoice is raised.
    - invoice_subtotal_due: Sub total due of all the line items before tax.
    - invoice_tax_due: Total tax amount due specifiend in the invoice text which is levied on Sub total.
    - invoice_total_due: Total amount due including tax and subtotal.
    - line_items: Invoice items containing item description, hrs or quantity, rate or cost and line total.

    Context/Text:
    {text}

    ***Important:***
    - If the due_date is given in number of days, add those many days to the invoice_date and get the new calendar due_date. For example if the invoice date is 03/10/2024 and the due days/date is 15 days the new calendar due date will be 03/15/2024.
    - Only use information directly from the text given in context above. Do not infer or hallucinate values.
    - Double check for the invoice line items and ensure that you are not missing any of it.

    ***Instructions:***
    - Carefully read through the provided text to locate the required details.
    - Ensure that the JSON output adheres to the specified format.
    - If a field is not found, return 'NA' for that field.

    ***Tax:***
    - Tax amount can't be less than $0.00. It has to have have some value equal to or greater than zero while less than sub total.

    Example output when all fields are available:
    {{
        "invoice_number": "INV123456",
        "invoice_date": "19/08/2005",
        "invoice_due_date": "19/09/2005",
        "invoice_to": "ABC Corp",
        "contact_number": "7899877890",
        "email": "abc@example.com",
        "invoice_subtotal_due": "$1,800.00",
        "invoice_tax_due": "$180.00",
        "invoice_total_due": "$1,980.00",
        "line_items": {
          {
            "description": "Foundation Labor",
            "hrs_or_quantity": "10",
            "rate_or_cost": "50",
            "line_total": "500"
          },
          {
            "description": "PCC",
            "hrs_or_quantity": "15",
            "rate_or_cost": "78.00",
            "line_total": "1,170.00"
          }
        }
    }}

    Example output when some fields are missing:
    {{
        "invoice_number": "INV123456",
        "invoice_date": "19/08/2005",
        "invoice_due_date": "NA",
        "invoice_to": "NA",
        "contact_number": "NA",
        "email": "abc@example.com",
        "invoice_subtotal_due": "$1,800.00",
        "invoice_tax_due": "$180.00",
        "invoice_total_due": "$1,980.00",
        "line_items": {
          {
            "description": "Foundation Labor",
            "hrs_or_quantity": "10",
            "rate_or_cost": "50",
            "line_total": "500"
          },
          {
            "description": "PCC",
            "hrs_or_quantity": "15",
            "rate_or_cost": "78.00",
            "line_total": "1,170.00"
          }
        }
    }}

    Now, please provide the extracted details in JSON format. Do not miss any field in the JSON, if any value is not available, return 'NA' for that.
    '''

     # --- Gemini API Call ---
    model = genai.GenerativeModel(gemini_model_name)
    response = model.generate_content(prompt)
    # --- End of Change ---

    logger.info("======invoice details========")
    
    # The Gemini response text is in response.text
    # We need to clean it up to ensure it's valid JSON
    cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
    logger.info(cleaned_response)
    
    invoice_details = json.loads(cleaned_response)
    return invoice_details

def verify_invoice_details(details):
    prompt = f'''
    As an advanced verification system, you are tasked with verifying the correctness of the invoice details by performing mathematical checks:

    - Calculate if the sub_total plus tax equals the total.
    - Calculate if the total minus amount_paid equals the total_due.

    Given Invoice Details:
    sub_total: {details['sub_total']}
    tax: {details['tax']}
    total: {details['total']}
    amount_paid: {details['amount_paid']}
    total_due: {details['total_due']}

    if (sub_total + tax) == total and (total - amount_paid) == total_due: 
        verification_result = True
    else:
        verification_result = False

    Instructions:
    - Perform the required verifications.
    - Return the results of the verifications in a structured JSON format.
    - If any amount/price/money field have missing values, assume '$0.00' for that field.
    - Include the details of the calculations that you will do on the above given invoice details in the response.
    - Always give amount fields with the precision of 2 decimal places e.g. 102.20

    Response fromat:
    {{
        "verification": verification
        
    }}

    Example output when 'verification_result' is equal to 'True':
    {{
        "verification": True
    }}

    Example output when 'verification_result' is equal to 'False':
    {{
        "verification": False
    }}

    Now, please provide the extracted details in JSON format. Do not miss any field in the JSON, if any value is not available, return 'NA' for that.
    '''

    # --- Gemini API Call ---
    model = genai.GenerativeModel(gemini_model_name)
    response = model.generate_content(prompt)
    # --- End of Change ---
    
    logger.info("======bill details========")
    
    cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
    logger.info(cleaned_response)
    
    reconciliation_data = json.loads(cleaned_response)
    return reconciliation_data

def fetch_bill_details(text):
    prompt = f'''
    You are an advanced data extraction system specialized in parsing a bill or list of bill documents. Your task is to extract specific details from the provided text and output them in a structured JSON format. The details to extract include:

    - bill_number: The unique number identifying the bill. Please note that, bill number is different than invoice number, pick bill number only.
    - bill_date: The date the bill was issued.
    - bill_payment_date: The date on which the payment was done.
    - bill_paid_by: The amount paid by which person or company.
    - bill_subtotal_paid: Total amount before tax.
    - bill_tax_paid: Tax amount.
    - bill_total_paid: Total amount including tax.
    - line_items: Bill items containing item description, amount.

    Context/Text:
    {text}

    **Important:** Only use information directly from the text given in context above. Do not infer or hallucinate values.

    Instructions:
    - Carefully read through the provided text to locate the required details.
    - Ensure that the JSON output adheres to the specified format.
    - If a field is not found, return 'NA' for that field.
    - Always give amount fields with the precision of 2 decimal places e.g. 102.20.

    **Tax:**
    - Tax amount can't be less than $0.00. It has to have have some value equal to or greater than zero while less than sub total.

    **Paid Amount:**
    - If the bill explicitly states the amount paid (e.g., "Amount Paid  $100.00"), extract that value.
    - If the bill doesn't mention the amount paid, return "NA".

    Example output when all fields are available:
    {{
        "bill_number": "100",
        "bill_date": "6/26/2012",
        "bill_payment_date": "6/26/2012",
        "bill_paid_by": "Mr. X",
        "bill_subtotal_paid": "$25,233.00",
        "bill_tax_paid": "$1,601.88",
        "bill_total_paid": "$27,231.88",
        "line_items": {
          {
            "description": "Transportation of Materials",
            "Amount": "450"
          },
          {
            "description": "Transportation of Materials",
            "Amount": "1000"
          }
        }
    }}

    Example output when some fields are missing:
    {{
        "bill_number": "100",
        "bill_date": "NA",
        "bill_payment_date": "6/26/2012",
        "bill_paid_by": "NA",
        "bill_subtotal_paid": "$25,233.00",
        "bill_tax_paid": "$1,601.88",
        "bill_total_paid": "$27,231.88",
        "line_items": {
          {
            "description": "Foundation Labor",
            "Amount": "500"
          },
          {
            "description": "PCC",
            "amount": "1170"
          }
        }
    }}

    Now, please provide the extracted details in JSON format. Do not miss any field in the JSON, if any value is not available, return 'NA' for that.
    '''
    # --- Gemini API Call ---
    model = genai.GenerativeModel(gemini_model_name)
    response = model.generate_content(prompt)
    # --- End of Change ---
    
    logger.info("======bill details========")
    
    cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
    logger.info(cleaned_response)
    
    reconciliation_data = json.loads(cleaned_response)
    return reconciliation_data

def save_and_process_file(file: UploadFile, is_invoice: bool = False):
    file_name = file.filename
    file_path = upload_directory_path + file_name

    # 👈 To create the directory if it doesn't exist
    Path(upload_directory_path).mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_type = get_file_type(file_name)
    text = extract_text_based_on_file_type(file_type, str(file_path))
    if is_invoice:
        details = fetch_invoice_details(text)
        #verification = verify_invoice_details(details)
        return details
    else:
        details = fetch_bill_details(text)
        return details
    
def aggregate_bills_subtotal(bills):
    return sum(float(clean_currency(bill['bill_subtotal_paid'])) for bill in bills)

def aggregate_bills_tax(bills):
    return sum(float(clean_currency(bill['bill_tax_paid'])) for bill in bills)

def aggregate_bills_total(bills):
    return sum(float(clean_currency(bill['bill_total_paid'])) for bill in bills)

def perform_reconciliation(invoice_data, bills_data):
    subtotal_bills = aggregate_bills_subtotal(bills_data)
    tax_bills = aggregate_bills_tax(bills_data)
    total_bills = aggregate_bills_total(bills_data)

    # Ensure all monetary values are formatted with 2 decimal places
    invoice_subtotal_due = float(clean_currency(invoice_data['invoice_subtotal_due']))
    invoice_tax_due = float(clean_currency(invoice_data['invoice_tax_due']))
    invoice_total_due = float(clean_currency(invoice_data['invoice_total_due']))

    all_matches = []
    all_mismatches = []

    for bill in bills_data:
        matched, mismatched = match_line_items(invoice_data["line_items"], bill["line_items"])
        all_matches.extend(matched)
        all_mismatches.extend(mismatched)


    prompt = f'''
    You are an advanced data reconciliation system. Your task is to reconcile the details between an invoice and multiple bills. Below are the details extracted from the invoice and the list of bills. Perform a reconciliation and provide a summary of any discrepancies or confirmations.

    ***Context***
    **invoice_number**: {invoice_data['invoice_number']}
    **invoice_date**: {invoice_data['invoice_date']}
    **invoice_due_date**: {invoice_data['invoice_due_date']}
    **invoice_to**: {invoice_data['invoice_to']}
    **invoice_subtotal_due**: {invoice_subtotal_due:.2f}
    **invoice_tax_due**: {invoice_tax_due:.2f}
    **invoice_total_due**: {invoice_total_due:.2f}

    '''
    
    for i, bill in enumerate(bills_data, 1):
        prompt += f'''
      **bills:**
        *bill_number*: {bill['bill_number']}
        *bill_date*: {bill['bill_date']}
        *bill_payment_date*: {bill['bill_payment_date']}
        *bill_paid_by*: {bill['bill_paid_by']}
        *bill_subtotal_paid*: {float(clean_currency(bill['bill_subtotal_paid'])):.2f}
        *bill_tax_paid*: {float(clean_currency(bill['bill_tax_paid'])):.2f}
        *bill_total_paid*: {float(clean_currency(bill['bill_total_paid'])):.2f}
    '''
    
    prompt += f'''

    **subtotal_difference**: 
        {invoice_subtotal_due:.2f} - {subtotal_bills:.2f}
    **tax_difference**: 
        {invoice_tax_due:.2f} - {tax_bills:.2f}
    **total_difference**: 
        {invoice_total_due:.2f} - {total_bills:.2f}


    **discrepancies**: 
        True if subtotal_difference > 0 OR tax_difference > 0 OR total_difference > 0 else False
    
    **reconciliation_summary**: 
        Please refer to the following examples
        
        Case 1: Discrepancies Found
        1. If discrepancy found in subtotal: "There is a discrepancy of {{give the value of subtotal_difference here}} in the subtotal. The invoice shows a subtotal of ${invoice_subtotal_due:.2f}, while the bill indicates a subtotal of ${subtotal_bills:.2f}."
        2. If discrepancy found in the tax: "There is a discrepancy of {{give the value of tax_difference here}} in the tax. The invoice indicates tax due of ${invoice_tax_due:.2f}, whereas the bill shows tax paid as ${tax_bills:.2f}."
        
        Always include the following line at the last:
        "The total amount differs by {{give the value of total_difference here}}. According to the invoice, the total due is ${invoice_total_due:.2f}, but the bill records a total paid of ${total_bills:.2f}."
        
        Case 2: No Discrepancies Found
        "All amounts match. No discrepancies found between the invoice and bill."

    ***Instructions***
    - Compare the similar details between the invoice and the bill.
    - Highlight any discrepancies.
    - Do not miss any of the fields, especially the fields like subtotal_difference, tax_difference, and total_difference in the response JSON.
    - Confirm if the details match or if there are any inconsistencies.
    - Provide a structured JSON output summarizing the reconciliation.
    - Always give amount fields with the precision of 2 decimal places e.g. 102.20

    Example output: when the difference amount is zero.
    {{
        "invoice_number": "10001",
        "invoice_date": "6/15/2024",
        "invoice_due_date": "30 days",
        "invoice_to": "Jash Enterprises",
        "invoice_subtotal_due": "$30,000.00",
        "invoice_tax_due": "$3,000.00",
        "invoice_total_due": "$33,000.00",
        "bills": [
            {{
                "bill_number": "99011",
                "bill_date": "6/26/2024",
                "bill_payment_date": "6/26/2024",
                "bill_subtotal_paid": "$10,000.00",
                "bill_tax_paid": "$1,000.00",
                "bill_total_paid": "$11,000.00",
                "bill_paid_by": "Mr. John Doe"
            }},
            {{
                "bill_number": "99012",
                "bill_date": "6/27/2024",
                "bill_payment_date": "6/28/2024",
                "bill_subtotal_paid": "$20,000.00",
                "bill_tax_paid": "$2,000.00",
                "bill_total_paid": "$22,000.00",
                "bill_paid_by": "Mr. John Doe"
            }}
        ],
        "subtotal_difference": "$0.00",
        "tax_difference": "$0.00",
        "total_difference": "$0.00",
        "discrepancies": "False",
        "reconciliation_summary": "No discrepancies found between the given invoice and bill."
    }}

    Example output when the difference amount is non-zero:
    {{
        "invoice_number": "10001",
        "invoice_date": "6/15/2024",
        "invoice_due_date": "30 days",
        "invoice_to": "Jash Enterprises",
        "invoice_subtotal_due": "$30,000.00",
        "invoice_tax_due": "$3,000.00",
        "invoice_total_due": "$33,000.00",
        "bills": [
            {{
                "bill_number": "99011",
                "bill_date": "6/26/2024",
                "bill_payment_date": "6/26/2024",
                "bill_subtotal_paid": "$10,000.00",
                "bill_tax_paid": "$900.00",
                "bill_total_paid": "$10,900.00",
                "bill_paid_by": "Mr. John Doe"
            }},
            {{
                "bill_number": "99012",
                "bill_date": "6/27/2024",
                "bill_payment_date": "6/28/2024",
                "bill_subtotal_paid": "$20,000.00",
                "bill_tax_paid": "$1,800.00",
                "bill_total_paid": "$21,800.00",
                "bill_paid_by": "Mr. John Doe"
            }}
        ],
        "subtotal_difference": "$0.00",
        "tax_difference": "$300.00",
        "total_difference": "$300.00",
        "discrepancies": "True",
        "reconciliation_summary": "Discrepancies found between the given invoice and bills."
    }}

    Now, please provide the extracted details in JSON format only. Do not miss any field in the output JSON, if any value is not available, return 'NA' for that.
    '''

    # --- Gemini API Call ---
    model = genai.GenerativeModel(gemini_model_name)
    response = model.generate_content(prompt)
    # --- End of Change ---
    
    # ... (rest of the function)
    
    # You will also need to update how the response is parsed here
    cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
    logger.info(cleaned_response)
    
    reconciliation_data = json.loads(cleaned_response)

    # Inject line item verification results
    reconciliation_data['line_item_verification'] = {
        "matched_items": all_matches,
        "mismatched_items": all_mismatches,
        "discrepancy_found": bool(all_mismatches)
    }

    return reconciliation_data


def convert_sql_results_to_dicts(results):
    keys = [
        "invoice_number", "invoice_date", "invoice_due_date", "invoice_to", "invoice_subtotal_due", 
        "invoice_tax_due", "invoice_total_due", "invoice_file_url", "bill_number", "bill_date", 
        "bill_payment_date", "bill_paid_by", "bill_subtotal_paid", "bill_tax_paid", "bill_total_paid", 
        "bill_file_url", "discrepancies", "reconciliation_summary", "total_difference", "contact_number", 
        "email"
    ]
    invoices = []

    for result in results:
        invoice = dict(zip(keys, result))
        if isinstance(invoice.get("invoice_date"), date):
            invoice["invoice_date"] = invoice["invoice_date"].isoformat()
        if isinstance(invoice.get("invoice_due_date"), date):
            invoice["invoice_due_date"] = invoice["invoice_due_date"].isoformat()
        if isinstance(invoice.get("bill_date"), date):
            invoice["bill_date"] = invoice["bill_date"].isoformat()
        if isinstance(invoice.get("bill_payment_date"), date):
            invoice["bill_payment_date"] = invoice["bill_payment_date"].isoformat()
        if "discrepancies" in invoice and isinstance(invoice["discrepancies"], bool):
            invoice["discrepancies"] = 'Yes' if invoice["discrepancies"] else 'No'
        invoices.append(invoice)
    return invoices

def match_line_items(invoice_items, bill_items):
    mismatches = []
    matched_items = []

    for b_item in bill_items:
        b_desc = b_item.get('description', '').strip().lower()
        b_raw_amount = b_item.get('amount') or b_item.get('Amount') or '0'
        try:
            b_amount = round(float(clean_currency(b_raw_amount)), 2)
        except Exception:
            b_amount = 0.00  # Fallback if amount parsing fails

        if not b_desc:
            mismatches.append({
                "description": "NA",
                "bill_amount": f"${b_amount:.2f}",
                "invoice_amount": "NA",
                "match": False,
                "reason": "Missing description in bill line item"
            })
            continue

        match_found = False

        for i_item in invoice_items:
            i_desc = i_item.get('description', '').strip().lower()
            i_raw_amount = i_item.get('line_total') or '0'
            try:
                i_amount = round(float(clean_currency(i_raw_amount)), 2)
            except Exception:
                i_amount = 0.00

            # Normalize and match descriptions
            if b_desc == i_desc:
                match_found = True
                if b_amount != i_amount:
                    mismatches.append({
                        "description": b_item['description'],
                        "bill_amount": f"${b_amount:.2f}",
                        "invoice_amount": f"${i_amount:.2f}",
                        "match": False,
                        "reason": "Amount mismatch"
                    })
                else:
                    matched_items.append({
                        "description": b_item['description'],
                        "amount": f"${b_amount:.2f}",
                        "match": True
                    })
                break

        if not match_found:
            mismatches.append({
                "description": b_item['description'],
                "bill_amount": f"${b_amount:.2f}",
                "invoice_amount": "NA",
                "match": False,
                "reason": "Line item not found in invoice"
            })

    return matched_items, mismatches