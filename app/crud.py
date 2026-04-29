from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime

from app.models import Material, User, InventoryRecord, Photo
from app.schemas import MaterialCreate, UserCreate


def get_material(db: Session, code: str) -> Optional[Material]:
    return db.query(Material).filter(Material.code == code).first()


def get_material_by_code(db: Session, code: str) -> Optional[Material]:
    return db.query(Material).filter(Material.code == code).first()


def get_material_suggestions(
    db: Session,
    keyword: str,
    limit: int = 20,
    hide_inventoried: bool = False
) -> List[dict]:
    if not keyword or len(keyword) < 1:
        return []

    keywords = keyword.split()
    query = db.query(Material)

    for kw in keywords:
        keyword_pattern = f"%{kw}%"
        query = query.filter(
            or_(
                Material.code.ilike(keyword_pattern),
                Material.name.ilike(keyword_pattern),
                Material.spec.ilike(keyword_pattern)
            )
        )

    materials = query.limit(limit * 3 if hide_inventoried else limit * 2).all()

    evaluated_codes = {
        r.material_code for r in db.query(InventoryRecord.material_code).distinct().all()
    }
    photo_codes = {
        p.material_code for p in db.query(Photo.material_code).distinct().all()
    }

    result = []
    for m in materials:
        has_inventory = m.code in evaluated_codes or m.code in photo_codes

        if hide_inventoried and has_inventory:
            continue

        result.append({
            "code": m.code,
            "name": m.name or "",
            "spec": m.spec or "",
            "has_inventory": has_inventory
        })

        if len(result) >= limit:
            break

    return result


def search_materials(
    db: Session,
    keyword: Optional[str] = None,
    has_inventory: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Material]:
    query = db.query(Material)

    if keyword:
        keywords = keyword.split()
        for kw in keywords:
            keyword_pattern = f"%{kw}%"
            query = query.filter(
                or_(
                    Material.code.ilike(keyword_pattern),
                    Material.name.ilike(keyword_pattern),
                    Material.spec.ilike(keyword_pattern)
                )
            )

    materials = query.offset(skip).limit(limit).all()

    if has_inventory is not None:
        codes_with_inventory = {
            r.material_code for r in db.query(InventoryRecord.material_code).distinct().all()
        }
        codes_with_photos = {
            p.material_code for p in db.query(Photo.material_code).distinct().all()
        }

        filtered = []
        for m in materials:
            has_record = m.code in codes_with_inventory or m.code in codes_with_photos
            if has_inventory and has_record:
                filtered.append(m)
            elif not has_inventory and not has_record:
                filtered.append(m)
        return filtered

    return materials


def create_material(db: Session, material: MaterialCreate) -> Material:
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


def create_materials_bulk(db: Session, materials: List[MaterialCreate]) -> tuple:
    success = 0
    failed = 0
    errors = []

    for m in materials:
        try:
            existing = get_material_by_code(db, m.code)
            if existing:
                for key, value in m.model_dump().items():
                    if value is not None:
                        setattr(existing, key, value)
                db.commit()
                success += 1
            else:
                db_material = Material(**m.model_dump())
                db.add(db_material)
                db.commit()
                success += 1
        except Exception as e:
            db.rollback()
            errors.append(f"物料编码 {m.code}: {str(e)}")
            failed += 1

    return success, failed, errors


def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def create_inventory_record(
    db: Session,
    material_code: str,
    score: int,
    operator: str
) -> InventoryRecord:
    record = InventoryRecord(
        material_code=material_code,
        score=score,
        operator=operator,
        evaluated_at=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_inventory_records(db: Session, material_code: str) -> List[InventoryRecord]:
    return db.query(InventoryRecord).filter(
        InventoryRecord.material_code == material_code
    ).order_by(InventoryRecord.evaluated_at.desc()).all()


def get_latest_inventory_record(db: Session, material_code: str) -> Optional[InventoryRecord]:
    return db.query(InventoryRecord).filter(
        InventoryRecord.material_code == material_code
    ).order_by(InventoryRecord.evaluated_at.desc()).first()


def create_photo(
    db: Session,
    material_code: str,
    file_path: str,
    filename: str,
    operator: str
) -> Photo:
    photo = Photo(
        material_code=material_code,
        file_path=file_path,
        filename=filename,
        operator=operator,
        uploaded_at=datetime.utcnow()
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def get_photos(db: Session, material_code: str) -> List[Photo]:
    return db.query(Photo).filter(
        Photo.material_code == material_code
    ).order_by(Photo.uploaded_at.desc()).all()


def get_photo_count(db: Session, material_code: str) -> int:
    return db.query(Photo).filter(Photo.material_code == material_code).count()


def delete_photo(db: Session, photo_id: int) -> bool:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo:
        db.delete(photo)
        db.commit()
        return True
    return False


def get_all_materials_simple(db: Session) -> List[Material]:
    return db.query(Material).all()


def get_category_stats(db: Session) -> List[dict]:
    """按物料号首字母分类统计"""
    materials = db.query(Material).all()

    evaluated_codes = {
        r.material_code for r in db.query(InventoryRecord.material_code).distinct().all()
    }
    photo_codes = {
        p.material_code for p in db.query(Photo.material_code).distinct().all()
    }

    categories = {}
    for m in materials:
        first_char = m.code[0].upper() if m.code else '#'
        if not first_char.isalpha():
            first_char = '#'

        if first_char not in categories:
            categories[first_char] = {'total': 0, 'evaluated': 0}

        categories[first_char]['total'] += 1
        if m.code in evaluated_codes or m.code in photo_codes:
            categories[first_char]['evaluated'] += 1

    result = []
    for letter in sorted(categories.keys()):
        data = categories[letter]
        result.append({
            'letter': letter,
            'total': data['total'],
            'evaluated': data['evaluated'],
            'not_evaluated': data['total'] - data['evaluated'],
            'progress': round(data['evaluated'] / data['total'] * 100, 1) if data['total'] > 0 else 0
        })

    return result
