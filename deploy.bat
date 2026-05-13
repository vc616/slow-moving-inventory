@echo off
chcp 65001 > nul
echo ==========================================
echo 物料信息采集系统 - Windows 一键部署脚本
echo ==========================================
echo.

set SERVER_HOST=xg.dtro.top
set SERVER_PORT=23397
set SERVER_USER=root
set SERVER_PASS=160218Cvc

echo [1/6] 连接到服务器并创建目录...
echo.

:: 创建远程目录
echo 创建项目目录中...
plink -P %SERVER_PORT% %SERVER_USER%@%SERVER_HOST% -pw %SERVER_PASS% "mkdir -p /var/www/material-system/photos /var/www/material-system/data /var/www/material-system/ssl"

echo.
echo [2/6] 上传项目文件...
echo.

:: 上传 app 目录
echo 上传 app 目录...
pscp -P %SERVER_PORT% -r app %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/

:: 上传静态文件目录
echo 上传 static 目录...
pscp -P %SERVER_PORT% -r static %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/

:: 上传模板目录
echo 上传 templates 目录...
pscp -P %SERVER_PORT% -r templates %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/

:: 上传数据目录
echo 上传 data 目录...
pscp -P %SERVER_PORT% -r data %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/

:: 上传 SSL 目录
echo 上传 ssl 目录...
pscp -P %SERVER_PORT% -r ssl %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/

:: 上传根目录的 Python 文件
echo 上传 Python 文件...
pscp -P %SERVER_PORT% app/__init__.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/
pscp -P %SERVER_PORT% app/main.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/
pscp -P %SERVER_PORT% app/models.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/
pscp -P %SERVER_PORT% app/schemas.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/
pscp -P %SERVER_PORT% app/crud.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/
pscp -P %SERVER_PORT% app/auth.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/
pscp -P %SERVER_PORT% app/database.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/

:: 上传路由文件
echo 上传路由文件...
pscp -P %SERVER_PORT% app/routers/__init__.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/routers/
pscp -P %SERVER_PORT% app/routers/materials.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/routers/
pscp -P %SERVER_PORT% app/routers/inventory.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/routers/
pscp -P %SERVER_PORT% app/routers/auth.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/routers/

:: 上传工具文件
echo 上传工具文件...
pscp -P %SERVER_PORT% app/utils/__init__.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/utils/
pscp -P %SERVER_PORT% app/utils/excel_loader.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/utils/
pscp -P %SERVER_PORT% app/utils/file_lock.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/app/utils/

:: 上传根目录文件
echo 上传配置文件...
pscp -P %SERVER_PORT% streamlit_app.py %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/
pscp -P %SERVER_PORT% requirements.txt %SERVER_USER%@%SERVER_HOST%:/var/www/material-system/

echo.
echo [3/6] 安装依赖和配置服务...
echo.

:: 创建安装脚本
plink -P %SERVER_PORT% %SERVER_USER%@%SERVER_HOST% -pw %SERVER_PASS% "cat > /tmp/install.sh << 'ENDSCRIPT'
#!/bin/bash

PROJECT_DIR='/var/www/material-system'
cd $PROJECT_DIR

# 安装系统依赖
apt-get update
apt-get install -y python3 python3-pip python3-venv

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装 Python 依赖
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pydantic python-multipart python-jose passlib bcrypt aiofiles python-dotenv

# 创建 systemd 服务文件
cat > /etc/systemd/system/material-system.service <<EOF
[Unit]
Description=Material Inventory System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8003
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# 启动服务
systemctl daemon-reload
systemctl enable material-system
systemctl start material-system

# 配置防火墙
ufw allow 8003/tcp

echo '安装完成!'
systemctl status material-system
ENDSCRIPT

chmod +x /tmp/install.sh
/tmp/install.sh"

echo.
echo [4/6] 等待服务启动...
timeout /t 5

echo.
echo [5/6] 检查服务状态...
plink -P %SERVER_PORT% %SERVER_USER%@%SERVER_HOST% -pw %SERVER_PASS% "systemctl status material-system"

echo.
echo [6/6] 测试访问...
echo.

:: 测试服务是否响应
curl -s http://localhost:8003/health > nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo 部署成功!
    echo ==========================================
    echo 访问地址: http://xg.dtro.top:8003
    echo 默认账户: admin / admin123
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo 部署完成，请检查服务状态
    echo ==========================================
    echo 手动检查命令:
    echo   systemctl status material-system
    echo   journalctl -u material-system -n 20
    echo ==========================================
)

echo.
pause
