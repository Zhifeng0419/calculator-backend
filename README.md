# 智能计算器后端 (Calculator Backend)

基于 **Python + Flask + SQLite** 的计算器后端服务。负责表达式安全校验、解析计算、进制/单位换算，以及计算历史记录的持久化存储与管理。

## 项目简介

本项目是「智能计算器 Web 应用」的后端部分，采用前后端分离架构。所有计算逻辑均在后端完成，前端仅负责交互与展示。历史记录持久化存储在 SQLite 数据库中，确保数据在服务重启后不丢失。

### 核心特性

- **安全表达式求值**：自行实现基于调度场算法（Shunting-yard）的表达式解析器，**不使用 `eval`/`exec`**，仅支持白名单内的运算符、函数与常量。
- **科学计算**：支持三角函数、对数、开方、幂运算、阶乘等。
- **进制转换**：二进制、八进制、十进制、十六进制互转。
- **单位换算**：长度、重量、温度、面积、体积、时间、数据存储等类别。
- **历史记录**：分页查询、关键字搜索、按类型筛选、单条删除、一键清空。
- **持久化**：SQLite 数据库，重启后数据不丢失。

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| Web 框架 | Flask 3.x |
| 跨域 | flask-cors |
| 数据库 | SQLite 3（Python 内置 `sqlite3`） |
| 表达式解析 | 自研调度场算法（无第三方依赖） |

## 运行环境要求

- Python 3.10 及以上
- pip
- （可选）虚拟环境工具，如 `venv`

## 安装方法

```bash
# 1. 进入后端目录
cd backend

# 2. （推荐）创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

## 启动方式

```bash
# 开发模式启动（默认监听 0.0.0.0:5000）
python app.py

# 或使用 flask 命令
flask --app app run --host 0.0.0.0 --port 5000
```

启动后：
- API 根地址：`http://localhost:5000`
- 前端由 uni-app 项目提供，在 HBuilderX 中运行（见前端 README）

## 配置说明

可通过环境变量配置：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `CALCULATOR_HOST` | `0.0.0.0` | 监听地址 |
| `CALCULATOR_PORT` | `5000` | 监听端口 |
| `CALCULATOR_DEBUG` | `0` | 是否开启调试模式（`1` 开启） |
| `CALCULATOR_DB_PATH` | `backend/history.db` | SQLite 数据库文件路径 |

## 数据库初始化方法

数据库采用 SQLite，**无需手动初始化**。首次启动后端服务时，`database.init_db()` 会自动创建 `history` 表。

如需手动初始化，可执行：

```bash
python -c "import database; database.init_db(); print('DB initialized')"
```

表结构：

```sql
CREATE TABLE history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    expression TEXT    NOT NULL,
    result     TEXT    NOT NULL,
    type       TEXT    NOT NULL DEFAULT 'calculate',  -- calculate / base / unit
    time       TEXT    NOT NULL                        -- 格式: YYYY-MM-DD HH:MM:SS
);
```

## 前后端对接方式

后端默认已开启 CORS，前端可跨域访问 API。前后端通过 HTTP + JSON 通信。

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/calculate` | 提交表达式进行计算 |
| POST | `/api/convert/base` | 进制转换 |
| POST | `/api/convert/unit` | 单位换算 |
| GET | `/api/units` | 获取可用单位类别及单位列表 |
| GET | `/api/history` | 获取历史记录（分页、搜索、筛选） |
| DELETE | `/api/history/<id>` | 删除指定 ID 的历史记录 |
| DELETE | `/api/history` | 清空全部历史记录 |
| GET | `/api/stats` | 计算统计信息 |
| GET | `/api/health` | 健康检查 |

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code: 0` 表示成功，非 0 表示失败
- `message` 为提示信息
- `data` 为返回数据，失败时为 `null`

### 接口示例

**计算表达式：**
```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"2+3*sin(pi/2)"}'
```
响应：
```json
{"code":0,"message":"success","data":{"id":1,"expression":"2+3*sin(pi/2)","result":"5"}}
```

**获取历史记录：**
```bash
curl "http://localhost:5000/api/history?page=1&page_size=20&search=2&type=calculate"
```

**删除单条记录：**
```bash
curl -X DELETE http://localhost:5000/api/history/1
```

**清空全部记录：**
```bash
curl -X DELETE http://localhost:5000/api/history
```

## 安全说明

- 表达式求值**不使用 `eval`/`exec`**，采用自研的词法分析 + 调度场算法 + RPN 求值。
- 仅允许白名单字符（数字、运算符、括号、英文字母、下划线、逗号、空格）。
- 仅支持白名单内的函数（sin、cos、sqrt、ln 等）和常量（pi、e、tau）。
- 对除零、溢出、无效输入等异常均有明确错误提示。

## 项目结构

```
backend/
├── app.py          # Flask 应用入口与 API 路由
├── calculator.py   # 安全表达式解析器（调度场算法）
├── converters.py   # 进制转换与单位换算
├── database.py     # SQLite 数据库操作
├── requirements.txt
├── README.md
└── codestyle.md
```
