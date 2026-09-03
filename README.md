# Online Judge

基于 FastAPI、SQLite 和 Streamlit 的课程 OJ 项目，支持用户与权限、Problem 管理、Python/C++ 评测、Submission、测试点日志和访问审计。

## 环境

- Python 3.10 或以上（当前开发环境为 Python 3.12）
- GCC 9 或以上，支持 C++14
- Windows 建议同时在 WSL/Linux 中进行最终回归

可以使用 venv 或 Conda。当前开发环境名称为 `oj_project`：

```powershell
conda activate oj_project
python -m pip install -r requirements.txt
```

Ubuntu/WSL 安装 C++ 编译器：

```bash
sudo apt update
sudo apt install -y g++
g++ --version
```

## 配置

建议在启动前设置随机 Session 密钥：

```powershell
$env:OJ_SESSION_SECRET = "replace-with-a-random-secret"
```

后端还支持：

- `OJ_INITIAL_ADMIN_USERNAME`
- `OJ_INITIAL_ADMIN_PASSWORD`

课程测试使用的初始管理员默认为：

```text
username: admin
password: admintestpassword
```

密码会以 bcrypt 哈希保存，不会明文写入数据库。

## 启动后端

在项目根目录运行：

```powershell
python -m uvicorn app.main:app --reload
```

Swagger：<http://127.0.0.1:8000/docs>

## 启动前端

保持后端运行，再打开另一个终端：

```powershell
python -m streamlit run frontend/app.py
```

前端默认访问 `http://127.0.0.1:8000`。需要修改时设置：

```powershell
$env:OJ_API_URL = "http://127.0.0.1:8000"
```

前端只通过 REST API 访问数据，不直接读写 SQLite。

## 自动化测试

```powershell
python -m pytest
```

测试覆盖题目管理、自动评测、用户权限、Submission 状态、日志和持久化/reset。Reset 测试使用 pytest 临时数据库，不会清空开发数据库。

## 运行数据

- SQLite：`data/oj.db`
- Judge 临时目录：`temp/`
- 以上运行文件均由 `.gitignore` 排除

`POST /api/reset/` 会清空系统业务数据、退出当前 Session，并重新创建初始管理员。请勿在需要保留数据的环境中误调用。

## 安全说明

- 不在代码中使用 `eval()` 或 `exec()` 执行提交代码
- 评测使用独立进程组，按完整进程树执行时间限制、内存监控和退出清理
- 动态语言命令使用参数列表执行，不通过 shell 拼接
- 不要提交 `.env`、真实 Session secret 或模型 API key
- 当前基础评测并非 Docker 沙箱，不应直接暴露到不可信公网
- 当前没有网络和文件系统隔离；生产环境应使用低权限 Judge 账户、
  禁用网络的容器、只读根文件系统及仅挂载单次评测临时目录
