from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import crud
from app.schemas import MaterialResponse, MaterialDetailResponse
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/materials", tags=["物料管理"])


@router.get("/suggestions")
def get_material_suggestions(
    keyword: str = Query(..., description="搜索关键字（多个关键词用空格分隔）"),
    limit: int = Query(20, ge=1, le=50, description="返回数量限制"),
    hide_inventoried: bool = Query(False, description="是否隐藏已盘库物料")
):
    db = next(get_db())
    try:
        suggestions = crud.get_material_suggestions(db, keyword, limit, hide_inventoried)
        return suggestions
    finally:
        db.close()


@router.get("/", response_model=List[MaterialResponse])
def search_materials(
    keyword: Optional[str] = Query(None, description="搜索关键字（编码、名称、规格）"),
    has_inventory: Optional[bool] = Query(None, description="是否已盘库"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    materials = crud.search_materials(db, keyword, has_inventory, skip, limit)

    result = []
    for m in materials:
        has_record = crud.get_latest_inventory_record(db, m.code)
        has_photos = crud.get_photos(db, m.code)
        result.append(MaterialResponse(
            code=m.code,
            name=m.name,
            spec=m.spec,
            model=m.model,
            unit=m.unit,
            quantity=m.quantity,
            unit_price=m.unit_price,
            total_amount=m.total_amount,
            created_at=m.created_at,
            has_inventory=has_record is not None or len(has_photos) > 0,
            has_photos=len(has_photos) > 0
        ))

    return result


@router.get("/{code}", response_model=MaterialDetailResponse)
def get_material(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    material = crud.get_material(db, code)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    records = crud.get_inventory_records(db, code)
    photos = crud.get_photos(db, code)

    return MaterialDetailResponse(
        code=material.code,
        name=material.name,
        spec=material.spec,
        model=material.model,
        unit=material.unit,
        quantity=material.quantity,
        unit_price=material.unit_price,
        total_amount=material.total_amount,
        created_at=material.created_at,
        has_inventory=len(records) > 0 or len(photos) > 0,
        has_photos=len(photos) > 0,
        inventory_records=records,
        photos=photos
    )
