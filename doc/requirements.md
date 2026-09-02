> 来源：[DBG-Course 在线评测系统文档](https://dbg-course.github.io/python-docs/oj/)  
> 核对日期：2026-09-02  
> 整理说明：正文按官网左侧导航重组；一级标题对应导航栏主要栏目，二级标题对应其子页面。页面正文、接口、字段、状态码、评分项、FAQ 与教程均按当前网页保留，仅调整标题层级，并将原相对链接改为可直接访问的官网链接。

# 实验概述

> 页面标题：OJ 系统实验说明

## 实验目标

构建一个小型但功能完整的 Online Judge (OJ) 系统，分阶段实现，逐步掌握系统设计、API 开发、异步评测、权限控制和前后端交互等核心能力。进阶模块在此基础上引入大语言模型应用开发。

> 快速入门可参考[快速入门文档](https://lab.cs.tsinghua.edu.cn/rust/projects/oj/quick-start/)。

## 技术要求

**异步编程实践**：本次作业要求使用 FastAPI 的异步接口（`async def`）完成所有 API 开发，目的是让大家初步体验异步编程的概念和用法。异步编程是现代 Web 开发的重要技术，有助于提高应用程序的并发性能。**不使用异步编程接口将拿不到本次作业分数，请同学们务必注意。**

**项目规模**：为了让大家初步体验较大项目的开发，本次作业代码行数预计在两千行左右，请同学们合理规划时间，做好进度管理。

**提交规范**：要求按照 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 规范编写 Git 提交信息，不符合规范的提交将酌情扣分。

---

## 基础模块（共30分）

| Step | 名称 | 主要功能描述 | 详细文档 |
| ---- | ---- | ------------ | -------- |
| Step 1 | 题目管理 | 题目配置加载、字段校验、增删改查 | [step1.md](https://dbg-course.github.io/python-docs/oj/project/step1/) |
| Step 2 | 评测控制 | 程序执行、资源限制、输出比对、动态注册语言 | [step2.md](https://dbg-course.github.io/python-docs/oj/project/step2/) |
| Step 3 | 评测管理 | 提交记录查询、状态管理、重新评测 | [step3.md](https://dbg-course.github.io/python-docs/oj/project/step3/) |
| Step 4 | 用户管理 | 用户注册、登录、权限管理、用户信息查询 | [step4.md](https://dbg-course.github.io/python-docs/oj/project/step4/) |
| Step 5 | 评测日志 | 测试点明细、日志查询、可见性与访问审计 | [step5.md](https://dbg-course.github.io/python-docs/oj/project/step5/) |
| Step 6 | 前端交互 | 用户、题目和评测提交页面，与后端 API 对接 | [step6.md](https://dbg-course.github.io/python-docs/oj/project/step6/) |

---

## 进阶模块（共 10 分）

| 模块 | 名称 | 主要功能描述 | 详细文档 |
| ---- | ---- | ------------ | -------- |
| Advance | AI 智能命题 | 在 OJ 系统上实现 AI 辅助命题 | [advance.md](https://dbg-course.github.io/python-docs/oj/project/advance/) |

---

## API 文档

所有接口、参数、异常、状态码等详见 [api.md](https://dbg-course.github.io/python-docs/oj/api/)。

---

## 评分标准

参见 [requirements.md](https://dbg-course.github.io/python-docs/oj/requirements/)

---

## 学习资源

- **技术教程**:
  - [系统设计基础](https://github.com/donnemartin/system-design-primer)
  - [Python 异步编程](https://docs.python.org/3/library/asyncio.html)
  - [Agent 架构：从文本生成到工具调用](https://lab.cs.tsinghua.edu.cn/rust/projects/agent/agent-architecture/)

- **参考项目**:
  - [Codeforces](https://codeforces.com/) - 知名OJ平台
  - [LeetCode](https://leetcode.com/) - 编程练习平台
  - [HackerRank](https://www.hackerrank.com/) - 技术评测平台

!!! 致谢
    本实验作业参考了韩文弢老师开设的程序设计训练（Rust）[OJ 大作业](https://lab.cs.tsinghua.edu.cn/rust/projects/oj/background/)的设计思想与文档结构。转载前已获得授课教师授权。在此对原作者及相关文档贡献者表示感谢。

---

# 实验内容

---

## Step1：题目管理

### 模块目标

实现题目配置的加载、动态增删改查，支持基础的 OJ 题目管理闭环。

---

### 前置知识要求

| 技术点         | 推荐学习内容           |
| -------------- | ---------------------- |
| JSON 配置文件   | `json.load()`          |
| REST API 基础   | FastAPI/Flask POST/GET/PUT/DELETE + 参数校验 |
| 异常处理        | `try/except`、HTTP 状态码 |

---

### 任务分解

> 具体字段与接口请参考 [api.md](https://dbg-course.github.io/python-docs/oj/api/)

#### 任务 1：题目管理 API
- 目标：实现题目配置的加载、增删改查。
- 要点：
  - 支持**查看题目列表**（返回所有题目的简要信息）。
  - 支持**添加题目**（校验字段完整性，保存到存储目录）。
  - 支持**编辑题目**（校验更新后的完整题目配置，覆盖原题目内容）。
  - 支持**删除题目**（根据题目 id 删除配置文件）。
  - 支持**查看具体题目信息**（根据题目 id 返回详细配置）。
  - 所有操作需返回结构化 JSON，异常时返回合理 HTTP 状态码。
- 建议：配置内容存入本地目录（如 `problems/`），每题一个 JSON 文件。

---

### OJ 题目字段说明

以洛谷 [P1001 A+B Problem](https://www.luogu.com.cn/problem/P1001) 为例，一个 OJ 题目通常需要以下字段：

#### 必选字段

1. **id**  
   题目唯一标识（如 "P1001"），用于检索和管理。
2. **title**  
   题目标题（如 "A+B Problem"），便于用户识别。
3. **description**  
   题目描述，详细说明题目的背景和要求。
4. **input_description**  
   输入格式说明，告诉用户输入数据的格式和要求。
5. **output_description**  
   输出格式说明，告诉用户输出数据的格式和要求。
6. **samples**  
   样例输入输出，通常为一个列表，每个元素包含 input 和 output 字段，帮助用户理解题意。
7. **constraints**  
   数据范围和限制条件（如 |a|,|b| ≤ 10^9），用于明确输入输出的边界。
8. **testcases**
   测试点，代码准确性通过测试点通过比例给出，会按难易划分，经常有毒瘤出题人卡常、造临界情况等。

#### 可选字段

1. **hint**  
   额外提示，帮助用户解题（如"有负数哦！"）。
2. **source**  
   题目来源或出处。
3. **tags**  
   题目标签，便于分类检索（如"基础题"、"模拟"）。
4. **time_limit**  
   时间限制，默认单位为 "s"，用于评测。
5. **memory_limit**  
   内存限制，默认单位为 "MB"，用于评测。
6. **author**  
   题目作者。
7. **difficulty**  
   难度等级。

##### 示例结构（JSON）

```json
{
  "id": "P1001",
  "title": "A+B Problem",
  "description": "输入两个整数 a, b，输出它们的和（|a|,|b| <= 10^9）。",
  "input_description": "输入两个整数 a 和 b。",
  "output_description": "输出 a+b 的结果。",
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
  "hint": "有负数哦！",
  "source": "洛谷",
  "tags": ["基础题"],
  "time_limit": 1,
  "memory_limit": 128,
  "author": "Luogu",
  "difficulty": "入门"
}
```

---

### 评分细则

| 功能/接口                | 分值 | 评分说明                         |
|--------------------------|------|----------------------------------|
| 题目列表/详情 API        | 3  | 路径、参数、响应、异常            |
| 题目增删改 API           | 2   | 路径、参数、响应、异常            |
| **小计**                 | **5**| |

---

## Step2：题目评测

### 模块目标

本模块将实现 OJ 题目的自动化评测。你需要从题库读取题目信息，接收用户提交的代码，自动运行并比对输出，返回结构化的评测结果。要求至少支持 Python 语言，进一步扩展支持 C++ 等多语言。

!!! danger "版本需求"
    建议 `python` 使用 `3.10` 版本；`C++` 使用 `GCC 9+, C++14` 版本

---

### 题目输入输出规范

与大一程设课类似，OJ 评测对输入输出格式有严格要求。以 [P1001 A+B Problem](https://www.luogu.com.cn/problem/P1001) 为例：

- **输入**：一行，包含两个整数 a 和 b，空格分隔。
- **输出**：一行，输出 a+b 的结果。

**注意事项：**
- 不允许有多余提示语（如"请输入..."）。
- 输出末尾允许有换行，评测时会忽略多余的行末空格和最后一行多余换行。
- 输入输出必须严格匹配样例格式。

**输入样例：**
```
1 2
```
**输出样例：**
```
3
```

---

### 任务分解

#### 任务 1：支持 Python 评测
- 实现评测流程：自动读取题库中的样例输入输出，将输入传递给用户提交的 Python 代码，捕获输出并与标准答案比对。
- 需要实现异步评测，但仅需支持单用户提交任务即可，不要求支持多用户同时提交代码。关于异步实现，你可以参考 `asyncio.create_task` 这个接口。
- 返回结构化评测结果（如 AC/WA/RE/TLE），并记录可供提交详情页面展示的编译信息、运行结果和错误信息。

**测试点结果**

你只需要考虑如下测试点结果，如果非 `AC` ~ `CE` 状态全部归为 `UNK` 即可。

| 状态缩写    | 全称                    | 含义                                    |
| ------- | --------------------- | ------------------------------------- |
| **AC**  | Accepted Answer          | 输出正确，程序运行无异常且输出结果与标准答案一致。            |
| **WA**  | Wrong Answer          | 输出错误，程序运行无异常但输出结果与标准答案不一致。            |
| **TLE** | Time Limit Exceeded   | 超时，程序运行超过了题目规定的时间限制。                  |
| **MLE** | Memory Limit Exceeded | 内存超限，程序使用内存超过了题目限制。                   |
| **RE**  | Runtime Error         | 运行时错误，如除零、数组越界、段错误等。                  |
| **CE**  | Compilation Error     | 编译错误，代码无法通过编译。                        |
| **UNK** | Unknown Error         | 未知错误，程序运行过程中发生了未被捕获的异常。               |

**评测状态**

对于评测状态，你只需要考虑如下三种。

| 状态    |      含义                      |
| ------- |      ---------------       |
| **pending**  |  评测正在进行中  |
| **success**  | 评测正常返回结果 |
| **error**  | 评测过程出现问题  |


> **如何评测一个任务？**
> 
> 设想一下你在运行一段 python 代码，你需要先将代码保存至一个文件（如 `test.py`），然后调用 `python test.py`，在命令行阅读代码输出结果。现在同理，你只需要调用 `subprocess` 模块，将本该输出到命令行的结果捕获到变量中，与预期输出比对即可。

#### 任务 2：支持多语言评测

> 本任务仅需额外实现 C++ 语言

- 在 Python 评测基础上，扩展支持 C++ 等其他语言。
- 需根据 `language` 字段自动选择编译/运行命令，C++ 需先编译再运行。
- 设计良好的语言配置与切换机制，便于后续扩展。

#### 任务 3：动态注册新语言
- 支持已登录用户动态注册新语言，便于系统扩展。

#### 任务 4：查询支持的语言列表
- 支持查询当前系统支持的所有编程语言。

---

### 评测流程说明

1. 读取题目信息：根据题目 id 获取输入输出样例和限制条件。
2. 接收用户代码：获取用户提交的代码及语言类型。
3. 运行与比对：将样例输入传递给用户代码，捕获输出并与标准答案比对。
4. 返回结果：以结构化方式返回评测状态、得分、编译信息、运行结果、错误信息、时间和内存等信息。

---

### 时间与内存限制要求

- 每道题目都应有 time limit（如 1 秒）和 memory limit（如 128MB）字段。
- 评测时，系统必须对用户代码的运行时间和内存消耗进行限制和监控。
- 超出限制时，评测结果应返回 TLE（Time Limit Exceeded，超时）或 MLE（Memory Limit Exceeded，超内存）。

#### 具体要求

1. 题目配置
   - 在题目 JSON 或数据库结构中，`time_limit` 和 `memory_limit` 字段可选，如果未设置的话，按照添加语言时的 `time_limit` 和 `memory_limit` 配置。
   - 示例：
     ```json
     {
       "id": "P1001",
       "title": "A+B Problem",
       ...
       "time_limit": 1.0,
       "memory_limit": 128
     }
     ```
2. 评测实现
   - 评测时，自动读取题目的时间和内存限制。
   - 运行用户代码时，必须设置相应的资源限制（如 Python 的 resource、subprocess，或 Linux ulimit）。
   - 若用户代码超时或超内存，应立即终止进程，并返回对应的评测状态（TLE/MLE）。
3. 评测结果
   - 评测接口的响应中，仅需返回最终评测结果即可，具体请参考 `api.md`。详细测试点状态会在 [Step5](https://dbg-course.github.io/python-docs/oj/project/step5/) 中实现。
   - 认为一个测试点 10 分

---

### 评分细则

| 功能/接口                | 分值 | 评分说明                         |
|--------------------------|------|----------------------------------|
| 多语言评测支持           | 2    | 评测流程支持多语言                |
| 动态注册新语言           | 1    | 支持动态注册、配置安全            |
| 查询支持语言列表         | 1    | 支持查询所有已注册语言            |
| 时间/内存限制实现        | 1    | 能正确限制并判定超时/超内存      |
| **小计**                 | **5**|                                  |

---

## Step3：评测列表

### 模块目标

实现评测任务的列表查询、单个评测详情、重新评测等功能，支持分页、筛选、权限控制。

---

### 前置知识要求

| 技术点         | 推荐学习内容           |
| -------------- | ---------------------- |
| 数据结构设计   | 列表、字典、分页       |
| REST API 设计  | GET/PUT 路由           |
| 权限控制       | 用户/管理员区分        |

---

### 任务分解

#### 任务 1：评测列表查询
- 目标：提供 API 查询评测任务列表，支持分页、筛选。
- 要点：可按用户、题目、状态等筛选，支持分页参数。

#### 任务 2：单个评测详情
- 目标：提供 API 查询单个评测任务的详细信息。
- 要点：需校验权限，仅本人或管理员可查；响应应包含评测状态、总分以及可供前端展示的编译信息、运行结果和错误信息。单个测试点的结果通过 Step 5 的评测日志接口查询。

#### 任务 3：重新评测
- 目标：管理员可对评测任务发起重新评测。
- 要点：需校验管理员权限，重新评测后状态变为 pending。

---

### 评分细则

| 功能/接口                | 分值 | 评分说明                         |
|--------------------------|------|----------------------------------|
| 评测列表查询接口         | 2    | 多条件筛选、分页                  |
| 单个评测详情接口         | 2    | 权限校验、响应结构                |
| 重新评测接口             | 1    | 权限、状态变更、异常              |
| **小计**                 | **5**|                                  |

---

## Step4：用户管理

### 模块目标

实现用户的注册、登录登出、信息查询、权限管理、用户列表等功能，支持权限控制和安全校验。

---

### 前置知识要求

| 技术点         | 推荐学习内容           |
| -------------- | ---------------------- |
| 数据结构设计   | 用户表、权限字段       |
| Session 管理 | Cookie, Session |
| REST API 设计  | GET/POST/PUT 路由      |
| 权限控制       | 用户/管理员区分        |

---

### 任务分解

#### 任务 0：用户登录/登出/初始管理员
- 目标：实现用户登录、登出接口，系统启动时自动创建初始管理员账户（账号为 `admin` / 密码为 `admintestpassword`）。

**Session 机制原理**

Session 是 Web 应用中维持用户状态的重要机制。由于 HTTP 协议是无状态的，服务器无法直接识别连续请求来自同一用户，因此需要 Session 来解决这个问题。

**工作流程：**
1. 用户首次访问时，服务器创建一个唯一的 Session ID
2. 服务器将 Session ID 通过 Cookie 发送给客户端
3. 客户端后续请求会自动携带这个 Cookie
4. 服务器根据 Session ID 查找对应的用户信息

**Session 存储方式：**
- **内存存储**：速度快，但服务器重启会丢失，不适合生产环境
- **文件存储**：持久化，但并发性能较差
- **数据库存储**：可靠性高，支持分布式部署
- **Redis 存储**：高性能，支持过期策略，是主流选择

**安全考虑：**
- Session ID 需要足够随机，防止被猜测
- 使用 HTTPS 传输 Cookie，防止被窃取
- 设置合理的过期时间，平衡用户体验和安全性
- 登出时要清除服务器端的 Session 数据

Session 相比 JWT 的优势是可以立即失效（服务器端删除），劣势是需要服务器端存储。建议查阅相关框架的 Session 文档，理解具体实现细节。

??? question "Session ID 生成"
    Session ID 用来唯一标记某个用户的某次会话，并且需要被服务器端存储，
    所以你需要保证拿到大规模不重复的 ID。

    可以使用 `uuid` 库的 `uuid4` 函数。

**中间件机制**

Web 框架通常使用中间件（Middleware）来处理 Session 管理。中间件是在请求处理过程中的拦截器，可以在请求到达路由处理函数之前或之后执行特定逻辑。

Session 中间件的工作原理：
1. 请求到达时，中间件从 Cookie 中读取 Session ID
2. 根据 Session ID 从存储中加载用户数据
3. 将用户信息附加到请求对象上
4. 请求处理完成后，中间件将 Session 数据保存回存储
5. 如果需要，更新 Cookie 中的 Session ID

这样设计的好处是业务代码无需关心 Session 的底层实现，只需要通过框架提供的接口访问用户信息即可。

**FastAPI Session 中间件示例**

```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

@app.post("/login")
async def login(request: Request):
    request.session["user_id"] = 1
    return {"message": "登录成功"}
```

建议查阅 Starlette 官方文档中的 [SessionMiddleware](https://www.starlette.io/middleware/#sessionmiddleware) 了解详细用法。

#### 任务 1：用户注册
- 目标：提供用户注册 API。

**数据验证与唯一性约束**

用户注册需要验证输入数据的有效性。主要检查用户名是否已存在、密码是否符合要求。

**基本验证要点：**
- 检查用户名长度（3-40 字符）
- 检查密码长度（最少 6 位）
- 查询数据库确认用户名未被使用
- 密码需要加密后存储（使用bcrypt库）

**处理流程：**
1. 接收用户名、密码参数
2. 验证格式是否正确
3. 检查用户名是否已存在
4. 加密密码并存储到数据库
5. 返回成功信息和用户ID

#### 任务 2：用户信息查询
- 目标：提供 API 查询用户信息。

**权限控制基础**

用户信息查询需要控制权限，确保用户只能查看自己的信息，管理员可以查看所有用户信息。

**权限检查流程：**
1. 从 session 中获取当前登录用户信息
2. 检查要查询的用户ID是否是当前用户自己
3. 或者检查当前用户是否是管理员
4. 如果权限不足，返回403错误
5. 如果权限充足，返回用户信息（不包含密码）

**返回数据：**

```json
{
  "code": 200, 
  "msg": "success", 
  "data": 
  {
    "total": 3, // 查询到的用户总数
    "users": 
    [
      {"user_id": "1", "join_time": "1924-08-17", "submit_count": 100, "resolve_count": 9},
      {"user_id": "2", "join_time": "1911-04-05", "submit_count": 90, "resolve_count": 8},
      {"user_id": "3", "join_time": "2012-07-14", "submit_count": 80, "resolve_count": 7},
    ]
  }
}
```

??? info "时间获取"
    你可以使用如下命令获取 f'{year}-{month}-{day}' 格式的时间
    ```python
    from datetime import datetime
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    ```

#### 任务 3：用户权限变更
- 目标：管理员可变更用户权限（如设为 admin/banned）。

如果用户被 ban，其再登录时会被阻止。

**管理员权限检查**

只有管理员可以修改用户权限，需要严格验证操作者身份。

**基本实现：**
1. 检查当前用户是否是管理员
2. 获取要修改的用户ID和新权限
3. 验证新权限值是否有效（如user、admin、banned）
4. 更新数据库中的用户权限
5. 记录操作日志（谁在什么时候修改了谁的权限）

!!! danger "权限提示"
    注意，在 step1 ~ step3 中，我们没有对题目上传 / 语言创建等进行权限控制。在添加用户权限后，我们需要更新之前的功能。为简化，我们规定为：题目上传 / 创建语言可以由任意用户执行，但是删除题目操作**仅管理员可执行**，暂不考虑删除语言。此外，你还需要修改之前的接口，在用户未登录时无法进行增删查改。

#### 任务 4：用户列表查询
- 目标：管理员可查询所有用户列表，支持分页、筛选。

**分页与筛选**

根据 API 文档，用户列表查询，支持分页参数。

**API 参数：**
- `page`（可选）：页码
- `page_size`（可选）：每页大小

**返回格式：**
```json
{
  "code": 200, 
  "msg": "success", 
  "data": 
  {
    "total": 3, // 查询到的用户总数
    "users": 
    [
      {"user_id": "1", "username": "xiaoming", "join_time": "1924-08-17", "submit_count": 100, "resolve_count": 9},
      {"user_id": "2", "username": "xiaohong", "join_time": "1911-04-05", "submit_count": 90, "resolve_count": 8},
      {"user_id": "3", "username": "xiaogang", "join_time": "2012-07-14", "submit_count": 80, "resolve_count": 7},
    ]
  }
}
```

---

### 评分细则

| 功能/接口                | 分值 | 评分说明                         |
|--------------------------|------|----------------------------------|
| 用户注册接口             | 2    | 路径、参数、响应、异常            |
| 用户信息查询接口         | 1    | 权限、响应、异常                  |
| 用户权限变更接口         | 1    | 权限、参数、响应、异常            |
| 用户列表查询接口         | 1    | 分页、筛选、权限                  |
| **小计**                 | **5**|                                  |

---

## Step5：日志与权限

### 模块目标

- 实现评测日志的记录与查询，提升系统可追溯性和调试能力。
- 增加细粒度权限管理，如是否允许用户查看评测日志、测例详情等。
- 支持管理员对日志和权限的管理与审计。

---

### 前置知识要求

| 技术点         | 推荐学习内容           |
| -------------- | ---------------------- |
| 日志设计       | 日志结构、存储与查询   |
| 权限控制       | 角色权限、接口校验     |
| REST API 设计  | GET 路由、权限参数     |

---

### 任务分解

#### 任务 1：评测日志记录与查询
- 目标：为每次评测任务记录日志。
- 要点：日志应与评测任务关联，支持按 `submission_id` 查询。

> 为简化，评测日志可见性变为公开后，所有登录的人都能看到这个评测的日志，但是没权限的用户仍对 `Step 2 & 3` 中评测的简单结果不可见

#### 任务 2：日志权限管理
- 目标：实现细粒度权限控制，决定哪些用户可以查看哪些日志内容。
- 要点：
  - 普通用户仅能查看自己的评测日志。
  - 管理员可查看所有日志。
  - 可扩展"允许公开日志"功能，支持题目设置是否允许**所有用户**查看日志详情。

#### 任务 3：权限配置与审计
- 目标：支持管理员配置日志的可见性策略，并能审计用户的日志访问行为。
- 要点：权限配置可针对题目、用户角色等维度，审计日志记录用户的访问操作。

---

### 评分细则

| 功能/接口                | 分值 | 评分说明                         |
|--------------------------|------|----------------------------------|
| 日志记录与查询           | 2    | 日志结构、查询接口、内容裁剪      |
| 日志/测例权限管理        | 2    | 权限配置、接口校验                |
| 审计与安全说明           | 1    | 日志访问审计        |
| **小计**                 | **5**|                                  |

---

## Step6：前端交互

> 本模块不要求掌握 JavaScript、HTML、CSS 等前端技术，要求使用 Python 的 `streamlit` 库实现前端页面，并通过 REST API 与 FastAPI 后端交互。

### 什么是 Streamlit？

Streamlit 是一个使用 Python 快速开发 Web 应用的开源框架。它提供表单、按钮、输入框、文件上传等常用组件，适合用于构建课程项目的交互界面。应用可通过以下命令启动：

```bash
streamlit run app.py
```

本模块要求实现一个与 OJ 后端配套的前端，覆盖用户、题目和评测提交三组页面。前端应调用前述模块实现的 API，不应绕过后端直接读写后端数据。

---

### 模块目标

- 实现 OJ 系统的基本前端页面，为用户管理、题目管理和评测提交提供可操作的图形界面。
- 完成前端与 FastAPI 后端的接口对接，正确处理身份状态、请求参数、响应数据和异常信息。
- 保证页面功能与前述模块的 API 行为一致。

---

### 前置知识要求

| 技术点 | 推荐学习内容 |
| ------ | ------------ |
| Streamlit 基础 | 页面布局、表单、按钮、输入组件、`session_state` |
| REST API 调用 | HTTP 方法、请求参数、JSON 响应、异常处理 |
| Cookie / Session | 登录状态保存、身份信息传递 |
| 前后端交互 | 页面状态与后端数据的同步 |

---

### 任务分解

#### 任务 1：用户页面组

实现与用户系统相关的页面。相关页面的内容至少包括：

- 用户注册；
- 用户登录和退出；
- 用户信息展示；
- 用户管理。

只有登录后用户才能进行题目提交、结果查询等操作，需安全地保存身份信息。前端需要实现登录表单，调用后端登录 API，完成用户身份认证。

- 实现建议：
  - 可用 session_state 或本地文件存储 token。
  - 登录失败时给出友好提示。

用户管理页面仅应向具备相应权限的管理员提供。页面应根据登录状态和用户角色展示可执行的操作，并正确处理未登录、权限不足、用户被禁用等情况。

#### 任务 2：题目页面组

实现与题目管理相关的页面。相关页面的内容至少包括：

- 题目列表；
- 题目详情；
- 题目新增；
- 题目编辑；
- 题目删除。

题目表单应覆盖题目配置所需字段，并在提交前进行必要的格式检查。题目删除等受限操作应遵循后端权限要求。

#### 任务 3：评测与提交页面组

实现与代码提交和评测结果查询相关的页面。相关页面的内容至少包括：

- 代码提交；
- 提交记录列表；
- 提交记录详情；
- 评测状态；
- 编译信息、运行结果和错误信息。

用户需要通过网页提交代码，并能实时查看评测状态和结果。前端需实现代码提交表单，调用后端提交 API，并展示评测结果。

- 实现建议：
  - 使用 streamlit 的文本框、下拉框等组件收集题号、语言、代码内容。
  - 调用后端提交 API，获取 submission_id。
  - 轮询或手动查询 submission_id 的评测状态与结果，并展示。

提交后，页面应能够展示任务当前状态，并在评测完成后展示后端允许当前用户查看的结果。对于编译失败、运行错误、超时等情况，应提供明确的状态和错误提示。

#### 任务 4：前端与后端接口对接

前后端分离架构下，所有数据流转均依赖 API，需保证参数、路径、状态码一致。应确保所有前端操作均通过 REST API 与后端交互，并严格遵循 [API 文档](https://dbg-course.github.io/python-docs/oj/api/)中的接口规范。

实现时应注意：

- 可封装统一的 API 调用函数，集中处理请求、身份信息和异常；
- 正确保存和传递登录会话，不得在页面代码中硬编码用户身份；
- 根据 HTTP 状态码和响应中的 `code` 字段展示成功或失败信息；
- 页面状态应与后端数据保持一致，不应仅在前端模拟操作结果。

---

### 评分细则

| 功能/接口 | 分值 | 评分说明 |
| --------- | ---- | -------- |
| 用户页面组 | 2 | 注册、登录/退出、用户信息、角色管理 |
| 题目页面组 | 1 | 题目列表、详情、新增、编辑、删除 |
| 评测与提交页面组 | 1 | 代码提交、记录查询、状态及运行信息展示 |
| 前端与后端接口对接 | 1 | API 调用、会话传递、响应与异常处理 |
| **小计** | **5** | |

---

## Advance：AI 智能命题

### 模块目标

程序设计训练（Python）课程的教师与助教需要根据每节课的教学内容设计配套 OJ 题目。命题过程通常包含知识点梳理、难度控制、题面编写、测试点构造以及题目测试等多个环节，需要投入较多时间。

本模块要求开发 AI 智能命题功能，辅助课程教师与助教完成每节课的 OJ 出题工作。命题人员可以输入题目必须覆盖的知识点、预期难度以及其他不同维度的要求；系统应能够据此独立完成题目设计、题目配置生成和测试点生成等多个环节，生成可用于 OJ 题目新增或编辑的完整结果。

本模块不限定具体的页面结构、任务流程或技术方案。实现可以围绕真实命题需求扩展检索、脚本执行、测试数据生成等能力。

---

### 前置知识要求

| 技术点 | 推荐学习内容 |
| ------ | ------------ |
| 大语言模型 API | HTTP 请求、JSON 数据、模型输入与输出 |
| 模型配置 | 提供商 URL、模型名称、模型密钥 |
| 异步任务 | 后台任务、任务状态管理、异常处理 |
| 实时通信 | 流式响应、SSE、WebSocket 或状态轮询 |
| 用量统计 | 输入/输出 Token、模型价格与费用计算 |
| 配置安全 | API 密钥等敏感信息的保存与使用 |

上述内容不限定具体框架或实现协议，可参考程序设计训练（Rust）课程的 [Agent 架构](https://lab.cs.tsinghua.edu.cn/rust/projects/agent/agent-architecture/)了解相关概念。

---

### 基本功能要求

#### R1. 出题交互界面

系统应提供可操作的 AI 智能命题界面。可以在基础模块的题目新增、题目编辑页面上扩展相关功能，也可以新增独立的 AI 智能命题页面。

界面应能够提交命题需求、展示处理状态和结果，并支持将所得内容用于后续的题目新增、审阅或修改。具体交互形式不作统一限制。

#### R2. 可自定义模型配置

系统应支持配置以下模型信息：

- 提供商 URL；
- 模型名称；
- 模型密钥。

配置结果应实际应用于后续模型请求，不得将服务提供商、模型名称或模型密钥固定在程序代码中。模型密钥属于敏感信息，不应在日志、页面响应或错误信息中明文泄露。

#### R3. 实时进度渲染和中断功能

AI 智能命题任务执行期间，界面应持续展示可观察的进度信息，不得仅在任务全部完成后返回最终结果。

系统应提供任务中断功能。中断操作应能够实际终止当前任务或阻止其继续执行，并在界面中明确展示任务已中断的状态。具体可采用流式响应、SSE、WebSocket、轮询等方式实现，不限定技术方案。

#### R4. Token 用量与价格统计

系统应统计模型调用产生的 Token 用量，并根据相应的模型价格计算调用费用。统计结果应在界面中清晰展示，至少能够反映当前任务的 Token 用量和费用。

若模型接口能够分别返回输入 Token 和输出 Token，应分别记录和展示。费用统计应说明所采用的计价依据；模型接口不提供完整用量信息时，应明确标注统计方式及其限制。

---

### 设计参考

以下示例用于说明本模块关注的设计方向，不限定具体实现方式，也不要求采用其中列出的全部功能。

#### 正例

##### 示例一：通过多次迭代完善题目

允许 AI 按照相应改编要求修改已生成题目（或者其他已有题目）。例如，调整题目的背景与考察内容、修改/加强测试用例，或在保留原有考查目标的基础上设计新的题目情境。

该设计允许 AI 通过多次迭代逐渐完成命题任务，出题人可以根据当前结果继续提出修改要求。具体的迭代流程和交互形式应根据实际设计确定。

##### 示例二：通过工具扩展能力

为 AI 提供若干与命题场景相关的可调用工具。例如，通过 Web 检索相关题目设计资料，或通过服务器 CLI 编写并运行测试数据生成脚本。

该设计利用外部工具扩展模型能力，使系统能够完成单纯文本生成以外的命题任务。工具的选择、权限和执行范围应根据实际设计确定。

#### 反例

##### 示例三：与基础功能相互割裂

仅在页面中添加“AI 出题”按钮，触发后返回一个包含题目信息的压缩包。

该功能与已有题目管理模块相互割裂，所得内容不能便捷地进入题目审阅、编辑或维护流程。

##### 示例四：未能有效辅助命题

AI 功能只能完成单一的文本生成，或者所得题目与输入的知识点、约束条件明显无关。

该功能未能有效处理所声明的命题需求，出题的主要工作仍需人工重新完成。

---

### 评分标准

本模块满分为 10 分。

| 评分项 | 分值 | 评分内容 |
| ------ | ---: | -------- |
| R1. 出题交互界面 | 1 | 是否提供完整、可操作的 AI 智能命题界面；是否能够提交需求、展示结果，并与题目新增或修改等操作合理衔接 |
| R2. 可自定义模型配置 | 1 | 是否支持配置提供商 URL、模型名称和模型密钥；配置是否实际应用于模型请求 |
| R3. 实时进度渲染和中断功能 | 1 | 是否能够实时展示任务进度；是否能够有效中断正在执行的任务，并正确反馈任务状态 |
| R4. Token 用量与价格统计 | 1 | 是否能够统计并清晰展示 Token 用量和模型调用费用；费用计算依据是否明确 |
| 题目合理性 | 2 | AI 智能命题生成的题目是否满足真实课程要求，是否符合输入的知识点、难度及其他命题要求 |
| 测试用例有效性 | 2 | 测试用例是否覆盖不同边界条件，数据规模和构造是否能有效区分用户提交的不同时间复杂度算法 |
| 功能易用性 | 2 | 交互流程是否符合使用习惯，操作是否便捷，功能状态和结果展示是否清晰 |
| **合计** | **10** | |

---

# API 文档

---

## 目录
1. 题目管理相关接口（Step 1）
2. 评测相关接口（Step 2 & 3）
3. 用户管理相关接口（Step 4）
4. 评测日志相关接口（Step 5）
5. 前端交互说明（Step 6）
6. AI 智能命题接口（Advance）
7. 安全性说明

---

**系统初始化说明**：系统启动时会自动创建初始管理员账户，用户名为 `admin`，密码为 `admintestpassword`（请注意校验要求）。

---

## 状态码与异常

| HTTP 状态码 | 说明           | 示例场景           |
|-------------|----------------|--------------------|
| 200         | 正常           | 一切正常           |
| 400         | 参数错误       | 缺少/错误参数      |
| 401         | 未登录         | 窃取 API 参数        |
| 403         | 权限不足/禁用  | banned 用户/无权限 |
| 404         | 资源不存在     | 题目/评测不存在    |
| 409         | 资源状态冲突   | id 已存在/任务已经结束 |
| 429         | 频率超限       | 1min 内提交超过 3 次       |
| 500         | 服务器异常     | 未知错误           |

说明：

- API 异常处理顺序为 **401 > 403 > 400 > 429 > 409 > 404 > 500**
- 所有 API 接口的 JSON 响应都必须包含 `code` 字段，该字段的值应与 HTTP 状态码保持一致
- 服务器必须设置对应的 HTTP 状态码（不能全部返回 200）
- 错误响应格式应该类似：
```json
{"code": 404, "msg": "problem not found", "data": null}
```

---

## 1. 题目管理相关接口（Step 1）

### 查看题目列表
- 路径：`GET /api/problems/`
- 权限：所有已登录用户
- 响应：
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {"id": "sum_2", "title": "两数之和"},
    {"id": "max_num", "title": "最大数"}
  ]
}
```

### 添加题目
- 路径：`POST /api/problems/`
- 权限：所有已登录用户
- 参数（参考 Step1 文档）：
  - `id` (str, 必填): 题目唯一标识
  - `title` (str, 必填): 题目标题
  - `description` (str, 必填): 题目描述
  - `input_description` (str, 必填): 输入格式说明
  - `output_description` (str, 必填): 输出格式说明
  - `samples` (list, 必填): 样例输入输出，元素为 {input, output}
  - `constraints` (str, 必填): 数据范围和限制条件
  - `testcases` (list, 必填): 测试点，元素为 {input, output}
  - `hint` (str, 可选): 额外提示
  - `source` (str, 可选): 题目来源
  - `tags` (list, 可选): 题目标签
  - `time_limit` (float, 可选): 时间限制，默认单位为 "s"，默认值为 "3"
  - `memory_limit` (int, 可选): 内存限制，默认单位为 "MB"，默认值为 "128"
  - `author` (str, 可选): 题目作者
  - `difficulty` (str, 可选): 难度等级
- 响应：
```json
{"code": 200, "msg": "add success", "data": {"id": "sum_2"}}
```
- 异常：400 字段缺失/格式错误 / 401 未登录 (Step 4) / 409 id 已存在

### 编辑题目
- 路径：`PUT /api/problems/{problem_id}`
- 权限：所有已登录用户
- 参数：与添加题目的字段一致。路径中的 `problem_id` 表示待编辑题目；请求体中的 `id` 必须与其一致。
- 说明：使用请求体中的题目配置更新原题目。字段校验规则与添加题目相同。
- 响应：
```json
{"code": 200, "msg": "update success", "data": {"id": "sum_2"}}
```
- 异常：400 字段缺失、格式错误或 id 不一致 / 401 未登录 / 404 题目不存在

### 删除题目
- 路径：`DELETE /api/problems/{problem_id}`
- 权限：仅管理员
- 参数：无（URL 路径参数：`problem_id`）
- 响应：
```json
{"code": 200, "msg": "delete success", "data": {"id": "sum_2"}}
```
- 异常：401 未登录 (Step 4) / 403 权限不足 / 404 题目不存在

### 查看题目信息
- 路径：`GET /api/problems/{problem_id}`
- 权限：所有已登录用户
- 响应：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": "P1001",
    "title": "A+B Problem",
    "description": "输入两个整数 a, b，输出它们的和（|a|,|b| <= 10^9）。",
    "input_description": "输入两个整数 a 和 b。",
    "output_description": "输出 a+b 的结果。",
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
    "hint": "有负数哦！",
    "source": "洛谷",
    "tags": ["基础题"],
    "time_limit": 1.0,
    "memory_limit": 128,
    "author": "Luogu",
    "difficulty": "入门"
  }
}
```
- 异常：401 未登录 (Step4) / 403 权限不足 / 404 题目不存在
-  默认字段需要返回本类型默认值，比如 `str` 类需返回 `""`，`list` 类需返回 `[]`

---

## 2. 评测相关接口（Step 2 & 3）

> Step 2 和 Step 3 的查询评测结果接口返回评测状态、总分以及必要的编译或错误信息；单个测试点的结果、时间和内存信息通过 Step 5 的评测日志接口查询。评测列表只返回用于列表展示的摘要信息。

### 提交评测
- 路径：`POST /api/submissions/`
- 参数：
  - `problem_id` (str, 必填): 题目编号
  - `language` (str, 必填): 语言（如 "python", "cpp"）
  - `code` (str, 必填): 用户代码内容
- 权限：登录用户
- 响应：
```json
{
  "code": 200,
  "msg": "success",
  "data": {"submission_id": "123", "status": "pending"}
}
```
- 异常：400 参数错误 / 401 未登录 (Step 4) / 403 权限不足 / 404 题目不存在 & 语言不存在 / 429 提交频率超限

### 查询评测结果
- 路径：`GET /api/submissions/{submission_id}`
- 权限：仅本人或管理员
- 响应：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "submission_id": "123",
    "status": "success",
    "score": 10, // 本题获得分数
    "counts": 30, // 本题总分数（测试点数目 * 10）
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
- `compile_info` 用于返回编译是否成功及编译器信息；解释型语言可返回 `null`。
- `run_info` 用于返回程序运行阶段的总体结果；各测试点的详细结果仍通过评测日志接口查询。
- `error_info` 用于返回评测任务级别的错误信息。不得在其中泄露服务器敏感路径、密钥等信息。
- `pending` 状态至少返回 `submission_id` 和 `status`；尚未产生的字段可返回 `null`。
- 异常：401 未登录 (Step 4) / 403 权限不足 / 404 评测不存在

### 查询评测列表
- 路径：`GET /api/submissions/`
- 参数：`user_id`、`problem_id`、`status`、`page`、`page_size`
> 这五个参数均可选，其中 `user_id`、`problem_id` 为一级条件，其余为二级条件。一级条件不可以全部为空。
> 如果 `page` 和 `page_size` 全为空，表明查询所有数据；`page` 为空但 `page_size` 不为空表明选择第一页数据；需要认为 `page` 非空但 `page_size` 为空的情况属于参数错误。
> 如果未提供 `user_id`，那么管理员可查看此问题所有同学的记录，普通用户尽可查看此题自己的提交记录。
- 权限：本人/管理员
- 响应：
```json
{
  "code": 200,
  "msg": "success",
  "data": 
  {
    "total": 100, // 查询到的评测总数
    "submissions": 
    [
      // 如果 status 是 error / pending，则只需要返回 submission_id 和 status
      {"submission_id": "1", "status": "success", "score": 10, "counts": 30},
      {...}
    ]
  }
}
```

### 重新评测
- 路径：`PUT /api/submissions/{submission_id}/rejudge`
- 重新评测需覆盖原 `submission_id` 对应的内容
- 权限：仅管理员
- 参数：无（URL 路径参数：`submission_id`）
- 响应：
```json
{"code": 200, "msg": "rejudge started", "data": {"submission_id": "1", "status": "pending"}}
```
- 异常：401 未登录 (Step 4) / 403 权限不足 / 404 评测不存在

### 动态注册新语言 (Step 2)
- 路径：`POST /api/languages/`
- 参数：
  - `name` (str, 必填): 语言名称
  - `file_ext` (str, 必填): 代码文件扩展名
  - `compile_cmd` (str, 可选): 编译命令
  - `run_cmd` (str, 必填): 运行命令
  - `time_limit` (float, 可选): 默认单位为 "s"
  - `memory_limit` (int, 可选): 默认单位为 "MB"
- 权限：所有已登录用户
- 响应：
```json
{"code": 200, "msg": "language registered", "data": {"name": "go"}}
```
- 异常：400 参数错误 / 401 未登录 (Step 4) / 403 用户无权限

- 示例：
```json
{
  "name": "cpp",
  "file_ext": ".cpp",
  "compile_cmd": "g++ {src} -o {exe}", // 请注意，这里的 src 和 exe 需要是路径（如 test.cpp 不是路径，但是 ./test.cpp 或 /root/test.cpp 是路径）
  "run_cmd": "{exe}",
  "time_limit": 1.0,
  "memory_limit": 128
}
```
```json
{
  "name": "python",
  "file_ext": ".py",
  "run_cmd": "python3 {src}",
  "time_limit": 1.0,
  "memory_limit": 128
}
```

### 查询支持语言列表 (Step 2)
- 路径：`GET /api/languages/`
- 响应：
```json
{"code": 200, "msg": "success", "data": {"name": ["python", "cpp"]}}
```

---

## 3. 用户管理相关接口（Step 4）

### 用户登录
- 路径：`POST /api/auth/login`
- 参数：`username` (str, 必填), `password` (str, 必填)
- 响应：
```json
{"code": 200, "msg": "login success", "data": {"user_id": "1", "username": "alice", "role": "user"}}
```
- 异常：400 参数错误 / 401 用户名或密码错误 / 403 用户被禁用（Step 4）

### 用户登出
- 路径：`POST /api/auth/logout`
- 参数：无
- 权限：登录用户
- 响应：
```json
{"code": 200, "msg": "logout success", "data": null}
```
- 异常：401 未登录

### 创建管理员账户
- 路径：`POST /api/users/admin`
- 参数：`username` (str, 必填), `password` (str, 必填)
- 权限：仅管理员
- 响应：
```json
{"code": 200, "msg": "success", "data": {"user_id": "2", "username": "new_admin"}}
```
- 异常：400 用户名已存在 & 参数错误 / 401 未登录 (Step 4) / 403 用户无权限

### 用户注册
- 路径：`POST /api/users/`
- 参数：
  - `username` (str, 必填): 用户名
  - `password` (str, 必填): 密码
- 响应：
```json
{
  "code": 200, 
  "msg": "register success", 
  "data": 
  {
    "user_id": "1",
    "username": "xiaogang",
    "join_time": "2012-07-14", 
    "role": "user",
    "submit_count": 0,  // 用户提交数（按提交算，一个 problem 可贡献多次）
    "resolve_count": 0 // 用户通过数（按题目算，一个 problem 最多贡献一次）
  }
}
```
- 异常：400 用户名已存在 & 参数错误

### 查询用户信息
- 路径：`GET /api/users/{user_id}`
- 权限：仅本人或管理员
- 响应：
```json
{
  "code": 200, 
  "msg": "success", 
  "data": 
  {
    "user_id": "1",
    "username": "alice", 
    "join_time": "2012-07-14", 
    "role": "user",
    "submit_count": 80, 
    "resolve_count": 7
  }
}
```
- 异常：401 用户未登录 / 403 用户无权限 / 404 用户不存在

### 用户权限变更
- 路径：`PUT /api/users/{user_id}/role`
- 参数：
  - `role` (str, 必填): 新角色（如 "admin", "user", "banned"）
- 权限：仅管理员
- 响应：
```json
{"code": 200, "msg": "role updated", "data": {"user_id": "1", "role": "admin"}}
```
- 异常：400 参数错误 / 401 用户未登录 / 403 用户无权限 / 404 用户不存在 

### 用户列表查询
- 路径：`GET /api/users/`，参数：`page`、`page_size`（可选）
- 参数意义与 `GET /api/submissions/` 一致
- 权限：仅管理员
- 响应：
```json
{
  "code": 200, 
  "msg": "success", 
  "data": 
  {
    "total": 3, // 查询到的用户总数
    "users": 
    [
      {"user_id": "1", "username": "xiaoming", "role": "user", "join_time": "1924-08-17", "submit_count": 100, "resolve_count": 9},
      {"user_id": "2", "username": "xiaohong", "role": "user", "join_time": "1911-04-05", "submit_count": 90, "resolve_count": 8},
      {"user_id": "3", "username": "xiaogang", "role": "user", "join_time": "2012-07-14", "submit_count": 80, "resolve_count": 7},
    ]
  }
}
```
- 异常：400 参数错误 / 401 用户未登录 / 403 用户无权限 / 404 用户不存在

---

## 4. 评测日志相关接口（Step 5）

### 查询评测日志
- 路径：`GET /api/submissions/{submission_id}/log`
- 权限：仅本人（如果没有公开）或管理员
- 响应：
```json
{
  "code": 200, 
  "msg": "success", 
  "data": {
    "details": [ // 管理员可见 details；仅当该评测对应问题 public_cases 设置为 True 时用户可见
      {"id": 1, "result": "AC", "time": 1.01, "memory": 130},
      {"id": 2, "result": "TLE", "time": 1.01, "memory": 130},
      {"id": 3, "result": "MLE", "time": 1.01, "memory": 130},
    ],
    "score": 10,
    "counts": 30, // 总分数
  }
}
```
- 异常：400 参数错误 / 401 用户未登录 / 403 用户无权限 / 404 评测不存在

### 配置日志可见性
- 路径：`PUT /api/problems/{problem_id}/log_visibility`
- 权限：仅管理员
- 参数：
  - `public_cases` (bool，选填，默认为 False): 日志是否向所有人公开
- 响应：
```json
{
  "code": 200,
  "msg": "log visibility updated",
  "data": {"problem_id": "sum_3_numbers", "public_cases": True}
}
```
- 异常：400 参数错误 / 401 用户未登录 / 403 用户无权限 / 404 题目不存在

### 日志访问审计
- 路径：`GET /api/logs/access/`
- 权限：仅管理员
- 其中 `status` 作为返回值，记录这次访问状态
- 不必记录未登录 / `submission` 不存在 / 参数错误时访问记录。
- 参数：
  - `user_id` (str, 可选)：按用户筛选
  - `problem_id` (str, 可选)：按题目筛选
  - `page` (int, 可选)：页码
  - `page_size` (int, 可选)：每页数量
- 参数意义与 `GET /api/submissions/` 一致
- 请注意，这里的 `action` 只有 `view_logs` 一个操作
- 响应：
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {"user_id": "test", "problem_id": "sum_3_numbers", "action": "view_log", "time": "2024-06-01", "status": "403"} // 这次访问用户无权限
  ]
}
```
- 异常：400 参数错误 / 401 用户未登录 / 403 用户无权限

---

## 5. 前端交互说明（Step 6）

Step 6 不新增一套独立的业务数据接口。前端应调用 Step 1 至 Step 5 已定义的接口完成相应操作。

| 页面组 | 主要接口 |
| ------ | -------- |
| 用户页面组 | `POST /api/users/`、`POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/users/{user_id}`、`PUT /api/users/{user_id}/role` |
| 题目页面组 | `GET /api/problems/`、`GET /api/problems/{problem_id}`、`POST /api/problems/`、`PUT /api/problems/{problem_id}`、`DELETE /api/problems/{problem_id}` |
| 评测与提交页面组 | `POST /api/submissions/`、`GET /api/submissions/`、`GET /api/submissions/{submission_id}`、`GET /api/submissions/{submission_id}/log` |

前端应根据接口的 HTTP 状态码和 `{code, msg, data}` 响应结构展示操作结果。登录会话、用户角色和资源可见性均以后端判断为准，不能仅依赖前端隐藏按钮实现权限控制。

### 测试支持：系统重置

系统重置接口供自动测试恢复初始环境使用，不属于 Step 6 的评分内容。

- 路径：`POST /api/reset/`
- 权限：仅管理员（测试环境可不校验）
- 参数：无
- 响应：
```json
{"code": 200, "msg": "system reset successfully", "data": null}
```
- 异常：401 用户未登录 / 403 权限不足
- 说明：清空测试产生的用户、题目和提交数据，退出当前登录状态，并重新创建初始管理员账户。

---

## 6. AI 智能命题接口（Advance）

AI 智能命题的页面结构和技术方案不作统一限制。以下接口用于说明 R1 至 R4 所需的数据交互，可按照项目设计采用等价的路径、传输协议或字段结构；采用不同设计时，应在项目文档中说明接口及其行为。

### 模型配置

- 建议路径：`PUT /api/ai/model-config`
- 权限：已登录用户
- 参数：
  - `provider_url` (str, 必填)：模型提供商 URL
  - `model` (str, 必填)：模型名称
  - `api_key` (str, 必填)：模型密钥
  - `input_price` (float, 可选)：输入 Token 单价
  - `output_price` (float, 可选)：输出 Token 单价
  - `price_unit` (int, 可选)：计价 Token 数量单位，如 `1000000`
- 响应示例：
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

模型密钥不得通过查询接口或普通响应返回。若系统保存模型密钥，应采取与其敏感程度相适应的保护措施。

### 创建智能命题任务

- 建议路径：`POST /api/ai/problem-tasks/`
- 权限：已登录用户
- 参数：
  - `requirement` (str, 必填)：本次命题需求
  - `problem_id` (str, 可选)：需要参考或修改的已有题目编号
  - 其他与项目功能相关的参数
- 响应示例：
```json
{
  "code": 200,
  "msg": "task created",
  "data": {"task_id": "ai-task-1", "status": "pending"}
}
```
- 异常：400 参数错误 / 401 用户未登录 / 404 指定题目不存在 / 500 服务器异常

### 查询任务状态和结果

- 建议路径：`GET /api/ai/problem-tasks/{task_id}`
- 权限：任务创建者或管理员
- 响应示例：
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

任务状态至少应能区分等待、执行、完成、中断和失败。任务完成后，`result` 返回值应能够被出题界面使用；具体结构由项目设计确定。

### 实时进度

可通过流式响应、SSE、WebSocket 或轮询实现实时进度。采用 SSE 时，可参考：

- 建议路径：`GET /api/ai/problem-tasks/{task_id}/events`
- 权限：任务创建者或管理员
- 事件示例：
```text
event: progress
data: {"task_id":"ai-task-1","status":"running","message":"正在处理命题需求"}

event: usage
data: {"input_tokens":1200,"output_tokens":350,"total_tokens":1550,"cost":0.0019,"currency":"USD"}
```

### 中断任务

- 建议路径：`PUT /api/ai/problem-tasks/{task_id}/cancel`
- 权限：任务创建者或管理员
- 响应示例：
```json
{
  "code": 200,
  "msg": "task cancelled",
  "data": {"task_id": "ai-task-1", "status": "cancelled"}
}
```
- 异常：401 用户未登录 / 403 用户无权限 / 404 任务不存在 / 409 任务已经结束

中断操作应实际终止任务或阻止任务继续执行，而不是只停止前端的进度展示。

### Token 用量与价格

统计结果至少包含当前任务的 Token 用量和费用。输入、输出 Token 采用不同单价时，可按以下方式计算：

```text
费用 = 输入 Token 数 / 计价单位 × 输入单价
     + 输出 Token 数 / 计价单位 × 输出单价
```

模型接口不能提供完整 Token 用量时，应在页面和项目文档中说明所采用的统计或估算方式。

---

## 7. 安全性说明

系统实现时需要注意相关的安全性要求，包括但不限于：

- 对请求参数、上传内容和模型返回数据进行必要校验；
- 所有权限判断均在后端完成，不能以前端是否显示操作入口代替权限校验；
- 密码和模型密钥等敏感信息不得明文记录在日志中，也不得通过普通查询接口返回；
- 调用外部模型服务时应处理超时、失败和异常响应，避免任务长期占用资源；
- 如实现外部工具调用，应限制可用工具和参数范围，并对文件写入、命令执行等有副作用的操作进行安全控制。

---

# 评分标准

共50分，其中实验功能验收占40分，代码规范5分，实验报告5分。本次作业最终会按照比例缩放到总评30%。

## 时间节点

1. OJ 系统的功能实现，在**9月10日（周四）**由助教线下验收（验收形式后续通知，参考第一次大作业）。
2. 助教会为每位同学创建好仓库。所有源代码需要在**9月10日（周四）课前完成**，需在网络学堂提交最后一次 git commit 号。
3. 实验报告在 **9月10日（周四）晚上23:59** 在网络学堂截止提交。
4. **作业原则上不接受补交。**需要有足够的原因（如医学证明）才能接受补交，且每人仅有一次补交机会。

**逾期未参加验收，实验功能部分记零分。请同学们务必按时参加验收！如遇到极特殊情况，请及时联系助教。**

---

## 实验功能

以下评分标准均建立在正确使用fastapi的异步编程接口上，不使用异步编程的无法拿到本次作业分数。

### 基础模块（共 30 分）

| 模块 | 主要评分点 | 分值 |
| ---- | ---------- | ---- |
| Step 1 题目管理 | 题目配置加载、校验与增删改查 | 5 |
| Step 2 评测控制 | 程序执行与资源限制 | 5 |
| Step 3 评测管理 | 提交记录查询、状态管理与重新评测 | 5 |
| Step 4 用户管理 | 用户注册、登录与权限管理 | 5 |
| Step 5 评测日志 | 测试点明细、可见性与访问审计 | 5 |
| Step 6 前端交互 | 用户、题目、评测提交页面及前后端接口对接 | 5 |

### 进阶模块（共 10 分）

| 模块 | 主要评分点 | 分值 |
| ---- | ---------- | ---- |
| AI 智能命题 | R1–R4、题目合理性、测试用例有效性与功能易用性 | 10 |

---

### 代码规范（5分）

参考第一次爬虫大作业，另外，本次对git提交会做更详尽的检查。请同学们正确使用git，**避免将大文件提交到git，这将会是扣分项**。

**Git 提交规范**：要求尽量按照 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 规范编写提交信息，不符合规范的提交将酌情扣分。提交信息应包含类型（如 feat、fix、docs 等）和简洁的描述。

---

### 实验报告（5分）

| 评分点 | 分值 | 达标标准 |
| ------ | ---- | -------- |
| 系统功能与设计 | 2 | 介绍系统架构、主要功能、技术选型、模块划分 |
| 关键实现与难点 | 2 | 说明关键技术实现、遇到的难点与解决方案 |
| 成果展示    | 1 | 展示系统效果、边界测试结果 |
| AI使用说明     | 0 | 介绍 AI 使用的工具链、工作流和 Vibe Coding 的代码比例等 |
| 总结与建议     | 0 | 反思收获、改进建议、时间投入等 |

- 报告建议为PDF，结构清晰，图文并茂。

---

## 扣分项（视情节严重程度）

> 本次作业允许使用 Vibe Coding，但这并不意味着可以忽视对代码架构和基本原理的理解。我们鼓励同学们在掌握基本原理和代码结构的基础上，借助 Vibe Coding 完成更现代化、更完整的作业。此外，对于使用 Vibe Coding 的同学，需要在报告中提交一份 AI 使用说明。

- 抄袭/作弊，0分处理。
- 未按时参加验收的，功能部分记零分。
- 代码/报告严重缺失，或未按要求提交，酌情扣分。
- 代码/报告与演示内容不符，酌情扣分。

---

**预祝大家项目顺利😁！**

---

# FAQ

> 此处收集 OJ 系统实验常见问题，持续补充中

## FastAPI 的参数校验在实际逻辑之前，导致 `422` 会比其他错误优先？

可使用 `Depends` 解决~ 参考

```python
from fastapi import Request, Depends, HTTPException, status
from fastapi.routing import APIRouter
import json
from models import ProblemModel
from services import auth, problem_ops

router = APIRouter()

@router.post("/api/problems/")
async def router_add_problem(
    request: Request,
    current_user=Depends(auth.get_current_user), # !!!!
):
    body = await request.body()
    try:
        body_data = json.loads(body)
        problem = ProblemModel(**body_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid body: {e}")

    await problem_ops.file_save_problem(problem.id, problem.model_dump())
    return {"code": 200, "msg": "add success", "data": {"id": problem.id}}
```


## API 要求返回 `400`，但是 FastAPI 默认返回 `422`？

可添加中间件解决~ 参考

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

class TestModel(BaseModel):
    name: str
    age: int

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Request body has validation errors", "errors": exc.errors()},
    )

@app.post("/items/")
async def create_item(item: TestModel):
    return item
```

## 评测日志中，测例详情是什么？

请大家区分一次评测和一个测例。测例是指 `test case`，即评测时的一组输入输出。一次评测中，评测结果类似

```json
"submissions": [
  {
    "submission_id": "1",
    "user_id": "1",
    "problem_id": "sum_2",
    "language": "python",
    "code": "a, b = map(int, input().split())\nprint(a + b)",
    "details": [
      {"id": 1, "result": "AC", "time": 1.01, "memory": 130},
      {"id": 2, "result": "AC", "time": 1.01, "memory": 130}
    ],
    "score": 100,
    "counts": 100,
  }
]
```

其中，一个测例是指 `{"id": 1, "result": "AC", "time": 1.01, "memory": 130}`，测例详情即为

```json
"details": [
  {"id": 1, "result": "AC", "time": 1.01, "memory": 130},
  {"id": 2, "result": "AC", "time": 1.01, "memory": 130}
],
```

如果用户不可见，评测时不返回此字段即可。

## 同学们的操作系统有 `linux`, `macos`, `windows`，最终评测应该如何进行呢？

最终评分会结合 `linux` 自动评测及线下人工评测，因此需要大家适配 `linux` 风格指令。使用 `macos` 的同学可以兼容所有评测会用到的 `linux` 指令，使用 windows 的同学建议使用 `WSL` 虚拟化容器。安装请参考 [WSL 安装文档](https://docs.eesast.com/docs/tools/wsl)，使用请参考 [RUNOOB Linux 教程](https://www.runoob.com/linux/linux-command-manual.html)。**也推荐大家使用生成式人工智能查询 Linux 操作，本次大作业基本只会用到 `g++`, `python` 等常用指令**

## 如何理解评测状态的 [pending, success, error] 与测试点结果的 [AC, WA, ...] 之间关系？

请区分两种状态，一种是一个 submission 的状态，一种是评测点结果的状态。提交的时刻，评测并未完成，返回一定是 `pending`；一个用户提交了评测，然后这个时候用户立刻查询评测列表，这时可能评测完成或者未完成，所以在查询评测列表的时候会有多种评测状态。

## [仓库] 如何将自己的仓库与助教提供的示例仓库关联，及时拉取最新更新？

请参考 [仓库拉取教程](https://dbg-course.github.io/python-docs/oj/gitpull/)

## [环境] Python/依赖环境如何配置？

- 推荐使用 Python 3.8 及以上版本。
- 建议使用 venv/conda 创建虚拟环境，安装依赖时可参考 requirements.txt。
- FastAPI/Flask、pytest、requests、uvicorn 等常用包需提前安装。

## [API] 如何查阅和测试 API？

- 所有接口、参数、异常、状态码详见 [api.md](https://dbg-course.github.io/python-docs/oj/api/)。
- 推荐使用 Postman、curl 或 httpie 进行本地 API 测试。
- 注意接口权限（如部分接口需登录/管理员权限）。

## [评测] 评测流程和判题标准有哪些注意事项？

- 评测需严格按照题目输入输出格式，不能有多余提示语。
- 支持多语言评测，需动态注册语言时请参考 API 文档。
- 评测时需限制运行时间、内存，超限应返回 TLE/MLE。
- 日志接口可用于调试和查看评测详情。

## [权限] 用户权限和接口访问控制说明

- 普通用户仅能访问/操作自己的评测、信息、日志。
- 管理员可管理所有用户、题目、评测、日志等。
- 权限不足时接口会返回 403。

## [实验要求] 代码/报告/演示提交注意事项

- 代码需结构清晰、注释规范，按要求提交至指定仓库。
- 报告建议为 PDF，结构清晰，图文并茂。
- 需保证代码/报告/演示内容一致，严禁抄袭。

## 如何获取内存用量？

参考如下代码

```python
import subprocess
import psutil
import threading
import time

def monitor_memory(proc, mem_limit_mb, result_holder):
    p = psutil.Process(proc.pid)
    while proc.poll() is None:
        mem_usage = p.memory_info().rss / (1024 ** 2)  # in MB
        if mem_usage > mem_limit_mb:
            proc.kill()
            result_holder["status"] = "MLE"
            return
        time.sleep(0.05)
    result_holder["status"] = "OK"

def run_user_code(cmd, mem_limit_mb, timeout_sec):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_holder = {"status": "OK"}
    t = threading.Thread(target=monitor_memory, args=(proc, mem_limit_mb, result_holder))
    t.start()

    try:
        proc.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        proc.kill()
        result_holder["status"] = "TLE"

    t.join()
    return result_holder["status"]
```

## [前端] Step 6 必须实现哪些页面？

Step 6 是基础模块，至少实现以下三组页面：

- 用户页面组：用户注册页面、用户登录页面、用户信息展示页面、用户管理页面；
- 题目页面组：题目列表展示页面、题目详情展示页面、新增/编辑题目页面；
- 评测与提交页面组：提交记录列表展示页面、提交评测详情页面。

所有页面操作均应通过后端 API 完成。具体要求见 [Step 6：前端交互](https://dbg-course.github.io/python-docs/oj/project/step6/)。

## [AI 智能命题] 必须实现工具调用或 Agent Loop 吗？

不要求。工具调用是扩展模型能力的一种设计方式，属于设计参考，不是独立的硬性评分项。项目可以根据实际功能选择单次模型调用、固定工作流、工具调用或其他合理方案。R1 至 R4 和评分维度以 [AI 智能命题](https://dbg-course.github.io/python-docs/oj/project/advance/)页面为准。

## [AI 智能命题] 正例中列出的功能都必须实现吗？

不要求。正例和反例用于说明设计方向，不规定唯一实现方案。评分时将结合题目合理性、测试用例有效性和功能易用性进行评价。

## [AI 智能命题] 模型配置需要包含哪些内容？

至少应支持提供商 URL、模型名称和模型密钥，并确保配置实际用于模型请求。不得将模型提供商、模型名称或模型密钥固定在代码中。模型密钥不得通过日志或普通页面响应明文泄露。

## [AI 智能命题] 怎样满足实时进度和中断要求？

实时进度应在任务执行期间持续反映当前状态，而不是等待任务全部结束后一次性返回。可以使用流式响应、SSE、WebSocket 或轮询等方式。

中断操作应实际终止当前任务或阻止其继续执行。仅停止前端动画或关闭进度窗口，但后台任务仍继续运行，不满足中断要求。

## [AI 智能命题] Token 用量和价格如何统计？

应统计并展示当前任务的 Token 用量和费用。模型接口能够分别提供输入、输出 Token 时，应分别记录。费用根据实际采用的模型价格计算，并说明价格单位和计价依据；模型接口不能提供完整用量时，应说明采用的统计或估算方式及其限制。

## [其他] 常见问题与解答

- Q: 必须实现前端吗？
  - A: 必须。前端交互已经调整为基础模块 Step 6。
- Q: API 接口必须完全一致吗？
  - A: 基础模块使用的接口必须严格遵循 api.md。AI 智能命题因设计方案不同，可以采用等价接口，但需要在项目文档中说明路径、参数、状态和响应结构。
- Q: 可以用 AI/LLM 辅助开发吗？
  - A: 可以，但需注明引用和来源，严禁抄袭。

---

!!! 致谢
    感谢刘青乐、马子润、刘宇哲、陈晓宇、唐恒毅、刘汉唐、常钫铭、孙钰杰、王懋源等同学为文档提出的意见。

如有其他疑问，欢迎在课程群或私聊助教留言，助教会及时补充解答。

---

# 仓库拉取教程

相信在之前的学习中，大家已经初步了解了在自己仓库中进行 git 操作，比如 `git add`、`git clone`、`git commit`、`git push`。

不过，我们在更多情况下使用 git 是为了与他人合作，那么如何将自己代码与他人代码以不冲突的方式合并呢？

---

## 前置知识回顾

我们已经掌握了一些基础的 Git 命令：

* `git clone`：克隆远程仓库到本地
* `git add`：将修改添加到暂存区
* `git commit`：提交修改
* `git push`：推送代码到远程仓库

但多人协作时，我们还需学会：

* 添加多个远程仓库
* 从其他远程仓库拉取代码
* 合并或重放（rebase）改动
* 解决冲突

---

## 克隆你的作业仓库

```bash
git clone https://git.tsinghua.edu.cn/<git-space>/<repo-name>.git
cd <repo-name>
```

```shell
git clone https://git.tsinghua.edu.cn/python-course-2026/pa2-oj-2026123456.git
Cloning into 'pa2-oj-2026123456'...
remote: Enumerating objects: 3, done.
remote: Counting objects: 100% (3/3), done.
remote: Compressing objects: 100% (2/2), done.
remote: Total 3 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
Receiving objects: 100% (3/3), done.
```

!!! warning
    如果 clone 时提示需要登录，用户名（username）是你清华 GitLab 的 ID；密码则需要前往 GitLab 的 **User settings → Personal access tokens** 创建一个 access token 来填入（不是你的登录密码）。


你可以用以下命令查看所有远程仓库：

```bash
git remote -v
```

??? info
    git 默认会将直接 clone 下来的仓库源名设置为 `origin`

你应该看到类似输出

```shell
origin	https://git.tsinghua.edu.cn/python-course-2026/pa2-oj-2026123456.git (fetch)
origin	https://git.tsinghua.edu.cn/python-course-2026/pa2-oj-2026123456.git (push)
```

## 自动化配置（可选）

你也可以设置默认拉取行为（避免每次都提示）：

```bash
# 只对当前仓库设置
git config pull.rebase true

# 或对全局设置（所有仓库生效）
git config --global pull.rebase true
```

## 常见问题

- 如果你发现已经输出 `Already up to date`，可以检查下目前 pull 的源名是否绑定了预期仓库。比如此处 personal 绑定了自己的个人仓库。

![alt text](https://dbg-course.github.io/python-docs/oj/gitpull/assets/pull-error.png)

