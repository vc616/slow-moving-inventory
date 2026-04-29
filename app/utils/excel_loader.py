import os
import pandas as pd
from typing import List, Tuple
from pathlib import Path

from app.schemas import MaterialCreate
from app.database import SessionLocal
from app import crud


def get_excel_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(base_dir, "物料总表.xlsx")
    return excel_path


def read_materials_from_excel(excel_path: str = None) -> Tuple[List[MaterialCreate], List[str]]:
    if excel_path is None:
        excel_path = get_excel_path()

    if not os.path.exists(excel_path):
        return [], [f"Excel文件不存在: {excel_path}"]

    try:
        df = pd.read_excel(excel_path)

        column_mapping = {}
        for col in df.columns:
            col_str = str(col).strip()
            if '物料编码' in col_str or col_str == 'code':
                column_mapping['code'] = col
            elif '物料名称' in col_str or col_str == 'name':
                column_mapping['name'] = col
            elif '规格' in col_str or col_str == 'spec':
                column_mapping['spec'] = col
            elif '型号' in col_str or col_str == 'model':
                column_mapping['model'] = col
            elif '主单位' in col_str or col_str == 'unit':
                column_mapping['unit'] = col
            elif '主数量' in col_str or col_str == 'quantity':
                column_mapping['quantity'] = col
            elif '单价' in col_str or 'unit_price' in col_str:
                column_mapping['unit_price'] = col
            elif '总金额' in col_str or 'total_amount' in col_str:
                column_mapping['total_amount'] = col

        materials = []
        errors = []

        for idx, row in df.iterrows():
            try:
                code = row.get(column_mapping.get('code'))
                if pd.isna(code) or str(code).strip() == '':
                    errors.append(f"第{idx + 2}行: 物料编码为空")
                    continue

                name = row.get(column_mapping.get('name'))
                spec = row.get(column_mapping.get('spec'))
                model = row.get(column_mapping.get('model'))
                unit = row.get(column_mapping.get('unit'))
                quantity = row.get(column_mapping.get('quantity'))
                unit_price = row.get(column_mapping.get('unit_price'))
                total_amount = row.get(column_mapping.get('total_amount'))

                materials.append(MaterialCreate(
                    code=str(code).strip(),
                    name=str(name).strip() if pd.notna(name) else None,
                    spec=str(spec).strip() if pd.notna(spec) else None,
                    model=str(model).strip() if pd.notna(model) else None,
                    unit=str(unit).strip() if pd.notna(unit) else None,
                    quantity=str(quantity).strip() if pd.notna(quantity) else None,
                    unit_price=str(unit_price).strip() if pd.notna(unit_price) else None,
                    total_amount=str(total_amount).strip() if pd.notna(total_amount) else None
                ))
            except Exception as e:
                errors.append(f"第{idx + 2}行处理失败: {str(e)}")

        return materials, errors

    except Exception as e:
        return [], [f"读取Excel失败: {str(e)}"]


def import_materials_from_excel() -> Tuple[int, int, List[str]]:
    materials, errors = read_materials_from_excel()

    if not materials:
        return 0, 0, errors

    db = SessionLocal()
    try:
        success, failed, db_errors = crud.create_materials_bulk(db, materials)
        return success, failed, errors + db_errors
    finally:
        db.close()
