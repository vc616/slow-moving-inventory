from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ScoreEnum(enum.IntEnum):
    SCORE_1 = 1
    SCORE_2 = 2
    SCORE_3 = 3
    SCORE_4 = 4
    SCORE_5 = 5


class Material(Base):
    __tablename__ = "materials"

    code = Column(String(50), primary_key=True, index=True)
    name = Column(String(200))
    spec = Column(String(500))
    model = Column(String(200))
    unit = Column(String(50))
    quantity = Column(String(50))
    unit_price = Column(String(50))
    total_amount = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory_records = relationship("InventoryRecord", back_populates="material", foreign_keys="InventoryRecord.material_code")
    photos = relationship("Photo", back_populates="material", foreign_keys="Photo.material_code")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), ForeignKey("materials.code"), nullable=False)
    score = Column(Integer, nullable=False)
    operator = Column(String(100))
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)

    material = relationship("Material", back_populates="inventory_records", foreign_keys=[material_code])


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), ForeignKey("materials.code"), nullable=False)
    file_path = Column(String(500), nullable=False)
    filename = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    operator = Column(String(100))

    material = relationship("Material", back_populates="photos", foreign_keys=[material_code])
