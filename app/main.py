from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os
import secrets

from app.database import engine, Base, SessionLocal
from app.models import Material, User, InventoryRecord, Photo
from app.routers import materials, inventory, auth, stats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            from app.schemas import UserCreate
            from app import crud
            admin_user = UserCreate(
                username="admin",
                password="admin123",
                full_name="系统管理员"
            )
            crud.create_user(db, admin_user)
            print("默认管理员账户已创建: admin / admin123")
    except Exception as e:
        print(f"初始化管理员账户时出错: {e}")
    finally:
        db.close()

    yield


app = FastAPI(
    title="物料信息采集系统",
    description="用于呆滞物料盘库信息采集，支持物料查询、状态评估、照片上传",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(materials.router)
app.include_router(inventory.router)
app.include_router(stats.router)

templates = Jinja2Templates(directory=os.path.join(PROJECT_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_DIR, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "username": "admin"})


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request, "username": "admin"})


@app.get("/materials", response_class=HTMLResponse)
async def materials_page(request: Request):
    return templates.TemplateResponse("materials.html", {"request": request, "username": "admin"})


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/photos/{path:path}")
def get_photo(path: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    file_path = os.path.join(project_dir, "photos", path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="照片不存在")
