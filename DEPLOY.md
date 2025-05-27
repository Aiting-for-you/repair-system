# 维修计价系统部署说明（Linux服务器从零部署）

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
sudo apt install -y python3 python3-pip git
# 可选：安装虚拟环境工具
sudo apt install -y python3-venv
```

## 2. 获取项目代码

```bash
git clone https://github.com/Aiting-for-you/repair-system.git
cd repair-system
```

## 3. 上传真实维修数据文件

> Windows本地的 schoolRepairItems.ts 需上传到服务器项目根目录

- 推荐用 WinSCP、Xftp、rz/sz 或 scp 命令上传：
  - WinSCP/Xftp：图形界面拖拽即可
  - scp命令（在本地Windows命令行/PowerShell执行）：
    ```bash
    scp E:/维修计价助手/RepairSystem/schoolRepairItems.ts 用户名@服务器IP:/home/用户名/repair-system/
    ```

## 4. 创建并激活虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate
```

## 5. 安装依赖

```bash
pip install -r requirements.txt
```

## 6. 初始化数据库

- 第一次运行后端会自动建表，无需手动操作。

## 7. 导入真实维修项目数据

```bash
python import_school_data.py
```
- 脚本会自动调用后端API，将schoolRepairItems.ts中的数据写入数据库。
- 如需清空原有学校和项目，可先执行：
  ```bash
  curl -X POST http://127.0.0.1:5001/api/dev/clear_schools_and_items
  ```

## 8. 启动后端服务

开发环境：
```bash
python backend/app.py
```
- 默认端口5001，防火墙需放行5001端口

生产环境（推荐gunicorn+nginx）：
```bash
pip install gunicorn
# 启动gunicorn
cd backend
exec gunicorn -w 4 -b 0.0.0.0:5001 app:app
```
- 建议用 supervisor/systemd 守护进程
- 前端静态文件可用nginx代理

## 9. 访问系统

- 用户界面：http://服务器公网IP:5001/static/index.html
- 管理后台：http://服务器公网IP:5001/static/admin.html

## 10. 数据库说明

- 默认使用SQLite，数据库文件为 `instance/repair_system.db`
- 如需MySQL/PostgreSQL，需修改 `backend/app.py` 并安装驱动

## 11. 常见问题

- **端口未开放**：请用 `sudo ufw allow 5001` 或云服务器安全组放行5001端口
- **schoolRepairItems.ts未上传**：请用WinSCP/Xftp/scp上传到项目根目录
- **依赖安装失败**：请检查pip源或网络，或用 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
- **静态文件404**：请访问 `/static/index.html`、`/static/admin.html`
- **图片/Excel导出失败**：请确保 `uploads/` 目录有写权限

## 12. 生产部署建议

- gunicorn/uwsgi+nginx反向代理
- supervisor/systemd守护gunicorn进程
- 定期备份 `instance/repair_system.db`
- 关闭调试模式（`debug=False`）

---
如有疑问请联系开发者或提交 issue。 