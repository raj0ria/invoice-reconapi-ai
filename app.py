"""
Filename: app.py
Author: Ashish Sharma
Date created: 15/05/2025
License: MIT License
Description: Entry point of the app, contains API implementation.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from typing import List
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
from pathlib import Path
from utils.invoice_processing import save_and_process_file
from config.config import ALLOW_ORIGINS, ALLOW_HEADERS, ALLOW_CREDENTIALS, ALLOW_METHODS
from utils.logs import logger
from utils.invoice_processing import perform_reconciliation

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

@app.get('/')
def hello_world():
    return "Hello,World"

@app.post("/api/invoice/reconcile")
async def reconcile_invoice(
    invoice_file: UploadFile = File(...),
    bill_files: List[UploadFile] = File(...)
):
    
    # Process invoice file
    invoice_details = save_and_process_file(invoice_file, is_invoice=True)
    
    # Process each bill file
    bill_details_list = []
    for bill_file in bill_files:
        bill_details = {}
        bill_details = save_and_process_file(bill_file, is_invoice=False)
        bill_details_list.append(bill_details)

    print("=========bill_details_list=========", bill_details_list)

    reconciliation_data = perform_reconciliation(invoice_details, bill_details_list)
    
    return {
        "invoice_details": invoice_details,
        "bill_details": bill_details_list,
        "result": reconciliation_data
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)