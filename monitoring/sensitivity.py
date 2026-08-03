import os

PUBLIC = 0
INTERNAL = 1
CONFIDENTIAL = 2

def get_sensitivity(file_path):
    folder = os.path.basename(os.path.dirname(file_path)).lower()

    if folder == "public":
        return PUBLIC
    elif folder == "internal":
        return INTERNAL
    elif folder == "confidential":
        return CONFIDENTIAL

    return PUBLIC