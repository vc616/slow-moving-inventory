from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.database import get_db
from app import crud
from app.schemas import InventoryRecordCreate, InventoryRecordResponse, PhotoResponse, ImportResult
from app.auth import get_current_user
from app.models import User, Photo
from app.utils.excel_loader import import_materials_from_excel
from app.utils.file_lock import FileLockManager, get_abs_photo_dir

router = APIRouter(prefix="/api/inventory", tags=["盘库管理"])

MAX_PHOTOS_PER_MATERIAL = 10


@router.post("/records", response_model=InventoryRecordResponse)
def create_inventory_record(
    record: InventoryRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    material = crud.get_material(db, record.material_code)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    if record.score < 1 or record.score > 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")

    return crud.create_inventory_record(
        db=db,
        material_code=record.material_code,
        score=record.score,
        operator=current_user.username
    )


@router.get("/records/{material_code}", response_model=List[InventoryRecordResponse])
def get_inventory_records(
    material_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    material = crud.get_material(db, material_code)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    return crud.get_inventory_records(db, material_code)


@router.post("/photos/{material_code}", response_model=PhotoResponse)
async def upload_photo(
    material_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    material = crud.get_material(db, material_code)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    photo_count = crud.get_photo_count(db, material_code)
    if photo_count >= MAX_PHOTOS_PER_MATERIAL:
        raise HTTPException(
            status_code=400,
            detail=f"每个物料最多上传{MAX_PHOTOS_PER_MATERIAL}张照片"
        )

    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG/PNG/WebP 格式")

    photo_dir = get_abs_photo_dir(material.code)
    Path(photo_dir).mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(photo_dir, filename)

    lock = FileLockManager.acquire(material.code)
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        relative_path = os.path.join("photos", material.code, filename).replace("\\", "/")
        return crud.create_photo(
            db=db,
            material_code=material_code,
            file_path=relative_path,
            filename=filename,
            operator=current_user.username
        )
    finally:
        FileLockManager.release(material.code)


@router.get("/photos/{material_code}", response_model=List[PhotoResponse])
def get_photos(
    material_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    material = crud.get_material(db, material_code)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    return crud.get_photos(db, material_code)


@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        abs_file_path = os.path.join(base_dir, photo.file_path)
        if os.path.exists(abs_file_path):
            os.remove(abs_file_path)
    except Exception:
        pass

    crud.delete_photo(db, photo_id)
    return {"message": "照片已删除"}


@router.post("/import", response_model=ImportResult)
def import_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success, failed, errors = import_materials_from_excel()
    return ImportResult(success=success, failed=failed, errors=errors)
