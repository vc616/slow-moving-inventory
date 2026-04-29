from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


class ScoreEnum(IntEnum):
    SCORE_1 = 1
    SCORE_2 = 2
    SCORE_3 = 3
    SCORE_4 = 4
    SCORE_5 = 5


class MaterialBase(BaseModel):
    code: str
    name: Optional[str] = None
    spec: Optional[str] = None
    model: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[str] = None
    unit_price: Optional[str] = None
    total_amount: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialResponse(MaterialBase):
    created_at: datetime
    has_inventory: bool = False
    has_photos: bool = False

    class Config:
        from_attributes = True


class MaterialDetailResponse(MaterialResponse):
    inventory_records: List["InventoryRecordResponse"] = []
    photos: List["PhotoResponse"] = []


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class InventoryRecordBase(BaseModel):
    score: int


class InventoryRecordCreate(InventoryRecordBase):
    material_code: str


class InventoryRecordResponse(InventoryRecordBase):
    id: int
    material_code: str
    operator: Optional[str]
    evaluated_at: datetime
    version: int

    class Config:
        from_attributes = True


class PhotoBase(BaseModel):
    filename: Optional[str] = None


class PhotoResponse(PhotoBase):
    id: int
    material_code: str
    file_path: str
    uploaded_at: datetime
    operator: Optional[str]

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    keyword: Optional[str] = None
    has_inventory: Optional[bool] = None


class ImportResult(BaseModel):
    success: int
    failed: int
    errors: List[str] = []


class CategoryStats(BaseModel):
    letter: str
    total: int
    evaluated: int
    not_evaluated: int
    progress: float  # 0-100

    class Config:
        from_attributes = True


class CategoryStatsResponse(BaseModel):
    categories: List[CategoryStats]
    total_materials: int
    total_evaluated: int
    total_not_evaluated: int
    overall_progress: float


MaterialDetailResponse.model_rebuild()
