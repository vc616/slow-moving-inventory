from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import CategoryStatsResponse
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/stats", tags=["统计"])


@router.get("/categories", response_model=CategoryStatsResponse)
def get_category_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = crud.get_category_stats(db)

    total_materials = sum(c['total'] for c in categories)
    total_evaluated = sum(c['evaluated'] for c in categories)
    total_not_evaluated = sum(c['not_evaluated'] for c in categories)
    overall_progress = round(total_evaluated / total_materials * 100, 1) if total_materials > 0 else 0

    return CategoryStatsResponse(
        categories=categories,
        total_materials=total_materials,
        total_evaluated=total_evaluated,
        total_not_evaluated=total_not_evaluated,
        overall_progress=overall_progress
    )
