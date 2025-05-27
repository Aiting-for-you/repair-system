# 维修计价系统部署说明（Linux服务器，无需反向代理，含守护进程自启动）

## 1. 服务器环境准备

### 1.1 系统要求
- 推荐操作系统：Ubuntu 20.04+/CentOS 7+/Debian 10+
- Python 3.8 及以上
- 建议2G内存及以上

### 1.2 安装基础软件

```bash
# 更新包管理器
sudo apt update
# 安装Python3、pip3、git
sudo apt install -y python3 python3-pip git python3-venv
```

## 2. 获取项目代码

```bash
git clone https://github.com/Aiting-for-you/repair-system.git
cd repair-system
```

> schoolRepairItems.ts 已包含在仓库中，无需手动上传。

## 3. 创建并激活虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. 安装依赖

```bash
pip install -r requirements.txt
```

## 5. 初始化数据库

- 第一次运行后端会自动建表，无需手动操作。

## 6. 导入真实维修项目数据

```bash
python import_school_data.py
```
- 脚本会自动调用后端API，将schoolRepairItems.ts中的数据写入数据库。
- 如需清空原有学校和项目，可先执行：
  ```bash
  curl -X POST http://127.0.0.1:5001/api/dev/clear_schools_and_items
  ```

## 7. 使用 systemd 守护进程实现开机自启

### 7.1 创建 systemd 服务文件

假设项目路径为 `/home/youruser/repair-system`，Python虚拟环境为 `venv`，请根据实际路径修改：

```bash
sudo nano /etc/systemd/system/repairsystem.service
```

内容如下（请根据实际用户名和路径调整）：

```
[Unit]
Description=Repair System Flask Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/repair-system
ExecStart=/home/youruser/repair-system/venv/bin/python backend/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 7.2 启用并启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable repairsystem
sudo systemctl start repairsystem
```

### 7.3 查看服务状态和日志

```bash
sudo systemctl status repairsystem
sudo journalctl -u repairsystem -f
```

## 8. 访问系统

- 用户界面：http://服务器公网IP:5001/static/index.html
- 管理后台：http://服务器公网IP:5001/static/admin.html

## 9. 数据库说明

- 默认使用SQLite，数据库文件为 `instance/repair_system.db`
- 如需MySQL/PostgreSQL，需修改 `backend/app.py` 并安装驱动

## 10. 常见问题

- **端口未开放**：请用 `sudo ufw allow 5001` 或云服务器安全组放行5001端口
- **依赖安装失败**：请检查pip源或网络，或用 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
- **静态文件404**：请访问 `/static/index.html`、`/static/admin.html`
- **图片/Excel导出失败**：请确保 `uploads/` 目录有写权限

## 11. 生产部署建议

- 使用 systemd 守护进程，保证服务自动重启和开机自启
- 定期备份 `instance/repair_system.db`
- 关闭调试模式（`debug=False`）

---
如有疑问请联系开发者或提交 issue。 