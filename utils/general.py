"""
Filename: general.py
Author: Ashish Sharma
Date created: 15/05/2025
License: MIT License
Description: This file contains generic functions.
"""

from utils.logs import logger
import mimetypes
from PyPDF2 import PdfReader
from datetime import datetime
    
def get_file_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    if (mime_type == None):
        parts = filename.split('.')
        extension = parts[-1]
        return extension
    return mime_type

def extract_text_from_pdf(file_path):
  """
  Extracts text from a PDF file and returns the combined text.

  Args:
      file_path (str): The path to the PDF file.

  Returns:
      str: The extracted text from the PDF file.
  """

  print("Extracting text from pdf...")
  try:
    with open(file_path, 'rb') as pdf_file:
      reader = PdfReader(pdf_file)
      totalPages = len(reader.pages)
      extracted_text = ""

      for i in range(0, totalPages):
        extracted_text += reader.pages[i].extract_text()
      return extracted_text
  except FileNotFoundError:
      print(f"Error: File not found at {file_path}")
      return ""

def extract_text_from_file(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text
     
def extract_text_based_on_file_type(file_type, file_path):
    extraction_functions = {
        'application/pdf': extract_text_from_pdf,
        'text/plain': extract_text_from_file
    }
    if file_type in extraction_functions:
        logger.info("======= {} =======".format(file_type))
        text_extraction_function = extraction_functions[file_type]
        return text_extraction_function(file_path)
    else:
        logger.error("Unsupported file type:", file_type)
        return None
    
def clean_currency(value):
    """Removes dollar signs and commas from a currency string."""
    if value is None:
        return "0.00"
    if not isinstance(value, str):
        raise ValueError("Input must be a string or None")
    return value.replace('$', '').replace(',', '')

def parse_date(date_string):
    """Parses a date string using various date formats."""
    if date_string is None or date_string == "NA":
        return None  # Return None for NA or None input
    date_formats = [
        '%d/%m/%Y', '%m/%d/%Y', '%Y/%d/%m', '%Y/%m/%d',
        '%d-%m-%Y', '%m-%d-%Y', '%Y-%d-%m', '%Y-%m-%d',
        '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d', '%Y.%m.%d'
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None #return none if no format matches