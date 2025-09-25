"""
PDF Processing Utilities for ChatAion
Handles PDF text extraction and processing
"""

import logging
from typing import Optional, List, Dict, Any
import os

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text from a PDF file using PyMuPDF (fitz)
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text or None if error
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Please install with: pip install PyMuPDF")
        return None
    
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        text_content = []
        
        # Extract text from each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():  # Only add non-empty pages
                text_content.append(f"--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        
        if text_content:
            return "\n\n".join(text_content)
        else:
            logger.warning(f"No text content found in PDF: {pdf_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return None

def get_pdf_metadata(pdf_path: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with PDF metadata or None if error
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Please install with: pip install PyMuPDF")
        return None
    
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        page_count = len(doc)
        doc.close()
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": page_count,
            "file_size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting PDF metadata {pdf_path}: {str(e)}")
        return None

def is_pdf_file(file_path: str) -> bool:
    """
    Check if a file is a valid PDF
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if valid PDF, False otherwise
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Please install with: pip install PyMuPDF")
        return False
    
    try:
        if not os.path.exists(file_path):
            return False
            
        # Try to open the file as PDF
        doc = fitz.open(file_path)
        doc.close()
        return True
        
    except Exception:
        return False

def extract_pdf_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    Extract images from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
        
    Returns:
        List of paths to extracted image files
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Please install with: pip install PyMuPDF")
        return []
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        image_paths = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_path = os.path.join(output_dir, f"page_{page_num + 1}_img_{img_index + 1}.png")
                    pix.save(img_path)
                    image_paths.append(img_path)
                
                pix = None
        
        doc.close()
        return image_paths
        
    except Exception as e:
        logger.error(f"Error extracting images from PDF {pdf_path}: {str(e)}")
        return []
