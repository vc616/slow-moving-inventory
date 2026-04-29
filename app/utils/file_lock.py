import os
import filelock
from pathlib import Path

LOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "locks")
Path(LOCK_DIR).mkdir(parents=True, exist_ok=True)


class FileLockManager:
    _locks = {}

    @classmethod
    def get_lock(cls, material_code: str) -> filelock.FileLock:
        if material_code not in cls._locks:
            lock_file = os.path.join(LOCK_DIR, f"{material_code}.lock")
            cls._locks[material_code] = filelock.FileLock(lock_file, timeout=10)
        return cls._locks[material_code]

    @classmethod
    def acquire(cls, material_code: str):
        lock = cls.get_lock(material_code)
        lock.acquire()
        return lock

    @classmethod
    def release(cls, material_code: str):
        if material_code in cls._locks:
            cls._locks[material_code].release()


def save_photo_with_lock(material_code: str, photo_data: bytes, filename: str) -> str:
    photo_dir = get_material_photo_dir(material_code)
    Path(photo_dir).mkdir(parents=True, exist_ok=True)

    file_path = os.path.join(photo_dir, filename)

    lock = FileLockManager.acquire(material_code)
    try:
        with open(file_path, "wb") as f:
            f.write(photo_data)
        return file_path
    finally:
        FileLockManager.release(material_code)


def get_material_photo_dir(material_code: str) -> str:
    return os.path.join("photos", material_code)

def get_abs_photo_dir(material_code: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, "photos", material_code)
