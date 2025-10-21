import os
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import fitz  # PyMuPDF
from docx import Document as DocxDocument
import mimetypes

class DocumentProcessor:
    """Handle file upload and text extraction"""
    
    def __init__(self, upload_folder: str = "./uploads"):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        
        # Allowed file extensions
        self.allowed_extensions = {'.pdf', '.docx', '.txt', '.md'}
        
        # Max file size (16MB)
        self.max_file_size = 16 * 1024 * 1024
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return Path(filename).suffix.lower() in self.allowed_extensions
    
    def validate_file(self, file: FileStorage) -> Dict[str, any]:
        """Validate uploaded file"""
        errors = []
        
        if not file or not file.filename:
            errors.append("No file provided")
            return {"valid": False, "errors": errors}
        
        if not self.is_allowed_file(file.filename):
            errors.append(f"File type not allowed. Supported: {', '.join(self.allowed_extensions)}")
        
        # Check file size (if possible)
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > self.max_file_size:
                errors.append(f"File too large. Max size: {self.max_file_size // (1024*1024)}MB")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "filename": file.filename,
            "size": getattr(file, 'content_length', None)
        }
    
    def save_file(self, file: FileStorage, chatbot_id: str) -> Dict[str, any]:
        """Save uploaded file to disk"""
        try:
            # Create chatbot-specific directory
            chatbot_dir = self.upload_folder / chatbot_id
            chatbot_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            original_filename = file.filename
            file_extension = Path(original_filename).suffix.lower()
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = chatbot_dir / unique_filename
            
            # Save file
            file.save(str(file_path))
            
            # Get file info
            file_size = file_path.stat().st_size
            file_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": unique_filename,
                "original_filename": original_filename,
                "file_size": file_size,
                "file_type": file_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = PyMuPDF.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Error extracting text from TXT: {str(e)}")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from file based on extension"""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension in ['.txt', '.md']:
            return self.extract_text_from_txt(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_extension}")
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get file information"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise Exception(f"File not found: {file_path}")
        
        stat = file_path.stat()
        
        return {
            "filename": file_path.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": file_path.suffix.lower(),
            "exists": True
        }