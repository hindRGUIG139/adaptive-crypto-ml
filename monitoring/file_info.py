import os

def get_file_info(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    file_size = os.path.getsize(file_path)  # Size in bytes
    extension = os.path.splitext(file_path)[1].lower()  # File extension
    FILE_TYPES = {
    ".txt": "Text",
    ".csv": "CSV",
    ".json": "JSON",
    ".xml": "XML",
    ".pdf": "PDF",
    ".jpg": "Image",
    ".jpeg": "Image",
    ".png": "Image",
    ".gif": "Image",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".mp4": "Video",
    ".avi": "Video",
    ".zip": "Archive"
}
    
    return {
        "size_bytes": file_size,
        "extension": extension,
        "data_type": FILE_TYPES.get(extension, "Unknown")
    }