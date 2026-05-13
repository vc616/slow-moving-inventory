#!/bin/bash

# 物料信息采集系统 - 服务器部署脚本

echo "=========================================="
echo "物料信息采集系统 - 服务器部署脚本"
echo "=========================================="

# 服务器配置
SERVER_HOST="xg.dtro.top"
SERVER_PORT="23397"
PROJECT_DIR="/var/www/material-system"
APP_DIR="$PROJECT_DIR/app"
PHOTOS_DIR="$PROJECT_DIR/photos"

# 1. 创建项目目录
echo "[1/7] 创建项目目录..."
ssh -p $SERVER_PORT root@$SERVER_HOST "mkdir -p $PROJECT_DIR && mkdir -p $PHOTOS_DIR"

# 2. 安装系统依赖
echo "[2/7] 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# 3. 创建虚拟环境
echo "[3/7] 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 4. 安装 Python 依赖
echo "[4/7] 安装 Python 依赖..."
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pydantic python-multipart python-jose passlib bcrypt aiofiles

# 5. 创建 systemd 服务文件
echo "[5/7] 创建系统服务..."
sudo tee /etc/systemd/system/material-system.service > /dev/null <<EOF
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

# 6. 设置权限
echo "[6/7] 设置文件权限..."
sudo chown -R www-data:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR

# 7. 启动服务
echo "[7/7] 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable material-system
sudo systemctl start material-system

echo ""
echo "=========================================="
echo "部署完成!"
echo "=========================================="
echo "服务状态: sudo systemctl status material-system"
echo "日志查看: sudo journalctl -u material-system -f"
echo "访问地址: http://xg.dtro.top:8003"
echo "=========================================="
