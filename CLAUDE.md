# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

物料信息采集系统 (Slow-Moving Inventory Information System) - A mobile-friendly inventory checking system for evaluating material condition and uploading photos. Built for ~10 concurrent users.

## Commands

### Start the backend server
```bash
# Using venv (Windows)
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or with reload for development
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Default credentials
- Username: `admin`
- Password: `admin123`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HTML/CSS/JS Frontend (templates/, static/)                │
│  - Served by FastAPI                                       │
│  - Mobile-optimized UI                                     │
│  - JavaScript API client (main.js)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (app/main.py)                             │
│  - Port 8000 (or 8001 if 8000 occupied)                   │
│  - JWT authentication                                      │
│  - Serves: HTML, static files, API                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  SQLite Database (data/inventory.db)                       │
│  - Tables: materials, users, inventory_records, photos     │
└─────────────────────────────────────────────────────────────┘
```

## Key Modules

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app entry, CORS, routers, lifespan, serves frontend |
| `app/models.py` | SQLAlchemy models: Material, User, InventoryRecord, Photo |
| `app/schemas.py` | Pydantic schemas for request/response validation |
| `app/crud.py` | Database operations: search, create, read |
| `app/auth.py` | JWT token creation/validation, OAuth2 scheme |
| `app/routers/auth.py` | Login/register endpoints |
| `app/routers/materials.py` | Material search/suggestions endpoints |
| `app/routers/inventory.py` | Scoring, photo upload/delete, Excel import |
| `app/utils/file_lock.py` | FileLockManager for serializing photo uploads |
| `app/utils/excel_loader.py` | Reads `物料总表.xlsx` and maps columns |
| `templates/index.html` | Jinja2 template for main page |
| `static/js/main.js` | Frontend JavaScript API client |
| `static/css/style.css` | Mobile-optimized styles |

## Data Flow

### Frontend Authentication
1. Page loads → JS calls `/api/auth/token` with username/password
2. Backend returns JWT token
3. JS stores token in localStorage
4. All subsequent API requests include `Authorization: Bearer {token}`

### Photo Upload (with concurrency control)
1. Client uploads photo to `/api/inventory/photos/{material_id}`
2. `FileLockManager.acquire(material.code)` - acquires per-material lock
3. Photo saved to `photos/{material_code}/{uuid}.{ext}`
4. `Photo` record created in database
5. `FileLockManager.release()` - releases lock

### Excel Import
1. POST `/api/inventory/import`
2. Reads `物料总表.xlsx` via `excel_loader.py`
3. Maps columns: 物料编码→code, 物料名称→name, 规格→spec, etc.
4. Uses `crud.create_materials_bulk()` - upserts by code

## Concurrency Strategy

- **Photo uploads**: File lock per material code (prevents race conditions)
- **Database**: SQLite with default mode (supports concurrent reads)
- **API**: JWT tokens expire after 480 minutes

## Rating System (1-5 Score)

| Score | Label |
|-------|-------|
| 5 | 全新可使用 (Brand new) |
| 4 | 99新，需要翻新 (99% new, needs refurbishment) |
| 3 | 外观性能尚可 (Acceptable condition) |
| 2 | 仅作为备件或拆机件使用 (For spare parts only) |
| 1 | 建议报废 (Recommend disposal) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token` | Login, returns JWT |
| POST | `/api/auth/register` | Register new user |
| GET | `/api/auth/me` | Get current user info |
| GET | `/api/materials/` | Search materials |
| GET | `/api/materials/suggestions` | Get suggestions |
| GET | `/api/materials/{id}` | Get material detail |
| POST | `/api/inventory/records` | Submit inventory score |
| POST | `/api/inventory/photos/{id}` | Upload photo |
| DELETE | `/api/inventory/photos/{id}` | Delete photo |
| POST | `/api/inventory/import` | Import from Excel |
