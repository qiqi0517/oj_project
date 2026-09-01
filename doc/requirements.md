# OJ 系统更新版作业要求

> 来源：`https://dbg-course.github.io/python-docs/oj/`  
> 整理日期：2026-09-01  
> 说明：本文**仅依据 DBG-Course 当前 OJ 文档**整理，不使用 `keg-course.github.io` 或旧 PDF 补充内容。
>
> 为避免网页内容与实现要求混淆，本文尽量保留 DBG 文档中的模块结构、API 路径、字段名、权限、状态码和评分口径；说明性段落采用转述方式整理。

---

# 1. 文档导航与项目结构

当前 DBG-Course OJ 文档包含：

## 1.1 实验概述

- 实验目标
- 技术要求
- 基础模块（30 分）
- 进阶模块（10 分）
- API 文档
- 评分标准
- 学习资源

## 1.2 实验内容

- Step1：题目管理
- Step2：题目评测
- Step3：评测列表
- Step4：用户管理
- Step5：日志与权限
- Step6：前端交互
- Advance：AI 智能命题

## 1.3 其他页面

- API 文档
- 评分标准
- FAQ
- 仓库拉取教程

---

# 2. 实验概述

## 2.1 实验目标

需要构建一个小型但功能完整的 Online Judge（OJ）系统。

开发过程分阶段完成，目标是掌握：

- 系统设计
- API 开发
- 异步评测
- 权限控制
- 前后端交互
- 多语言程序运行
- 资源限制
- 评测日志
- AI 应用开发（进阶）

Advance 模块在基础 OJ 之上增加大语言模型相关能力。

---

## 2.2 FastAPI 与异步要求

所有 API 必须使用 FastAPI 的异步接口：

```python
async def ...
```

该要求是硬性评分前提。

如果没有正确使用 FastAPI 异步接口，则无法获得本次作业的功能分。

---

## 2.3 项目规模

课程说明预计项目代码量在约两千行规模。

需要合理：

- 规划开发周期
- 做模块划分
- 管理 Git 历史
- 避免把全部代码写进少量大文件

---

## 2.4 Git 提交规范

要求按照 Conventional Commits 风格编写 Git 提交信息。

常见类型：

```text
feat
fix
docs
test
refactor
chore
```

示例形式：

```text
feat: add problem api
fix: handle timeout process
test: add submission tests
docs: update readme
```

不规范提交会酌情扣代码规范分。

---

# 3. 总体评分结构

总分：

```text
50 分
```

其中：

```text
实验功能：40 分
代码规范：5 分
实验报告：5 分
```

最终按课程总评：

```text
30%
```

折算。

---

# 4. 基础模块：共 30 分

| Step | 名称 | 核心内容 | 分值 |
|---|---|---|---:|
| Step 1 | 题目管理 | 配置加载、校验、增删改查 | 5 |
| Step 2 | 评测控制 | 程序执行、资源限制、输出比较、多语言 | 5 |
| Step 3 | 评测管理 | 提交查询、状态管理、重新评测 | 5 |
| Step 4 | 用户管理 | 注册、登录、权限、用户信息 | 5 |
| Step 5 | 评测日志 | testcase 明细、可见性、访问审计 | 5 |
| Step 6 | 前端交互 | 用户、题目、提交页面及后端 API 对接 | 5 |

---

# 5. Advance：AI 智能命题，共 10 分

唯一进阶模块为：

```text
AI 智能命题
```

核心评分点：

- R1 出题交互界面
- R2 自定义模型配置
- R3 实时进度与中断
- R4 Token 用量与价格
- 题目合理性
- 测试用例有效性
- 功能易用性

---

# 6. 全局 API 响应规范

## 6.1 基本响应格式

成功响应应使用统一 JSON 结构，例如：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

错误响应类似：

```json
{
  "code": 404,
  "msg": "problem not found",
  "data": null
}
```

必须保证：

```text
JSON.code == 实际 HTTP status code
```

不能统一返回 HTTP 200 后只修改 JSON 内的 code。

---

# 7. 全局 HTTP 状态码

| HTTP | 含义 | 典型场景 |
|---:|---|---|
| 200 | 正常 | 请求成功 |
| 400 | 参数错误 | 缺少参数、字段格式错误 |
| 401 | 未登录/认证失败 | 无 Session、登录失败 |
| 403 | 权限不足或禁用 | banned、非管理员操作管理员接口 |
| 404 | 资源不存在 | Problem/Submission/User 不存在 |
| 409 | 状态或资源冲突 | id 已存在、任务已经结束 |
| 429 | 请求频率超限 | 1 分钟提交超过 3 次 |
| 500 | 服务器异常 | 未知内部错误 |

---

# 8. 异常检查优先级

API 文档明确要求异常检查顺序：

```text
401 > 403 > 400 > 429 > 409 > 404 > 500
```

因此设计受保护接口时，应先完成身份与权限判断，再处理普通请求校验。

这会影响 FastAPI/Pydantic 的默认 422 行为。

---

# 9. FastAPI 422 与课程要求的 400

FastAPI 默认可能在进入 Router 业务代码前返回：

```text
422 Unprocessable Entity
```

但当前 API 文档对参数错误要求：

```text
400
```

FAQ 给出两类解决思路：

## 9.1 用 Depends 让认证优先

可以让：

```python
Depends(get_current_user)
```

先执行。

之后再手动解析请求体并构造 Pydantic Model。

这样可以避免：

```text
422 抢在 401/403 前面
```

## 9.2 自定义 RequestValidationError Handler

可以注册：

```python
@app.exception_handler(RequestValidationError)
async def ...
```

将 Pydantic 验证错误统一转成：

```text
HTTP 400
```

具体返回 JSON 仍应符合项目统一：

```text
code / msg / data
```

---

# 10. 系统初始管理员

系统启动时自动创建：

```text
username = admin
password = admintestpassword
```

密码仍应经过安全哈希后存储。

---

# 11. Step1：题目管理

## 11.1 模块目标

实现题目配置的：

- 加载
- 创建
- 编辑
- 删除
- 列表查询
- 单题详情

形成完整题目管理闭环。

---

# 12. Step1 推荐存储形式

文档建议可以把题目配置放在本地目录中：

```text
problems/
```

每道题保存一个 JSON。

这只是推荐方案；如果使用数据库，也需要保持 API 行为一致。

---

# 13. Problem 必选字段

Problem 至少需要：

```text
id
title
description
input_description
output_description
samples
constraints
testcases
```

含义：

## 13.1 id

题目唯一标识，例如：

```text
P1001
sum_2
```

## 13.2 title

题目标题。

## 13.3 description

题目正文。

## 13.4 input_description

输入格式描述。

## 13.5 output_description

输出格式描述。

## 13.6 samples

公开样例列表。

每项：

```json
{
  "input": "...",
  "output": "..."
}
```

## 13.7 constraints

数据范围和限制条件。

## 13.8 testcases

实际评测测试点。

每项基本结构：

```json
{
  "input": "...",
  "output": "..."
}
```

---

# 14. Problem 可选字段

```text
hint
source
tags
time_limit
memory_limit
author
difficulty
```

其中：

```text
time_limit 默认 3 秒
memory_limit 默认 128 MB
```

查询 Problem 时，如果可选字段未设置，需要返回该类型的合理默认值，例如：

```text
str  → ""
list → []
```

---

# 15. Step1 API：题目列表

```text
GET /api/problems/
```

权限：

```text
所有已登录用户
```

返回题目摘要列表。

每项至少包括：

```text
id
title
```

---

# 16. Step1 API：添加题目

```text
POST /api/problems/
```

权限：

```text
所有已登录用户
```

需要提交完整题目字段。

成功：

```text
HTTP 200
```

返回新题目的 id。

异常：

```text
400 字段缺失/格式错误
401 未登录
409 id 已存在
```

---

# 17. Step1 API：编辑题目

```text
PUT /api/problems/{problem_id}
```

权限：

```text
所有已登录用户
```

请求体字段和创建 Problem 相同。

额外规则：

```text
body.id 必须与 URL 的 problem_id 一致
```

否则：

```text
400
```

需要对更新后的完整 Problem 重新校验。

题目不存在：

```text
404
```

---

# 18. Step1 API：删除题目

```text
DELETE /api/problems/{problem_id}
```

权限：

```text
仅管理员
```

需要检查：

```text
401 未登录
403 非管理员
404 题目不存在
```

---

# 19. Step1 API：题目详情

```text
GET /api/problems/{problem_id}
```

权限：

```text
所有已登录用户
```

返回完整题目配置，包括：

```text
testcases
```

当前 DBG 文档并没有旧 PDF 中“普通学生必须隐藏 test_cases”的规则。

注意：Step5 的日志可见性是另一套规则，不应与 Problem API 混淆。

---

# 20. Step1 权限补充

Step4 用户系统完成后，需要回头更新 Step1～Step3 权限。

课程为简化规定：

```text
题目上传：任意已登录用户
创建语言：任意已登录用户
删除题目：仅管理员
删除语言：暂不要求
```

此外，用户未登录时不能进行这些受保护的增删查改操作。

---

# 21. Step1 评分

| 功能 | 分值 |
|---|---:|
| 题目列表 / 详情 | 3 |
| 题目增删改 | 2 |
| 合计 | 5 |

---

# 22. Step2：题目评测

## 22.1 模块目标

从题库读取题目，接收用户代码，自动执行、比较输出并返回结构化评测结果。

至少支持：

```text
Python
```

同时基础模块要求扩展：

```text
C++
```

---

# 23. Step2 版本建议

```text
Python：建议 3.10
C++：GCC 9+，C++14
```

---

# 24. 输入输出规范

评测必须严格处理输出。

允许：

- 输出末尾换行
- 每一行末尾额外空格
- 最后一行多余换行

不能忽略：

- 额外提示语
- 实际内容差异
- 与标准答案不匹配的文本

例如输出：

```text
请输入：3
```

不能因为其中包含 `3` 就判为正确。

---

# 25. testcase Result

测试点结果需要支持：

```text
AC
WA
TLE
MLE
RE
CE
UNK
```

含义：

| 状态 | 含义 |
|---|---|
| AC | 正确 |
| WA | 输出错误 |
| TLE | 超时 |
| MLE | 内存超限 |
| RE | 运行时错误 |
| CE | 编译错误 |
| UNK | 其他未归类错误 |

文档说明：

非 AC～CE 这些明确类别的错误可以统一归到：

```text
UNK
```

---

# 26. Submission 状态

一次评测任务的状态和单 testcase 结果是两个概念。

Submission 状态只有：

```text
pending
success
error
```

含义：

```text
pending：评测还在进行
success：评测流程正常完成
error：评测流程本身发生问题
```

不要把：

```text
AC / WA / TLE / ...
```

存入 Submission status 字段。

---

# 27. Python Judge

基本步骤：

```text
保存用户源码
↓
创建独立程序运行
↓
向 stdin 输入 testcase
↓
捕获 stdout / stderr
↓
应用 time/memory 限制
↓
输出比较
↓
生成 testcase result
```

要求异步评测。

文档建议可以使用：

```python
asyncio.create_task(...)
```

只要求支持单用户任务即可，不要求实现高并发评测系统。

---

# 28. C++ Judge

基础 Step2 额外要求：

```text
C++
```

流程：

```text
写 .cpp
↓
调用 g++ 编译
↓
编译失败 → CE
↓
编译成功
↓
运行可执行文件
↓
进行 testcase 评测
```

语言选择必须由：

```text
language
```

字段控制。

---

# 29. 动态注册语言

接口：

```text
POST /api/languages/
```

权限：

```text
所有已登录用户
```

字段：

```text
name
file_ext
compile_cmd
run_cmd
time_limit
memory_limit
```

其中：

```text
name          必填
file_ext      必填
compile_cmd   可选
run_cmd       必填
time_limit    可选
memory_limit  可选
```

异常：

```text
400
401
403
```

---

# 30. 动态语言命令模板

C++ 可类似：

```text
file_ext = .cpp
compile_cmd = g++ {src} -o {exe}
run_cmd = {exe}
```

Python 可类似：

```text
file_ext = .py
compile_cmd = null
run_cmd = python3 {src}
```

文档提醒：

```text
{src}
{exe}
```

展开后应当是有效路径，而不是随意字符串。

---

# 31. 查询语言列表

```text
GET /api/languages/
```

返回当前支持语言名称。

示例语义：

```json
{
  "name": ["python", "cpp"]
}
```

---

# 32. time_limit 与 memory_limit

每道 Problem 可以配置：

```text
time_limit
memory_limit
```

如果 Problem 没有配置：

```text
使用 Language 配置中的默认值
```

运行时必须监控：

```text
运行时间
内存占用
```

超出后：

```text
TLE
MLE
```

并终止程序。

---

# 33. 内存监控建议

文档/FAQ 给出的可选技术包括：

- `resource`
- `subprocess`
- Linux `ulimit`
- `psutil`
- 单独线程定期检查 RSS

一种推荐思路：

```text
启动 subprocess
↓
线程周期读取进程 RSS
↓
超过 memory_limit → kill → MLE
```

主逻辑同时负责：

```text
timeout → TLE
```

---

# 34. testcase 计分

当前规则：

```text
每个 testcase 10 分
```

所以：

```text
counts = testcase 总数 × 10
score = AC testcase 数量 × 10
```

Step2/Step3 结果接口只需要返回总分等摘要。

单 testcase 的：

```text
result
time
memory
```

留给 Step5 日志接口。

---

# 35. Step2 评分

| 功能 | 分值 |
|---|---:|
| 多语言评测 | 2 |
| 动态语言注册 | 1 |
| 查询语言列表 | 1 |
| 时间 / 内存限制 | 1 |
| 合计 | 5 |

---

# 36. Step3：评测列表 / 评测管理

## 36.1 模块目标

实现：

- 创建提交
- 查询评测列表
- 查询单评测详情
- 分页
- 筛选
- 权限
- 重新评测

---

# 37. 提交评测接口

```text
POST /api/submissions/
```

权限：

```text
登录用户
```

参数：

```text
problem_id
language
code
```

成功后立即返回：

```text
submission_id
status = pending
```

成功状态码：

```text
HTTP 200
```

异常：

```text
400 参数错误
401 未登录
403 权限不足
404 problem / language 不存在
429 提交频率超限
```

---

# 38. 提交频率限制

API 文档明确给出的示例要求：

```text
1 分钟内提交超过 3 次 → 429
```

实现 Submission API 时需要纳入频率控制。

---

# 39. 查询单个 Submission

```text
GET /api/submissions/{submission_id}
```

权限：

```text
提交本人
或
管理员
```

完成状态下主要返回：

```text
submission_id
status
score
counts
compile_info
run_info
error_info
```

---

# 40. compile_info

用于描述：

```text
编译是否成功
编译器信息
```

对于 Python 等解释型语言：

```text
compile_info 可以是 null
```

---

# 41. run_info

用于描述整个程序运行阶段的总体状态。

具体 testcase 结果不放这里，而通过：

```text
Step5 log API
```

查看。

---

# 42. error_info

用于提交级别错误信息。

不能泄露：

- 服务端绝对路径
- 密钥
- 其他敏感运行信息

---

# 43. pending Submission 响应

当 status 为：

```text
pending
```

至少需要返回：

```text
submission_id
status
```

其他尚未产生的字段可以：

```text
null
```

---

# 44. 查询 Submission 列表

```text
GET /api/submissions/
```

参数：

```text
user_id
problem_id
status
page
page_size
```

全部可选，但有特殊规则。

---

# 45. 一级筛选条件

```text
user_id
problem_id
```

属于一级条件。

规则：

```text
不能两者都为空
```

其他参数是二级条件。

---

# 46. Submission 分页语义

## 46.1 page 和 page_size 都为空

表示：

```text
返回全部匹配记录
```

## 46.2 page 为空、page_size 非空

表示：

```text
默认第一页
```

## 46.3 page 非空、page_size 为空

视为：

```text
400 参数错误
```

---

# 47. Submission 列表权限

普通用户：

```text
只能查询自己的 submission
```

管理员：

```text
可查询任意用户
```

如果没有给 `user_id`：

- admin：可以看指定 Problem 的所有用户提交
- 普通用户：只能看该 Problem 下自己的提交

---

# 48. Submission 列表返回

返回：

```text
total
submissions
```

对于：

```text
pending
error
```

列表项只要求：

```text
submission_id
status
```

对于：

```text
success
```

可返回：

```text
submission_id
status
score
counts
```

---

# 49. 重新评测

```text
PUT /api/submissions/{submission_id}/rejudge
```

权限：

```text
仅管理员
```

规则：

```text
复用原 submission_id
覆盖原评测内容
重新设为 pending
```

异常：

```text
401
403
404
```

---

# 50. Step3 评分

| 功能 | 分值 |
|---|---:|
| 评测列表 | 2 |
| 单评测详情 | 2 |
| 重新评测 | 1 |
| 合计 | 5 |

---

# 51. Step4：用户管理

## 51.1 模块目标

实现：

- 登录
- 登出
- 初始管理员
- 注册
- 用户详情
- 权限变更
- 用户列表
- Session
- 密码安全

---

# 52. Session 机制

课程要求采用 Cookie + Session 维护身份。

核心概念：

```text
客户端 Cookie 保存 Session ID
服务器保存 Session 对应身份状态
```

Session ID 需要：

- 足够随机
- 不易预测
- 可唯一标识一次会话

文档建议：

```python
uuid.uuid4()
```

---

# 53. Session 存储

页面介绍的可选存储形式：

- 内存
- 文件
- 数据库
- Redis

需要理解：

- 内存简单，但服务重启丢失
- 文件可持久化，但并发弱
- 数据库可靠
- Redis 常用于高性能 Session

---

# 54. Session 安全

需要考虑：

- Session ID 随机性
- Cookie 安全
- 过期策略
- 登出时清理 Session
- 防止用户继续使用已失效 Session

---

# 55. Starlette SessionMiddleware

文档示例采用：

```python
from starlette.middleware.sessions import SessionMiddleware
```

应用中：

```python
app.add_middleware(
    SessionMiddleware,
    secret_key=...
)
```

登录后可以：

```python
request.session["user_id"] = ...
```

---

# 56. 用户注册

```text
POST /api/users/
```

字段：

```text
username
password
```

验证：

```text
username 长度 3～40
password 至少 6 位
username 必须唯一
password 使用 bcrypt hash 保存
```

注册普通用户角色：

```text
user
```

---

# 57. 注册返回 User 信息

主要字段：

```text
user_id
username
join_time
role
submit_count
resolve_count
```

---

# 58. submit_count

含义：

```text
提交次数
```

同一道 Problem 可以多次贡献。

---

# 59. resolve_count

含义：

```text
通过的不同 Problem 数
```

同一道 Problem 最多贡献一次。

---

# 60. 用户登录

```text
POST /api/auth/login
```

参数：

```text
username
password
```

成功返回：

```text
user_id
username
role
```

异常：

```text
400 参数错误
401 用户名或密码错误
403 banned
```

---

# 61. 用户登出

```text
POST /api/auth/logout
```

权限：

```text
已登录用户
```

成功：

```text
HTTP 200
data = null
```

未登录：

```text
401
```

登出必须清除对应 Session 状态。

---

# 62. 创建管理员

```text
POST /api/users/admin
```

权限：

```text
仅管理员
```

参数：

```text
username
password
```

成功后创建新的 admin 用户。

异常：

```text
400 username 已存在/参数错误
401
403
```

---

# 63. User Role

当前 DBG 文档使用：

```text
user
admin
banned
```

---

# 64. banned

当用户变为：

```text
banned
```

再次登录应被阻止：

```text
403
```

实现受保护接口时也应进行合理身份/权限校验。

---

# 65. 查询 User

```text
GET /api/users/{user_id}
```

权限：

```text
用户本人
或
管理员
```

返回信息不包含密码。

异常：

```text
401
403
404
```

---

# 66. 修改角色

```text
PUT /api/users/{user_id}/role
```

权限：

```text
仅管理员
```

参数：

```text
role
```

合法值：

```text
user
admin
banned
```

异常：

```text
400
401
403
404
```

---

# 67. 权限修改审计

Step4 页面明确要求权限修改时记录：

```text
谁
何时
修改了谁
修改成什么角色
```

该记录应作为操作日志的一部分。

---

# 68. 用户列表

```text
GET /api/users/
```

权限：

```text
仅管理员
```

参数：

```text
page
page_size
```

分页语义与：

```text
GET /api/submissions/
```

保持一致。

返回：

```text
total
users
```

每个 User 至少展示：

```text
user_id
username
role
join_time
submit_count
resolve_count
```

---

# 69. join_time 格式

Step4 示例使用：

```text
YYYY-MM-DD
```

例如：

```text
2026-09-01
```

---

# 70. Step4 评分

| 功能 | 分值 |
|---|---:|
| 用户注册 | 2 |
| 用户信息查询 | 1 |
| 用户权限变更 | 1 |
| 用户列表 | 1 |
| 合计 | 5 |

---

# 71. Step5：日志与权限

## 71.1 模块目标

实现：

- 评测日志
- testcase 明细
- 按 submission 查询
- 日志可见性
- 访问审计

---

# 72. Testcase Detail

Step5/FAQ 将单测试点详情表示为：

```text
id
result
time
memory
```

例如：

```json
{
  "id": 1,
  "result": "AC",
  "time": 1.01,
  "memory": 130
}
```

多个测试点组成：

```text
details
```

---

# 73. 查询评测日志

```text
GET /api/submissions/{submission_id}/log
```

返回：

```text
details
score
counts
```

---

# 74. 默认日志权限

普通用户：

```text
只能查看自己的评测日志
```

管理员：

```text
可以查看所有日志
```

---

# 75. public_cases

Problem 可以设置：

```text
public_cases: bool
```

默认：

```text
False
```

如果设置为：

```text
True
```

则其他已登录用户也能查看对应 Submission 的 testcase details。

---

# 76. 日志公开与 Submission 摘要权限的区别

文档特别说明：

即使日志被公开：

```text
其他用户可以看该评测的日志
```

但没有权限的用户仍然不能通过 Step2/Step3 的 Submission 查询接口查看该 Submission 的简单结果。

因此：

```text
Submission 可见性
```

和：

```text
Log 可见性
```

要分开实现。

---

# 77. 配置日志可见性

```text
PUT /api/problems/{problem_id}/log_visibility
```

权限：

```text
仅管理员
```

参数：

```text
public_cases
```

默认：

```text
False
```

异常：

```text
400
401
403
404
```

---

# 78. 日志访问审计

```text
GET /api/logs/access/
```

权限：

```text
仅管理员
```

筛选参数：

```text
user_id
problem_id
page
page_size
```

分页含义与 Submission 列表一致。

---

# 79. Access Log 字段

审计记录包含：

```text
user_id
problem_id
action
time
status
```

其中：

```text
status
```

表示这次访问返回的状态，例如：

```text
200
403
```

---

# 80. Access Log action

API 页面正文写：

```text
action 只有 view_logs
```

示例记录中使用：

```text
view_log
```

实现时建议参考自动测试/API 最新要求保持一致，并避免自行扩展不必要的枚举。

---

# 81. 哪些情况不记录访问审计

当前文档明确说不必记录：

- 未登录访问
- Submission 不存在
- 参数错误

---

# 82. Step5 评分

| 功能 | 分值 |
|---|---:|
| 日志记录与查询 | 2 |
| 日志 / testcase 权限 | 2 |
| 审计与安全 | 1 |
| 合计 | 5 |

---

# 83. Step6：前端交互

## 83.1 Step6 是基础模块

当前 DBG 文档和 FAQ 都明确：

```text
Step6 前端交互属于基础模块
```

必须完成。

不是选做。

---

# 84. 前端技术

要求使用：

```text
Streamlit
```

无需掌握：

- JavaScript
- HTML
- CSS

启动示例：

```bash
streamlit run app.py
```

---

# 85. 前端原则

前端只通过：

```text
REST API
```

访问后端。

禁止：

- 直接读写后端数据库
- 绕过 FastAPI Service
- 在前端写死假题目或假结果
- 只在前端模拟操作成功

---

# 86. 用户页面组

至少包含：

- 用户注册
- 登录
- 登出
- 用户信息展示
- 用户管理

要求：

- 登录后才能进行需要认证的操作
- 管理员页面按后端权限决定是否可用
- 处理 banned
- 处理未登录
- 处理 403

---

# 87. 前端 Session

需要维护登录状态。

文档提到：

```text
session_state
```

可以用于 Streamlit 页面状态。

所有身份依据仍以：

```text
后端 Session / API 响应
```

为准。

不能在前端硬编码用户身份。

---

# 88. 题目页面组

至少包含：

- Problem 列表
- Problem 详情
- 新增 Problem
- 编辑 Problem
- 删除 Problem

表单应覆盖 Problem 所需字段。

删除操作必须遵守：

```text
admin only
```

---

# 89. 评测与提交页面组

至少包含：

- 代码提交
- Submission 列表
- Submission 详情
- 评测状态
- compile_info
- run_info
- error_info

---

# 90. 代码提交表单

至少提供：

```text
problem_id
language
code
```

提交后调用：

```text
POST /api/submissions/
```

获取：

```text
submission_id
```

---

# 91. 评测状态更新

前端可以：

- 轮询
- 手动刷新

查询：

```text
submission_id
```

评测状态。

需要清楚展示：

- pending
- success
- error
- 编译失败
- RE
- TLE
- MLE
- 其他允许展示的信息

---

# 92. API 调用封装

Step6 推荐集中封装统一 API client，用于：

- 请求
- Cookie/Session
- 异常处理
- HTTP status
- JSON code
- msg

---

# 93. 前端错误处理

页面应根据：

```text
真实 HTTP status
JSON.code
JSON.msg
```

显示失败原因。

页面状态必须与后端数据一致。

---

# 94. Step6 FAQ 最低页面组

FAQ 明确至少包括：

## 用户页面

- 注册
- 登录
- 用户信息
- 用户管理

## Problem 页面

- 列表
- 详情
- 新增 / 编辑

Step6 正文还要求：

- 删除

## Submission 页面

- 提交记录列表
- Submission 详情

Step6 正文进一步要求代码提交能力。

---

# 95. Step6 评分

| 功能 | 分值 |
|---|---:|
| 用户页面组 | 2 |
| Problem 页面组 | 1 |
| Submission 页面组 | 1 |
| 前后端 API 对接 | 1 |
| 合计 | 5 |

---

# 96. 自动测试支持：系统 reset

虽然不是 Step6 评分点，但 API 文档要求提供：

```text
POST /api/reset/
```

用途：

```text
自动测试恢复初始系统环境
```

权限：

```text
仅管理员
```

但测试环境：

```text
可不校验管理员权限
```

---

# 97. reset 行为

Reset 应：

- 清空测试产生的用户
- 清空题目
- 清空 Submission
- 清空相关运行数据
- 退出当前登录状态
- 重新创建初始管理员

初始管理员仍为：

```text
admin / admintestpassword
```

---

# 98. Advance：AI 智能命题

## 98.1 模块目标

让 AI 辅助教师/助教完成 OJ 命题。

AI 应能处理：

- 知识点要求
- 预期难度
- 题面设计
- Problem 配置
- testcase 生成
- 题目修改
- 题目迭代

生成结果应能方便进入：

```text
题目新增
题目编辑
审阅
维护
```

流程。

---

# 99. Advance 不限定 Agent 架构

不强制：

- Agent Loop
- 工具调用
- Web Search
- 固定工作流

这些属于设计参考。

可以使用：

- 单次模型调用
- 多轮模型交互
- 固定工作流
- Agent
- Tools
- 其他合理方案

真正硬性要求是：

```text
R1～R4
```

以及题目质量相关评分。

---

# 100. R1：AI 出题交互界面

系统需要有可操作的 AI 命题界面。

可以：

- 集成到 Problem 新增页
- 集成到 Problem 编辑页
- 单独新增 AI 命题页

需要支持：

- 输入命题需求
- 展示任务状态
- 展示结果
- 将结果用于 Problem 新增或修改

---

# 101. R2：模型配置

至少支持：

```text
provider_url
model
api_key
```

配置必须真实应用到模型请求。

不能把：

```text
provider URL
model name
api_key
```

写死在代码中。

---

# 102. API Key 安全

模型密钥属于敏感数据。

不得在：

- 日志
- 普通 API Response
- 页面明文展示
- Error message

中泄露。

---

# 103. R3：实时进度

任务执行时需要持续展示可观察进度。

不能：

```text
等整个任务完成后一次性返回最终结果
```

可选技术：

- Streaming
- SSE
- WebSocket
- Polling

---

# 104. R3：中断任务

必须可以：

```text
实际终止正在执行的任务
或
阻止任务继续执行
```

仅仅：

```text
关闭前端动画
停止显示进度
```

但后台仍运行，不满足要求。

---

# 105. R4：Token 用量

需要统计：

```text
input_tokens
output_tokens
total_tokens
```

如果模型接口能分别返回输入和输出 Token，应分别保存和展示。

---

# 106. R4：费用

根据模型价格计算：

```text
cost
```

应记录/说明：

```text
input_price
output_price
price_unit
currency
```

若供应商不给完整 token usage：

```text
需说明估算方式和限制
```

---

# 107. AI 设计正例

文档给出的设计方向包括：

## 107.1 迭代式命题

允许用户继续要求 AI：

- 改背景
- 改考察内容
- 改 difficulty
- 加强 testcase
- 保留知识点但换题目情境

体现多轮改进能力。

## 107.2 Tool 扩展

可选给 AI：

- Web 检索
- CLI
- testcase 生成脚本
- 运行校验脚本

但工具范围和权限必须控制。

---

# 108. AI 设计反例

不推荐：

## 108.1 与 Problem 管理割裂

例如：

```text
只放一个“AI 出题”按钮
→ 生成 ZIP
→ 无法直接进入 Problem 编辑/审阅
```

这种集成度太低。

## 108.2 只有普通文本生成

如果 AI：

- 只生成一段题面
- 不理解知识点
- 不生成有效 testcase
- 无法完成命题需求

则不满足良好智能命题目标。

---

# 109. AI Model Config API

文档给出建议接口：

```text
PUT /api/ai/model-config
```

权限：

```text
已登录用户
```

字段：

```text
provider_url
model
api_key
input_price
output_price
price_unit
```

注意：

Advance API 允许按项目设计使用等价路径和字段，但必须在项目文档说明。

---

# 110. 创建 AI 命题任务

建议：

```text
POST /api/ai/problem-tasks/
```

字段：

```text
requirement
problem_id
其他项目需要字段
```

其中：

```text
requirement 必填
problem_id 可选
```

返回：

```text
task_id
status
```

初始状态可为：

```text
pending
```

---

# 111. 查询 AI Task

建议：

```text
GET /api/ai/problem-tasks/{task_id}
```

权限：

```text
Task 创建者
或
管理员
```

Task 状态至少区分：

```text
等待
执行
完成
中断
失败
```

返回可包含：

```text
progress
result
usage
```

---

# 112. AI 实时事件

如果使用 SSE，可设计：

```text
GET /api/ai/problem-tasks/{task_id}/events
```

事件可包括：

```text
progress
usage
```

等。

该路径属于建议，不是基础 API 的固定路径要求。

---

# 113. 中断 AI Task

建议：

```text
PUT /api/ai/problem-tasks/{task_id}/cancel
```

权限：

```text
Task 创建者
或
管理员
```

错误：

```text
401
403
404
409 已结束
```

---

# 114. AI 安全

需要：

- 校验请求参数
- 校验模型返回
- 后端执行权限判断
- 不泄露密码
- 不泄露 API Key
- 处理模型请求 timeout
- 处理模型服务异常
- 工具调用限制参数范围
- 对文件/命令等副作用操作做安全控制

---

# 115. Advance 评分

| 项目 | 分值 |
|---|---:|
| R1 出题交互界面 | 1 |
| R2 自定义模型配置 | 1 |
| R3 实时进度与中断 | 1 |
| R4 Token 与价格 | 1 |
| 题目合理性 | 2 |
| testcase 有效性 | 2 |
| 易用性 | 2 |
| 合计 | 10 |

---

# 116. 题目合理性评分重点

AI 生成 Problem 是否：

- 满足课程实际需要
- 覆盖指定知识点
- 满足输入难度
- 满足其他命题约束

---

# 117. testcase 有效性评分重点

需要考虑：

- 边界条件
- 不同规模
- 特殊数据
- 不同时间复杂度算法的区分能力

不能只生成若干简单随机样例。

---

# 118. 功能易用性

评分关注：

- 流程是否自然
- 操作是否便捷
- 结果展示是否清楚
- 与原有 Problem 工作流是否整合

---

# 119. API 总表

## 119.1 Problem

```text
GET    /api/problems/
POST   /api/problems/
GET    /api/problems/{problem_id}
PUT    /api/problems/{problem_id}
DELETE /api/problems/{problem_id}
PUT    /api/problems/{problem_id}/log_visibility
```

## 119.2 Submission

```text
POST /api/submissions/
GET  /api/submissions/
GET  /api/submissions/{submission_id}
PUT  /api/submissions/{submission_id}/rejudge
GET  /api/submissions/{submission_id}/log
```

## 119.3 Language

```text
POST /api/languages/
GET  /api/languages/
```

## 119.4 Auth

```text
POST /api/auth/login
POST /api/auth/logout
```

## 119.5 Users

```text
POST /api/users/
POST /api/users/admin
GET  /api/users/
GET  /api/users/{user_id}
PUT  /api/users/{user_id}/role
```

## 119.6 Audit

```text
GET /api/logs/access/
```

## 119.7 Test reset

```text
POST /api/reset/
```

## 119.8 Advance 建议 API

```text
PUT  /api/ai/model-config
POST /api/ai/problem-tasks/
GET  /api/ai/problem-tasks/{task_id}
GET  /api/ai/problem-tasks/{task_id}/events
PUT  /api/ai/problem-tasks/{task_id}/cancel
```

Advance 的路径可以等价调整，但必须写入项目文档。

---

# 120. FAQ：Linux 兼容性

最终评分结合：

```text
Linux 自动评测
+
线下人工验收
```

因此代码需要适配 Linux 常见指令。

macOS 一般兼容课程用到的 Linux 命令。

Windows 用户建议使用：

```text
WSL
```

课程重点可能用到：

```text
g++
python
```

---

# 121. FAQ：环境

推荐：

```text
Python >= 3.8
```

Step2 更具体建议：

```text
Python 3.10
```

建议使用：

```text
venv
conda
```

管理虚拟环境。

常见依赖包括：

- FastAPI
- pytest
- requests
- uvicorn

具体以项目 `requirements.txt` 为准。

---

# 122. FAQ：API 测试

建议使用：

```text
Postman
curl
httpie
```

测试时检查：

- Method
- Path
- Body
- Query
- Session/Cookie
- HTTP status
- JSON code
- msg
- 权限行为

---

# 123. FAQ：评测注意事项

必须：

- 严格输入输出
- 无多余提示
- 支持多语言
- time_limit
- memory_limit
- TLE
- MLE
- testcase logs

---

# 124. FAQ：权限

普通用户：

- 主要操作自己的用户信息
- 主要查看自己的 Submission
- 主要查看自己的 Log

管理员：

- 用户管理
- Problem 删除
- Rejudge
- 全部日志
- 日志配置
- 审计

具体仍以 API 单接口权限为准。

---

# 125. FAQ：Step6 必须实现

FAQ 明确：

```text
必须实现前端
```

因为：

```text
Step6 已调整为基础模块
```

这是当前 DBG 文档与一些旧版本要求的重要区别。

---

# 126. FAQ：AI Agent Loop

不要求一定实现：

```text
Agent Loop
Tools
```

只要满足 R1～R4 和质量评分即可。

---

# 127. FAQ：AI 示例是否全部必做

不要求。

正反例是设计指导，而不是逐项硬性需求。

---

# 128. FAQ：模型配置

至少支持：

```text
provider URL
model name
API key
```

并且不能在代码中硬编码。

API key 不得泄露。

---

# 129. FAQ：实时进度与中断

实时：

```text
执行过程中持续更新
```

中断：

```text
后台真的停止/阻止继续执行
```

不只是 UI 停止动画。

---

# 130. FAQ：Token 与费用

需要展示：

- Token 用量
- 模型调用费用

若输入输出单价不同，需要分开计算。

需说明：

- price unit
- 计价依据
- 估算限制

---

# 131. FAQ：基础 API 必须一致

当前文档明确：

```text
基础模块接口必须严格遵循 api.md
```

Advance 因设计差异可以使用等价 API，但必须清楚说明：

- path
- 参数
- status
- response

---

# 132. FAQ：允许使用 AI

允许：

```text
AI / LLM / Vibe Coding
```

但：

- 要说明来源
- 报告写 AI 使用说明
- 不能抄袭
- 需要理解自己的架构和核心代码

---

# 133. 评分时间节点

当前评分页面写明：

## 133.1 功能验收

```text
2026-09-10（周四）
```

由助教线下验收。

## 133.2 源码

所有源码需要在：

```text
2026-09-10 课前
```

完成。

网络学堂提交：

```text
最后一次 Git commit 号
```

## 133.3 实验报告

截止：

```text
2026-09-10 23:59
```

通过网络学堂提交。

## 133.4 补交

原则：

```text
不接受补交
```

特殊情况需要充分证明。

每人只有一次补交机会。

## 133.5 未参加验收

逾期未参加：

```text
实验功能部分 = 0
```

---

# 134. 代码规范 5 分

重点：

- 项目结构
- Git 使用
- 避免大文件
- 提交历史
- Conventional Commits
- 代码可读性
- 合理模块划分

---

# 135. 实验报告 5 分

| 部分 | 分值 |
|---|---:|
| 系统功能与设计 | 2 |
| 关键实现与难点 | 2 |
| 成果展示 | 1 |
| AI 使用说明 | 0 |
| 总结与建议 | 0 |

即使 AI 使用说明单独不计分，也需要写。

---

# 136. 报告内容建议

## 系统功能与设计

说明：

- 架构
- 主要模块
- 技术选型
- 数据流

## 关键实现与难点

例如：

- 异步评测
- subprocess
- TLE
- MLE
- Session
- 权限
- 日志
- Streamlit Session
- C++ 编译

## 成果展示

展示：

- 前端
- API
- 评测结果
- 边界测试
- 异常状态

## AI 使用说明

包括：

- AI 工具链
- Vibe Coding 工作流
- AI 参与模块
- 大致代码比例
- 如何验证 AI 生成代码

---

# 137. 报告格式

建议：

```text
PDF
```

要求：

- 结构清楚
- 图文结合
- 与代码和演示保持一致

---

# 138. 扣分项

## 138.1 不使用 async FastAPI

直接影响功能分。

## 138.2 抄袭 / 作弊

```text
0 分
```

## 138.3 不参加验收

功能部分：

```text
0 分
```

## 138.4 代码 / 报告严重缺失

酌情扣分。

## 138.5 代码 / 报告 / 演示不一致

酌情扣分。

## 138.6 Git 大文件与不规范提交

会影响代码规范部分。

---

# 139. 仓库拉取教程

## 139.1 基本 Git 命令

需要熟悉：

```bash
git clone
git add
git commit
git push
```

协作时还需要理解：

- 多远程仓库
- pull
- merge/rebase
- conflict

---

# 140. 克隆个人 OJ 仓库

基本形式：

```bash
git clone https://git.tsinghua.edu.cn/<git-space>/<repo-name>.git
cd <repo-name>
```

课程示例仓库命名形式类似：

```text
python-course-2026/pa2-oj-<student-id>.git
```

---

# 141. GitLab 登录

如果 HTTPS clone 要认证：

```text
username = 清华 GitLab ID
```

密码不是普通账户登录密码。

需要在 GitLab：

```text
User settings
→ Personal access tokens
```

生成 Access Token。

---

# 142. 查看 Remote

```bash
git remote -v
```

直接 clone 后默认 Remote 名通常为：

```text
origin
```

---

# 143. pull.rebase 配置

当前仓库：

```bash
git config pull.rebase true
```

全局：

```bash
git config --global pull.rebase true
```

用于避免每次 pull 时重复询问默认策略。

---

# 144. Already up to date 排查

如果出现：

```text
Already up to date
```

但预期应该有更新，需要检查：

```bash
git remote -v
```

确认当前拉取的 remote 是否绑定了正确仓库。

---

# 145. 课程文档中的重要实现优先级

从评分与 API 强制性来看，建议优先确保：

1. 所有 Router 都是 `async def`
2. API path 完全正确
3. HTTP status 与 JSON code 相同
4. 异常优先级正确
5. Session 权限正确
6. Problem CRUD 正确
7. Python Judge 正确
8. C++ Judge 正确
9. TLE 正确
10. MLE 正确
11. Submission 状态与 testcase result 分离
12. Submission query / pagination 正确
13. Rejudge 正确
14. testcase log 正确
15. public_cases 权限正确
16. Access audit 正确
17. Streamlit 前端完整
18. `/api/reset/` 可供自动测试使用
19. Git 与报告完整
20. 再考虑 Advance

---

# 146. 基础模块最终 Checklist

## FastAPI

- [ ] 所有 API 使用 `async def`
- [ ] 所有 HTTP status 正确
- [ ] JSON `code` 与 HTTP status 一致
- [ ] 参数校验返回 400
- [ ] 异常检查顺序正确

## Step1

- [ ] GET problems
- [ ] POST problem
- [ ] PUT problem
- [ ] DELETE problem
- [ ] GET problem detail
- [ ] 必选字段验证
- [ ] 默认字段
- [ ] 登录权限
- [ ] 删除 admin only

## Step2

- [ ] Python
- [ ] C++
- [ ] AC
- [ ] WA
- [ ] TLE
- [ ] MLE
- [ ] RE
- [ ] CE
- [ ] UNK
- [ ] 动态语言注册
- [ ] 语言列表
- [ ] time_limit
- [ ] memory_limit
- [ ] 异步评测

## Step3

- [ ] POST submission
- [ ] pending
- [ ] success
- [ ] error
- [ ] GET single submission
- [ ] GET submission list
- [ ] user_id/problem_id 筛选
- [ ] status 筛选
- [ ] 分页特殊规则
- [ ] owner/admin 权限
- [ ] 429 rate limit
- [ ] admin rejudge

## Step4

- [ ] initial admin
- [ ] Session
- [ ] bcrypt
- [ ] register
- [ ] login
- [ ] logout
- [ ] user/admin/banned
- [ ] user info
- [ ] admin creation
- [ ] role update
- [ ] user list
- [ ] submit_count
- [ ] resolve_count

## Step5

- [ ] testcase details
- [ ] submission log
- [ ] own log
- [ ] admin all logs
- [ ] public_cases
- [ ] log_visibility
- [ ] access log
- [ ] 403 访问审计
- [ ] 不记录不要求审计的错误

## Step6

- [ ] Streamlit
- [ ] 用户注册页面
- [ ] 登录页面
- [ ] 登出
- [ ] 用户信息
- [ ] 用户管理
- [ ] Problem list
- [ ] Problem detail
- [ ] Problem add
- [ ] Problem edit
- [ ] Problem delete
- [ ] Code submit
- [ ] Submission list
- [ ] Submission detail
- [ ] 状态更新
- [ ] compile/run/error 信息
- [ ] 所有操作只走 REST API
- [ ] Session 正确传递
- [ ] 错误提示正确

## 自动测试

- [ ] POST `/api/reset/`
- [ ] reset 后重新创建 admin
- [ ] reset 后当前 Session 退出

## 工程

- [ ] Linux/WSL 可运行
- [ ] `requirements.txt`
- [ ] Conventional Commits
- [ ] 无无关大文件
- [ ] 报告
- [ ] AI 使用说明
