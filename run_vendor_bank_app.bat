@echo off
cd /d D:\VendorBankApp\app
D:\VendorBankApp\.venv\Scripts\streamlit.exe run 00_CODE\FC_VENDOR_BANK_APP.py --server.port 8501 --server.headless true
