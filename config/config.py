
"""
Filename: config.py
Author: Ashish Sharma
Date created: 15/06/2025
License: MIT License
Description: This file contains application configuration.
"""

from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from openai import OpenAI
import os
import json
import tempfile
from pathlib import Path

load_dotenv()

import google.generativeai as genai
import os

# -----------------
# New Gemini Configuration
# -----------------
# It's recommended to store your API key as an environment variable for security.
# However, for a direct replacement, you can place it here.
GOOGLE_API_KEY = "AIzaSyA72Zz_on4cjtL-TvsPad3-22bXqmaQQhY" # 👈 Replace with your actual key
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model_name = "gemini-1.5-pro-latest" 

openai_api_key = os.environ['OPENAI_API_KEY']
openai_gpt_model = 'gpt-3.5-turbo'
# openai_client = OpenAI(api_key=openai_api_key)

import openai
openai_client = openai.Client(api_key=openai_api_key)


openai_embeddings = OpenAIEmbeddings(api_key=openai_api_key)
openai_llm = ChatOpenAI(  
        openai_api_key=openai_api_key,
        model_name='gpt-4.5',  
        temperature=0.0  
    )
api_client_id = os.environ['API_CLIENT_ID']
api_client_secret = os.environ['API_CLIENT_SECRET']
local_download_path = os.environ['LOCAL_DOWNLOAD_PATH']

#AIML-17
LANGCHAIN_API_KEY = os.environ['LANGCHAIN_API_KEY']
LANGCHAIN_TRACING_V2 = os.environ['LANGCHAIN_TRACING_V2']
LANGCHAIN_ENDPOINT= os.environ['LANGCHAIN_ENDPOINT'] 
LANGCHAIN_PROJECT = os.environ['LANGCHAIN_PROJECT'] 

#Invoice Path 
upload_directory_path = "uploads/"

# CORS settings
ALLOW_ORIGINS = ["*"]  # In production, replace "*" with the actual origins
ALLOW_CREDENTIALS = True
ALLOW_METHODS = ["POST", "GET"]  # Make sure to allow the methods you use
ALLOW_HEADERS = ["Authorization", "Content-Type"]	