# API 文档

> 来源：`https://dbg-course.github.io/python-docs/oj/api/`  
> 整理日期：2026-09-01  
> 本文件仅根据该 DBG-Course 页面整理，不混入其他站点或旧版作业要求。

---

# 目录

1. [状态码与异常](#状态码与异常)
2. [题目管理相关接口（Step 1）](#1-题目管理相关接口step-1)
3. [评测相关接口（Step 2 & 3）](#2-评测相关接口step-2--3)
4. [用户管理相关接口（Step 4）](#3-用户管理相关接口step-4)
5. [评测日志相关接口（Step 5）](#4-评测日志相关接口step-5)
6. [前端交互说明（Step 6）](#5-前端交互说明step-6)
7. [AI 智能命题接口（Advance）](#6-ai-智能命题接口advance)
8. [安全性说明](#7-安全性说明)

---

# 系统初始化说明

系统启动时自动创建初始管理员：

```text
username: admin
password: admintestpassword
```

实现时仍需满足课程关于密码安全的要求。

---

# 状态码与异常

| HTTP 状态码 | 说明 | 示例场景 |
|---:|---|---|
| `200` | 正常 | 请求成功 |
| `400` | 参数错误 | 缺少参数、参数格式错误 |
| `401` | 未登录 | 未认证访问受保护 API |
| `403` | 权限不足 / 禁用 | banned 用户、普通用户访问管理员接口 |
| `404` | 资源不存在 | 题目、评测等不存在 |
| `409` | 资源状态冲突 | ID 已存在、任务已经结束 |
| `429` | 频率超限 | 1 分钟内提交超过 3 次 |
| `500` | 服务器异常 | 未知内部错误 |

异常处理优先级：

```text
401 > 403 > 400 > 429 > 409 > 404 > 500
```

所有 API JSON 响应必须包含：

```text
code
```

并且：

```text
JSON.code == 实际 HTTP status code
```

服务器必须设置正确的 HTTP 状态码，不能统一返回 `200`。

错误响应结构：

```json
{
  "code": 404,
  "msg": "problem not found",
  "data": null
}
```

---

# 1. 题目管理相关接口（Step 1）

## 1.1 查看题目列表

### 请求

```http
GET /api/problems/
```

### 权限

所有已登录用户。

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "id": "sum_2",
      "title": "两数之和"
    },
    {
      "id": "max_num",
      "title": "最大数"
    }
  ]
}
```

---

## 1.2 添加题目

### 请求

```http
POST /api/problems/
```

### 权限

所有已登录用户。

### 参数

#### 必填字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `str` | 题目唯一标识 |
| `title` | `str` | 题目标题 |
| `description` | `str` | 题目描述 |
| `input_description` | `str` | 输入格式说明 |
| `output_description` | `str` | 输出格式说明 |
| `samples` | `list` | 样例输入输出，元素为 `{input, output}` |
| `constraints` | `str` | 数据范围和限制条件 |
| `testcases` | `list` | 测试点，元素为 `{input, output}` |

#### 可选字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `hint` | `str` | 额外提示 |
| `source` | `str` | 题目来源 |
| `tags` | `list` | 题目标签 |
| `time_limit` | `float` | 时间限制，单位秒，默认 `3` |
| `memory_limit` | `int` | 内存限制，单位 MB，默认 `128` |
| `author` | `str` | 题目作者 |
| `difficulty` | `str` | 难度等级 |

### 响应

```json
{
  "code": 200,
  "msg": "add success",
  "data": {
    "id": "sum_2"
  }
}
```

### 异常

```text
400 字段缺失或格式错误
401 未登录
409 id 已存在
```

---

## 1.3 编辑题目

### 请求

```http
PUT /api/problems/{problem_id}
```

### 权限

所有已登录用户。

### 参数

请求体字段与添加题目一致。

要求：

```text
请求体中的 id 必须和 URL 中的 problem_id 一致。
```

更新后的完整题目配置仍需通过与新增题目相同的字段校验。

### 响应

```json
{
  "code": 200,
  "msg": "update success",
  "data": {
    "id": "sum_2"
  }
}
```

### 异常

```text
400 字段缺失、格式错误或 id 不一致
401 未登录
404 题目不存在
```

---

## 1.4 删除题目

### 请求

```http
DELETE /api/problems/{problem_id}
```

### 权限

仅管理员。

### 参数

URL 路径参数：

```text
problem_id
```

### 响应

```json
{
  "code": 200,
  "msg": "delete success",
  "data": {
    "id": "sum_2"
  }
}
```

### 异常

```text
401 未登录
403 权限不足
404 题目不存在
```

---

## 1.5 查看题目信息

### 请求

```http
GET /api/problems/{problem_id}
```

### 权限

所有已登录用户。

### 响应字段

完整题目信息可包含：

```text
id
title
description
input_description
output_description
samples
constraints
testcases
hint
source
tags
time_limit
memory_limit
author
difficulty
```

示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": "P1001",
    "title": "A+B Problem",
    "description": "输入两个整数并输出它们的和。",
    "input_description": "输入两个整数 a 和 b。",
    "output_description": "输出 a+b。",
    "samples": [
      {
        "input": "1 2",
        "output": "3"
      }
    ],
    "constraints": "|a|,|b| <= 10^9",
    "testcases": [
      {
        "input": "1 2",
        "output": "3"
      }
    ],
    "hint": "",
    "source": "",
    "tags": [],
    "time_limit": 1.0,
    "memory_limit": 128,
    "author": "",
    "difficulty": ""
  }
}
```

### 默认字段

没有提供的可选字段仍需返回该类型的默认值，例如：

```text
str  → ""
list → []
```

### 异常

```text
401 未登录
403 权限不足
404 题目不存在
```

---

# 2. 评测相关接口（Step 2 & 3）

Step 2 和 Step 3 的查询评测结果接口返回：

```text
评测状态
总分
编译信息
运行阶段总体信息
评测任务级错误信息
```

单个测试点的：

```text
result
time
memory
```

通过 Step 5 的评测日志接口查询。

评测列表只返回列表展示所需的摘要。

---

## 2.1 提交评测

### 请求

```http
POST /api/submissions/
```

### 权限

登录用户。

### 参数

| 字段 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `problem_id` | `str` | 是 | 题目编号 |
| `language` | `str` | 是 | 语言，例如 `python`、`cpp` |
| `code` | `str` | 是 | 用户代码 |

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "submission_id": "123",
    "status": "pending"
  }
}
```

### 异常

```text
400 参数错误
401 未登录
403 权限不足
404 题目不存在或语言不存在
429 提交频率超限
```

---

## 2.2 查询评测结果

### 请求

```http
GET /api/submissions/{submission_id}
```

### 权限

仅提交本人或管理员。

### 成功评测响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "submission_id": "123",
    "status": "success",
    "score": 10,
    "counts": 30,
    "compile_info": {
      "result": "success",
      "message": ""
    },
    "run_info": {
      "result": "finished",
      "message": "3 test cases finished"
    },
    "error_info": ""
  }
}
```

字段含义：

### `score`

本次提交获得的分数。

### `counts`

题目总分：

```text
测试点数量 × 10
```

### `compile_info`

返回编译是否成功及编译器信息。

解释型语言可返回：

```json
null
```

### `run_info`

返回整个程序运行阶段的总体结果。

单测试点详细结果仍通过日志接口查询。

### `error_info`

评测任务级别错误信息。

不得包含：

- 服务器敏感绝对路径
- 密钥
- 其他敏感运行信息

### pending 状态

至少返回：

```text
submission_id
status
```

尚未产生的字段可为 `null`。

### 异常

```text
401 未登录
403 权限不足
404 评测不存在
```

---

## 2.3 查询评测列表

### 请求

```http
GET /api/submissions/
```

### 参数

```text
user_id
problem_id
status
page
page_size
```

这五个参数均可选。

其中：

```text
user_id
problem_id
```

是一级条件。

一级条件：

```text
不可以全部为空
```

其余属于二级条件。

### 分页规则

#### `page` 和 `page_size` 都为空

返回：

```text
全部匹配数据
```

#### `page` 为空、`page_size` 非空

默认：

```text
第一页
```

#### `page` 非空、`page_size` 为空

属于：

```text
400 参数错误
```

### 权限

本人或管理员。

如果未提供 `user_id`：

- 管理员可查看该题所有用户提交。
- 普通用户只能查看该题自己的提交。

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 100,
    "submissions": [
      {
        "submission_id": "1",
        "status": "success",
        "score": 10,
        "counts": 30
      }
    ]
  }
}
```

如果 Submission 状态是：

```text
error
pending
```

列表项只需要返回：

```text
submission_id
status
```

---

## 2.4 重新评测

### 请求

```http
PUT /api/submissions/{submission_id}/rejudge
```

### 权限

仅管理员。

### 行为

重新评测时：

```text
复用原 submission_id
覆盖该 submission_id 原有评测内容
重新设置为 pending
```

### 响应

```json
{
  "code": 200,
  "msg": "rejudge started",
  "data": {
    "submission_id": "1",
    "status": "pending"
  }
}
```

### 异常

```text
401 未登录
403 权限不足
404 评测不存在
```

---

## 2.5 动态注册新语言

### 请求

```http
POST /api/languages/
```

### 权限

所有已登录用户。

### 参数

| 字段 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `name` | `str` | 是 | 语言名称 |
| `file_ext` | `str` | 是 | 源代码文件扩展名 |
| `compile_cmd` | `str` | 否 | 编译命令 |
| `run_cmd` | `str` | 是 | 运行命令 |
| `time_limit` | `float` | 否 | 默认时间限制，秒 |
| `memory_limit` | `int` | 否 | 默认内存限制，MB |

### 响应

```json
{
  "code": 200,
  "msg": "language registered",
  "data": {
    "name": "go"
  }
}
```

### 异常

```text
400 参数错误
401 未登录
403 用户无权限
```

### C++ 示例配置

```json
{
  "name": "cpp",
  "file_ext": ".cpp",
  "compile_cmd": "g++ {src} -o {exe}",
  "run_cmd": "{exe}",
  "time_limit": 1.0,
  "memory_limit": 128
}
```

`{src}` 与 `{exe}` 展开后必须是路径。

### Python 示例配置

```json
{
  "name": "python",
  "file_ext": ".py",
  "run_cmd": "python3 {src}",
  "time_limit": 1.0,
  "memory_limit": 128
}
```

---

## 2.6 查询支持语言列表

### 请求

```http
GET /api/languages/
```

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "name": [
      "python",
      "cpp"
    ]
  }
}
```

---

# 3. 用户管理相关接口（Step 4）

## 3.1 用户登录

### 请求

```http
POST /api/auth/login
```

### 参数

```text
username: str，必填
password: str，必填
```

### 响应

```json
{
  "code": 200,
  "msg": "login success",
  "data": {
    "user_id": "1",
    "username": "alice",
    "role": "user"
  }
}
```

### 异常

```text
400 参数错误
401 用户名或密码错误
403 用户被禁用
```

---

## 3.2 用户登出

### 请求

```http
POST /api/auth/logout
```

### 权限

登录用户。

### 参数

无。

### 响应

```json
{
  "code": 200,
  "msg": "logout success",
  "data": null
}
```

### 异常

```text
401 未登录
```

---

## 3.3 创建管理员账户

### 请求

```http
POST /api/users/admin
```

### 权限

仅管理员。

### 参数

```text
username: str，必填
password: str，必填
```

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "user_id": "2",
    "username": "new_admin"
  }
}
```

### 异常

```text
400 用户名已存在或参数错误
401 未登录
403 用户无权限
```

---

## 3.4 用户注册

### 请求

```http
POST /api/users/
```

### 参数

```text
username: str，必填
password: str，必填
```

### 响应

```json
{
  "code": 200,
  "msg": "register success",
  "data": {
    "user_id": "1",
    "username": "xiaogang",
    "join_time": "2012-07-14",
    "role": "user",
    "submit_count": 0,
    "resolve_count": 0
  }
}
```

字段含义：

```text
submit_count:
按提交次数统计，同一个 Problem 可以贡献多次。

resolve_count:
按通过的不同 Problem 数统计，一个 Problem 最多贡献一次。
```

### 异常

```text
400 用户名已存在或参数错误
```

---

## 3.5 查询用户信息

### 请求

```http
GET /api/users/{user_id}
```

### 权限

仅本人或管理员。

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "user_id": "1",
    "username": "alice",
    "join_time": "2012-07-14",
    "role": "user",
    "submit_count": 80,
    "resolve_count": 7
  }
}
```

### 异常

```text
401 用户未登录
403 用户无权限
404 用户不存在
```

---

## 3.6 用户权限变更

### 请求

```http
PUT /api/users/{user_id}/role
```

### 权限

仅管理员。

### 参数

```text
role: str，必填
```

可取值示例：

```text
admin
user
banned
```

### 响应

```json
{
  "code": 200,
  "msg": "role updated",
  "data": {
    "user_id": "1",
    "role": "admin"
  }
}
```

### 异常

```text
400 参数错误
401 用户未登录
403 用户无权限
404 用户不存在
```

---

## 3.7 用户列表查询

### 请求

```http
GET /api/users/
```

### 参数

```text
page
page_size
```

均可选。

参数含义与：

```http
GET /api/submissions/
```

中的分页规则一致。

### 权限

仅管理员。

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 3,
    "users": [
      {
        "user_id": "1",
        "username": "xiaoming",
        "role": "user",
        "join_time": "1924-08-17",
        "submit_count": 100,
        "resolve_count": 9
      },
      {
        "user_id": "2",
        "username": "xiaohong",
        "role": "user",
        "join_time": "1911-04-05",
        "submit_count": 90,
        "resolve_count": 8
      }
    ]
  }
}
```

### 异常

```text
400 参数错误
401 用户未登录
403 用户无权限
404 用户不存在
```

---

# 4. 评测日志相关接口（Step 5）

## 4.1 查询评测日志

### 请求

```http
GET /api/submissions/{submission_id}/log
```

### 权限

默认：

```text
提交本人
或
管理员
```

当对应 Problem 的：

```text
public_cases = True
```

时，普通已登录用户也可以看到 `details`。

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "details": [
      {
        "id": 1,
        "result": "AC",
        "time": 1.01,
        "memory": 130
      },
      {
        "id": 2,
        "result": "TLE",
        "time": 1.01,
        "memory": 130
      },
      {
        "id": 3,
        "result": "MLE",
        "time": 1.01,
        "memory": 130
      }
    ],
    "score": 10,
    "counts": 30
  }
}
```

### `details`

管理员可见。

普通用户只有在：

```text
public_cases=True
```

时可见公开 testcase details。

### 异常

```text
400 参数错误
401 用户未登录
403 用户无权限
404 评测不存在
```

---

## 4.2 配置日志可见性

### 请求

```http
PUT /api/problems/{problem_id}/log_visibility
```

### 权限

仅管理员。

### 参数

```text
public_cases: bool，可选，默认 False
```

### 响应

```json
{
  "code": 200,
  "msg": "log visibility updated",
  "data": {
    "problem_id": "sum_3_numbers",
    "public_cases": true
  }
}
```

### 异常

```text
400 参数错误
401 用户未登录
403 用户无权限
404 题目不存在
```

---

## 4.3 日志访问审计

### 请求

```http
GET /api/logs/access/
```

### 权限

仅管理员。

### 参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | `str` | 否 | 按用户筛选 |
| `problem_id` | `str` | 否 | 按题目筛选 |
| `page` | `int` | 否 | 页码 |
| `page_size` | `int` | 否 | 每页数量 |

分页规则与：

```http
GET /api/submissions/
```

一致。

### Access Log 字段

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

记录本次日志访问返回的状态，例如：

```text
200
403
```

页面正文规定 `action` 只有：

```text
view_logs
```

页面响应示例中出现：

```text
view_log
```

实现时应以课程自动测试/最新页面要求为准。

### 不必记录的访问

以下情况不要求产生 access log：

- 未登录
- Submission 不存在
- 参数错误

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "user_id": "test",
      "problem_id": "sum_3_numbers",
      "action": "view_log",
      "time": "2024-06-01",
      "status": "403"
    }
  ]
}
```

### 异常

```text
400 参数错误
401 用户未登录
403 用户无权限
```

---

# 5. 前端交互说明（Step 6）

Step 6 不增加新的业务数据接口。

前端应调用 Step 1～Step 5 的现有 API。

| 页面组 | 主要接口 |
|---|---|
| 用户页面组 | `POST /api/users/`、`POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/users/{user_id}`、`PUT /api/users/{user_id}/role` |
| 题目页面组 | `GET /api/problems/`、`GET /api/problems/{problem_id}`、`POST /api/problems/`、`PUT /api/problems/{problem_id}`、`DELETE /api/problems/{problem_id}` |
| 评测与提交页面组 | `POST /api/submissions/`、`GET /api/submissions/`、`GET /api/submissions/{submission_id}`、`GET /api/submissions/{submission_id}/log` |

前端必须根据：

```text
HTTP status
code
msg
data
```

展示操作结果。

权限、登录状态和资源可见性必须以后端判断为准。

不能只靠：

```text
前端隐藏按钮
```

实现权限控制。

---

## 5.1 测试支持：系统重置

该接口供自动测试恢复初始环境使用。

不属于 Step 6 评分内容。

### 请求

```http
POST /api/reset/
```

### 权限

正常环境：

```text
仅管理员
```

测试环境：

```text
允许不校验管理员权限
```

### 参数

无。

### 响应

```json
{
  "code": 200,
  "msg": "system reset successfully",
  "data": null
}
```

### 行为

重置系统需要：

- 清空测试产生的用户
- 清空题目
- 清空提交数据
- 退出当前登录状态
- 重新创建初始管理员

### 异常

```text
401 用户未登录
403 权限不足
```

---

# 6. AI 智能命题接口（Advance）

Advance 的页面结构和技术方案不强制统一。

下面接口用于说明 R1～R4 所需的数据交互。

可以根据项目设计采用：

- 等价路径
- 不同传输协议
- 不同字段结构

但如果与下面不同，必须在项目文档中说明。

---

## 6.1 模型配置

### 建议请求

```http
PUT /api/ai/model-config
```

### 权限

已登录用户。

### 参数

| 字段 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `provider_url` | `str` | 是 | 模型提供商 URL |
| `model` | `str` | 是 | 模型名称 |
| `api_key` | `str` | 是 | 模型密钥 |
| `input_price` | `float` | 否 | 输入 Token 单价 |
| `output_price` | `float` | 否 | 输出 Token 单价 |
| `price_unit` | `int` | 否 | 计价 Token 单位，例如 `1000000` |

### 响应

```json
{
  "code": 200,
  "msg": "model config updated",
  "data": {
    "provider_url": "https://model-provider.example/v1",
    "model": "example-model",
    "api_key_configured": true,
    "input_price": 1.0,
    "output_price": 2.0,
    "price_unit": 1000000
  }
}
```

### 密钥安全

模型密钥不得：

- 通过普通查询接口返回
- 在普通响应中返回
- 明文记录到日志

若保存 API Key，应采取与敏感程度匹配的保护措施。

---

## 6.2 创建智能命题任务

### 建议请求

```http
POST /api/ai/problem-tasks/
```

### 权限

已登录用户。

### 参数

```text
requirement: str，必填
problem_id: str，可选
其他与项目功能相关的参数
```

`problem_id` 可用于参考或修改已有 Problem。

### 响应

```json
{
  "code": 200,
  "msg": "task created",
  "data": {
    "task_id": "ai-task-1",
    "status": "pending"
  }
}
```

### 异常

```text
400 参数错误
401 用户未登录
404 指定题目不存在
500 服务器异常
```

---

## 6.3 查询任务状态和结果

### 建议请求

```http
GET /api/ai/problem-tasks/{task_id}
```

### 权限

任务创建者或管理员。

### 响应

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "task_id": "ai-task-1",
    "status": "running",
    "progress": "正在处理命题需求",
    "result": null,
    "usage": {
      "input_tokens": 1200,
      "output_tokens": 350,
      "total_tokens": 1550,
      "cost": 0.0019,
      "currency": "USD"
    }
  }
}
```

### Task 状态

至少需要区分：

```text
等待
执行
完成
中断
失败
```

任务完成后：

```text
result
```

应能直接被智能命题界面继续使用。

具体 result 结构由项目设计决定。

---

## 6.4 实时进度

实时进度可以通过：

- 流式响应
- SSE
- WebSocket
- Polling

实现。

### SSE 建议请求

```http
GET /api/ai/problem-tasks/{task_id}/events
```

### 权限

任务创建者或管理员。

### 事件示例

```text
event: progress
data: {"task_id":"ai-task-1","status":"running","message":"正在处理命题需求"}

event: usage
data: {"input_tokens":1200,"output_tokens":350,"total_tokens":1550,"cost":0.0019,"currency":"USD"}
```

---

## 6.5 中断任务

### 建议请求

```http
PUT /api/ai/problem-tasks/{task_id}/cancel
```

### 权限

任务创建者或管理员。

### 响应

```json
{
  "code": 200,
  "msg": "task cancelled",
  "data": {
    "task_id": "ai-task-1",
    "status": "cancelled"
  }
}
```

### 异常

```text
401 用户未登录
403 用户无权限
404 任务不存在
409 任务已经结束
```

### 中断语义

中断必须：

```text
真正终止任务
或
阻止任务继续执行
```

不能只停止前端的进度展示。

---

## 6.6 Token 用量与价格

至少统计：

```text
input_tokens
output_tokens
total_tokens
cost
currency
```

如果输入和输出 Token 使用不同价格，可按：

```text
cost
=
input_tokens / price_unit × input_price
+
output_tokens / price_unit × output_price
```

计算。

如果模型 API 无法提供完整 Token usage，需要：

- 在页面说明统计/估算方式
- 在项目文档说明估算限制

---

# 7. 安全性说明

系统实现需要注意至少以下安全要求：

## 7.1 输入与数据校验

需要校验：

- 请求参数
- 上传内容
- 模型返回数据

## 7.2 后端权限

所有权限判断必须在：

```text
后端
```

完成。

不能使用：

```text
前端是否显示按钮
```

替代权限校验。

## 7.3 敏感数据

以下敏感信息不得明文写日志，也不得通过普通查询接口返回：

- 用户密码
- 模型 API Key
- 其他敏感凭证

## 7.4 外部模型调用

调用外部模型服务必须处理：

- timeout
- 请求失败
- 异常响应

避免任务长期占用资源。

## 7.5 外部工具

如果 Advance 实现外部工具调用，需要限制：

- 可用工具
- 工具参数范围

对于具有副作用的操作尤其需要安全控制，例如：

- 文件写入
- 命令执行

---

# API 路径汇总

## Problem

```text
GET    /api/problems/
POST   /api/problems/
PUT    /api/problems/{problem_id}
DELETE /api/problems/{problem_id}
GET    /api/problems/{problem_id}
PUT    /api/problems/{problem_id}/log_visibility
```

## Submission

```text
POST /api/submissions/
GET  /api/submissions/{submission_id}
GET  /api/submissions/
PUT  /api/submissions/{submission_id}/rejudge
GET  /api/submissions/{submission_id}/log
```

## Language

```text
POST /api/languages/
GET  /api/languages/
```

## Auth

```text
POST /api/auth/login
POST /api/auth/logout
```

## Users

```text
POST /api/users/admin
POST /api/users/
GET  /api/users/{user_id}
PUT  /api/users/{user_id}/role
GET  /api/users/
```

## Audit

```text
GET /api/logs/access/
```

## Test Support

```text
POST /api/reset/
```

## Advance AI（建议接口）

```text
PUT  /api/ai/model-config
POST /api/ai/problem-tasks/
GET  /api/ai/problem-tasks/{task_id}
GET  /api/ai/problem-tasks/{task_id}/events
PUT  /api/ai/problem-tasks/{task_id}/cancel
```
