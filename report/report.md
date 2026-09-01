# Online Judge 系统实验报告

## 1. 项目概述

本项目使用 FastAPI、SQLite 和 Streamlit 实现一个小型 Online Judge。当前基础功能包括：

- 用户注册、登录、登出和 Session 身份认证
- `user/admin/banned` 三种角色及管理员权限管理
- Problem 增删改查和日志可见性配置
- Python、C++ 和动态语言配置
- 异步 Submission、查询、分页、限流和重新评测
- AC、WA、TLE、MLE、RE、CE、UNK 分类
- testcase 日志、公开规则和访问审计
- 系统 reset 和初始管理员重建
- Streamlit 用户、题目和 Submission 页面

## 2. 系统架构

后端按以下层次组织：

```text
Router
  ↓
Service
  ↓
Repository
  ↓
SQLite
```

- `app/routers/`：HTTP 路径、参数、依赖和统一响应
- `app/services/`：权限、业务规则、后台评测和状态流转
- `app/repositories/`：参数化 SQL、事务和 schema migration
- `app/models/`：Pydantic 请求、响应及内部结果模型
- `app/judge/`：源码运行、资源监控、输出比较和多 testcase 汇总
- `frontend/app.py`：只通过 REST API 访问后端的 Streamlit 前端

所有 FastAPI 路由均使用 `async def`。

## 3. 数据设计

SQLite 主要数据表包括：

- `users`：用户、角色、密码哈希、提交数和解题数
- `problems`：题目正文、限制、默认字段和 `public_cases`
- `test_cases`：评测输入和标准输出
- `languages`：扩展名、编译命令、运行命令和默认资源限制
- `submissions`：源码、状态、得分和提交级信息
- `judge_logs`：单 testcase 结果、耗时和内存
- `access_logs`：日志访问者、题目、动作、时间和 HTTP 状态
- `audit_logs`：角色修改等管理操作

启动时会执行兼容性 migration，将旧角色和旧 Submission 状态映射到新版枚举，并为已有数据库补充新增列。

## 4. 核心实现

### 4.1 认证和权限

密码使用 bcrypt 哈希。登录后 Session 保存用户 ID，每次受保护请求重新从数据库读取用户，因此用户被改为 `banned` 后，旧 Session 也会立即失去访问权限。

受保护接口使用 FastAPI dependency 先完成认证和权限判断。统一异常响应采用：

```json
{
  "code": 403,
  "msg": "permission denied",
  "data": null
}
```

### 4.2 自动评测

每次 testcase 都创建独立 UUID 临时目录。源码通过 UTF-8 写入，使用 `asyncio.create_subprocess_exec()` 启动，不使用 `eval()`、`exec()` 或 `shell=True`。

Runner 同时监控：

- `time_limit`：超时后终止子进程并产生 TLE
- `memory_limit`：使用 psutil 读取进程及子进程 RSS，超限后产生 MLE
- exit code：非零退出码产生 RE
- UTF-8：无法解码的输出产生 RE
- C++ 编译：g++ 编译失败产生 CE
- Judge 内部异常：产生 UNK

输出比较会统一换行、删除每行末尾空格和文件末尾空行，但保留行首及行内空格。

### 4.3 Submission

创建 Submission 时先保存 `pending` 记录并立即返回 submission ID，再使用 asyncio 后台任务继续评测。

每个 testcase 固定 10 分：

```text
counts = testcase 数量 × 10
score = AC testcase 数量 × 10
```

Submission status 使用 `pending/success/error`，与 testcase result 分开。系统还实现每个用户一分钟最多三次提交、本人/admin 查询和 admin rejudge。

### 4.4 日志权限

Submission 本人和 admin 可以查看 testcase detail。Problem 的 `public_cases=True` 时，其他已登录用户也能查看日志，但仍不能查看不属于自己的 Submission 摘要。

日志 API 只公开：

```text
id / result / time / memory
```

不直接返回服务端路径、标准答案或内部完整输出。规定的成功访问和 403 会写入访问审计。

### 4.5 前端

Streamlit 使用 `requests.Session` 保存后端 Cookie，并集中封装 REST API 请求。页面根据真实 HTTP status、JSON code 和 msg 展示结果，不直接读写 SQLite。

## 5. API 概览

主要 API：

- `/api/users/`、`/api/users/admin`、`/api/users/{user_id}`
- `/api/auth/login`、`/api/auth/logout`
- `/api/problems/`、`/api/problems/{problem_id}`
- `/api/languages/`
- `/api/submissions/`、`/api/submissions/{submission_id}`
- `/api/submissions/{submission_id}/rejudge`
- `/api/submissions/{submission_id}/log`
- `/api/logs/access/`
- `/api/reset/`

完整交互格式可以通过 FastAPI Swagger 查看。

## 6. 测试结果

在 `Miniconda/env/oj_project`、Python 3.12.14 环境运行：

```text
49 passed
0 skipped
```

覆盖六类测试：题目管理、自动评测、用户权限、Submission 状态、日志、持久化/reset。

额外完成：

- `python -m compileall -q app frontend`
- `python -m pip check`
- FastAPI 健康接口和 Swagger 冒烟测试
- Streamlit HTTP 和 AppTest 加载测试
- Python/C++、TLE、MLE、CE 实际子进程测试

尚需在最终提交环境补充：

- Linux/WSL 完整回归
- GCC 9+ 回归；当前 Windows 开发机 g++ 为 8.3
- 最终演示截图

## 7. 问题与解决过程

### 7.1 新旧要求契约冲突

旧实现使用 student/teacher/admin、`message`、422 和旧 Submission 状态。解决方式是先迁移统一响应和角色，再通过 SQLite migration 保留已有数据，最后逐模块改写测试。

### 7.2 Windows 子进程差异

Windows 标准输出使用 CRLF，Runner 保留原始输出，由 Comparator 统一换行。C++ 可执行文件在 Windows 使用 `.exe`，Linux 使用无扩展名文件。

### 7.3 快速内存分配难以采样

极短程序可能在第一次 RSS 采样前退出。测试程序会短暂持有内存，Runner 使用 10 ms 周期监控进程树并记录峰值。

### 7.4 Reset 测试的数据安全

Reset 会清空业务数据。pytest 使用独立临时 SQLite 文件验证该接口，避免清空开发数据库。

## 8. AI 工具使用说明

本项目开发过程中使用了 OpenAI Codex 辅助：

- 对照新旧要求并整理变更清单
- 扫描现有代码与数据库 schema
- 提出分阶段迁移方案
- 辅助编写局部实现和 pytest
- 执行测试、定位失败原因并迭代修正
- 整理 README 和实验报告初稿

工作流为：读取要求和现有实现 → 形成可核对的修改项 → 局部修改 → 专项测试 → 完整回归 → 人工检查差异。

代码提交前仍需项目作者理解、检查和确认所有实现，尤其是权限、动态语言命令、子进程安全、Linux 兼容性及报告描述。本文没有使用 AI 生成的虚假测试结果或虚构截图。

## 9. 总结

当前系统已经形成从用户登录、题目管理、代码提交、异步评测到结果与日志查询的基础闭环，并已完成课程 `api.md` 的字段级核对。后续重点是 Linux/GCC 9+ 环境验证、演示截图，以及按时间决定是否实现 Advance AI 智能命题。
