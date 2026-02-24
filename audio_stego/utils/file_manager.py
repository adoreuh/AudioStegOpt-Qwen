import os
import tempfile
import uuid
from typing import Optional

class FileManager:
    def __init__(self, upload_dir: str = "uploads", output_dir: str = "outputs"):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def save_uploaded_file(self, file_data: bytes, filename: str) -> str:
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path

    def save_output_file(self, file_data: bytes, filename: str) -> str:
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"output_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(self.output_dir, unique_filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path

    def get_file_path(self, filename: str, directory: str = None) -> str:
        if directory is None:
            directory = self.upload_dir
        return os.path.join(directory, filename)

    def file_exists(self, filepath: str) -> bool:
        return os.path.exists(filepath)

    def delete_file(self, filepath: str) -> bool:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception:
            return False

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for directory in [self.upload_dir, self.output_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        if self.delete_file(filepath):
                            deleted_count += 1
        
        return deleted_count

    def get_file_info(self, filepath: str) -> dict:
        if not os.path.exists(filepath):
            return {}
        
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'extension': os.path.splitext(filepath)[1]
        }