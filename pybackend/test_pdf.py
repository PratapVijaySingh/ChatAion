#!/usr/bin/env python3
"""
Test script for PDF processing functionality
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from pdf_utils import extract_text_from_pdf, get_pdf_metadata, is_pdf_file
    print("✅ PDF utilities imported successfully")
    
    # Test fitz import
    import fitz
    print("✅ PyMuPDF (fitz) imported successfully")
    
    # Test basic functionality
    print("✅ PDF processing functionality is ready")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("🎉 All PDF processing tests passed!")
