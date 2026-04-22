"""
File Handler Service - Handles file operations for uploaded PDFs
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class FileHandler:
    """Handles file operations for uploaded PDFs."""
    
    def __init__(self):
        self.upload_dir = Path(os.getenv("UPLOADS_DIR", "uploads"))
        self.output_dir = Path(os.getenv("OUTPUTS_DIR", "outputs"))
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure upload and output directories exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file) -> str:
        """
        Save uploaded file to uploads directory.
        
        Args:
            file: Uploaded file object
            
        Returns:
            str: Path to saved file
        """
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(file.filename).name
        filename = f"{timestamp}_{original_name}"
        file_path = self.upload_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return str(file_path)
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """
        List all uploaded PDF files.
        
        Returns:
            List of file information dictionaries
        """
        files = []
        for filename in os.listdir(self.upload_dir):
            if filename.lower().endswith('.pdf'):
                file_path = self.upload_dir / filename
                file_stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "file_path": str(file_path),
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
        
        return sorted(files, key=lambda x: x["created"], reverse=True)
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from uploads directory.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        file_path = self.upload_dir / Path(filename).name
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def get_file_path(self, filename: str) -> str:
        """
        Get full path for a filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            str: Full path to the file
        """
        return str(self.upload_dir / Path(filename).name)
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in uploads directory.
        
        Args:
            filename: Name of the file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        file_path = self.upload_dir / Path(filename).name
        return file_path.exists()
    
    def get_file_size(self, filename: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            filename: Name of the file
            
        Returns:
            int: File size in bytes
        """
        file_path = self.upload_dir / Path(filename).name
        if file_path.exists():
            return file_path.stat().st_size
        return 0
