import os
import tempfile
import zipfile

from app.utils.zip_safety import check_zip_safety


def test_check_zip_safety():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("safe_file.txt", "hello")
        
    assert check_zip_safety(path) is True
    
    # Zip slip test
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("../unsafe.txt", "hello")
        
    assert check_zip_safety(path) is False
    os.remove(path)
