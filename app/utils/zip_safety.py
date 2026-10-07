import zipfile


def check_zip_safety(zip_path: str, max_uncompressed_size: int = 200 * 1024 * 1024) -> bool:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            total_size = 0
            for info in zf.infolist():
                if info.file_size > max_uncompressed_size:
                    return False
                total_size += info.file_size
                if total_size > max_uncompressed_size:
                    return False
                # Prevent zip slip
                if info.filename.startswith("/") or ".." in info.filename:
                    return False
        return True
    except zipfile.BadZipFile:
        return False
