# 物料信息采集系统

用于呆滞物料盘库信息采集，支持物料查询、状态评估、照片上传。

## 功能特性

- 🔍 **物料查询** - 支持按编码、名称、规格型号关键字搜索
- 📊 **状态评估** - 5分制评分体系（全新可使用到建议报废）
- 📷 **照片管理** - 支持手机拍照或本地图片上传，每个物料最多10张
- 👤 **用户认证** - 用户名密码登录，支持多用户并发操作
- 📱 **移动端适配** - 响应式设计，手机浏览器直接使用

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI (异步支持，高并发) |
| 数据库 | SQLite |
| 前端 | Jinja2 模板 + 原生 JavaScript |
| 认证 | JWT Token |

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

**Windows:**
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**或使用 8001 端口（如果 8000 被占用）:**
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

启动后访问:
- 前端页面: http://localhost:8000
- API文档: http://localhost:8000/docs

### 3. 默认账户

- 用户名: `admin`
- 密码: `admin123`

## 使用流程

### 首次使用

1. 使用管理员账户登录
2. 进入「数据导入」页面，点击「从Excel导入物料数据」
3. 系统将自动读取 `物料总表.xlsx` 中的物料信息

### 盘库操作

1. 在「物料查询」页面搜索要盘库的物料
2. 点击「选择」进入盘库页面
3. 选择物料状态评分（1-5分）
4. 点击「提交评分」保存
5. 使用手机拍照或选择本地图片上传
6. 照片自动关联到当前物料

## 评分标准

| 分数 | 状态 |
|------|------|
| 5分 | 全新可使用 |
| 4分 | 99新，需要翻新 |
| 3分 | 外观性能尚可 |
| 2分 | 仅作为备件或拆机件使用 |
| 1分 | 建议报废 |

## 并发控制

系统采用以下机制保证数据一致性:

- **文件锁** - 同一物料的照片上传串行化
- **SQLite WAL模式** - 支持读并发
- **请求限流** - 防止短时间内重复提交

## 部署外网访问

### 使用内网穿透

```bash
# 使用ngrok
ngrok http 8000

# 或使用frp等工具
```

### 使用反向代理

推荐使用 Nginx 反向代理到 8000 端口。

## 目录结构

```
呆滞物料信息系统/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 应用入口
│   ├── database.py       # 数据库配置
│   ├── models.py         # 数据模型
│   ├── schemas.py        # Pydantic 模式
│   ├── crud.py          # 数据库操作
│   ├── auth.py          # 认证逻辑
│   ├── routers/
│   │   ├── auth.py       # 认证API
│   │   ├── materials.py  # 物料API
│   │   ├── inventory.py  # 盘库API
│   │   └── stats.py      # 统计API
│   └── utils/
│       ├── file_lock.py  # 文件锁
│       └── excel_loader.py # Excel导入
├── templates/            # Jinja2 模板
│   ├── base.html        # 基础模板
│   ├── index.html       # 主页/物料详情
│   ├── materials.html   # 物料列表
│   └── stats.html       # 分类统计
├── static/              # 静态资源
│   ├── css/style.css    # 样式
│   └── js/main.js       # 前端脚本
├── photos/              # 照片存储
├── data/                # 数据库存储
├── requirements.txt     # 依赖列表
└── CLAUDE.md            # 项目指南
```

## 数据备份

数据库文件: `data/inventory.db`
照片目录: `photos/`

定期备份这两个位置即可完整保存所有数据。
