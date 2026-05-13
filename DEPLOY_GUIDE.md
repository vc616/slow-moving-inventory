# 物料信息采集系统 - 服务器部署指南

## 服务器信息
- 地址: xg.dtro.top
- SSH 端口: 23397
- 用户名: root
- 密码: 160218Cvc

## 部署步骤

### 1. 连接服务器
```bash
ssh -p 23397 root@xg.dtro.top
```
输入密码: 160218Cvc

### 2. 创建项目目录
```bash
mkdir -p /var/www/material-system
mkdir -p /var/www/material-system/photos
mkdir -p /var/www/material-system/data
mkdir -p /var/www/material-system/ssl
```

### 3. 安装系统依赖
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv
```

### 4. 创建 Python 虚拟环境
```bash
cd /var/www/material-system
python3 -m venv venv
source venv/bin/activate
```

### 5. 安装 Python 依赖
```bash
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pydantic python-multipart python-jose passlib bcrypt aiofiles python-dotenv
```

### 6. 上传项目文件

在本地 Windows 电脑上，使用以下命令上传文件：

**使用 SCP 上传整个项目（需要排除 venv 目录）：**
```bash
# 在本地项目目录执行
scp -P 23397 -r app root@xg.dtro.top:/var/www/material-system/
scp -P 23397 -r data root@xg.dtro.top:/var/www/material-system/
scp -P 23397 -r photos root@xg.dtro.top:/var/www/material-system/
scp -P 23397 -r static root@xg.dtro.top:/var/www/material-system/
scp -P 23397 -r templates root@xg.dtro.top:/var/www/material-system/
scp -P 23397 -r ssl root@xg.dtro.top:/var/www/material-system/
scp -P 23397 app.py database.py models.py schemas.py crud.py auth.py __init__.py requirements.txt root@xg.dtro.top:/var/www/material-system/
```

### 7. 配置和启动服务

创建 systemd 服务文件：
```bash
cat > /etc/systemd/system/material-system.service <<EOF
[Unit]
Description=Material Inventory System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/material-system
ExecStart=/var/www/material-system/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8003
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

设置权限：
```bash
chown -R www-data:www-data /var/www/material-system
chmod -R 755 /var/www/material-system
```

启动服务：
```bash
systemctl daemon-reload
systemctl enable material-system
systemctl start material-system
systemctl status material-system
```

### 8. 配置防火墙
```bash
ufw allow 8003/tcp
```

### 9. 访问应用
- 地址: http://xg.dtro.top:8003
- 或使用 Nginx 配置反向代理

## Nginx 反向代理配置（可选）

安装 Nginx：
```bash
apt-get install -y nginx
```

创建 Nginx 配置：
```bash
cat > /etc/nginx/sites-available/material-system <<EOF
server {
    listen 80;
    server_name xg.dtro.top;

    location / {
        proxy_pass http://127.0.0.1:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /photos {
        alias /var/www/material-system/photos;
        autoindex off;
    }
}
EOF
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/material-system /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
ufw allow 80/tcp
```

## 常用命令

### 查看服务状态
```bash
systemctl status material-system
```

### 查看日志
```bash
journalctl -u material-system -f
```

### 重启服务
```bash
systemctl restart material-system
```

### 更新代码后重载
```bash
systemctl restart material-system
```

## 数据备份

定期备份数据库：
```bash
cp /var/www/material-system/data/inventory.db /var/www/material-system/data/inventory.db.backup
```

## 故障排查

1. **服务启动失败**
   - 检查日志: `journalctl -u material-system -e`
   - 验证 Python 依赖是否完整安装
   - 检查端口是否被占用: `netstat -tlnp | grep 8003`

2. **无法访问**
   - 检查防火墙: `ufw status`
   - 检查服务状态: `systemctl status material-system`
   - 检查端口监听: `ss -tlnp | grep 8003`

3. **权限问题**
   - 确保 www-data 用户有权限访问项目目录
   - 检查文件和目录权限

## 快速部署脚本

在服务器上创建并执行：
```bash
cat > /tmp/deploy.sh << 'SCRIPT'
#!/bin/bash

PROJECT_DIR="/var/www/material-system"
cd $PROJECT_DIR

# 停止服务
systemctl stop material-system

# 备份数据库
cp data/inventory.db data/inventory.db.$(date +%Y%m%d).bak

# 重启服务
systemctl start material-system
systemctl status material-system

echo "部署完成!"
SCRIPT

chmod +x /tmp/deploy.sh
/tmp/deploy.sh
```

## 默认账户

- 用户名: admin
- 密码: admin123
