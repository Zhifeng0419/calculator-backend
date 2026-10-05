# 代码规范 (Code Style) — 后端

> **规范来源**：本规范基于 [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/) 与 [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)，并参考 Google Python Style Guide 制定。

## 1. 代码布局

- **缩进**：使用 4 个空格，不使用制表符（Tab）。
- **行长度**：单行最大 100 字符（PEP 8 默认 79，项目放宽至 100）。
- **空行**：
  - 顶层函数与类定义之间空 2 行。
  - 类内部方法之间空 1 行。
  - 逻辑相关的代码组之间可空 1 行。
- **编码**：源文件统一使用 UTF-8，文件末尾保留一个换行符。

## 2. 命名规范

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块/文件 | 小写下划线 | `calculator.py`, `database.py` |
| 类 | 大驼峰 | `CalculatorError`, `TokenType` |
| 函数/方法 | 小写下划线 | `calculate()`, `get_records()` |
| 变量 | 小写下划线 | `expression`, `record_id` |
| 常量 | 全大写下划线 | `MAX_EXPRESSION_LENGTH`, `OPERATORS` |
| 私有成员 | 单下划线前缀 | `_apply_operator()` |

## 3. 导入规范

- 导入顺序（每组之间空 1 行）：
  1. 标准库导入（`os`, `math`, `sqlite3` ...）
  2. 第三方库导入（`flask`, `flask_cors` ...）
  3. 本地模块导入（`calculator`, `database` ...）
- 避免使用 `from module import *`。
- 优先使用绝对导入。

## 4. 字符串与注释

- 字符串优先使用双引号 `"`，文档字符串（docstring）使用三双引号 `"""`。
- 所有公共模块、类、函数必须编写 docstring，简要说明用途、参数、返回值与异常。
- 行内注释与代码之间至少空 2 个空格。
- 注释使用中文或英文均可，但同一文件内保持一致。

## 5. 类型注解

- 公共函数与方法应添加类型注解（`def calculate(expression: str) -> float`）。
- 使用 `from __future__ import annotations` 以支持延迟求值（兼容旧版本）。
- 复杂类型使用 `typing` 模块或内置泛型（Python 3.9+）。

## 6. 异常处理

- 自定义异常继承自 `Exception`，命名以 `Error` 结尾。
- 不使用裸 `except:`，应捕获具体异常类型。
- 捕获异常后应做有意义的处理（记录日志、转换为业务异常等），禁止静默吞掉异常。

## 7. Flask 路由规范

- 路由函数命名使用 `api_<资源>_<动作>` 风格，如 `api_calculate`、`api_delete_history`。
- 统一使用 `ok()` / `fail()` 辅助函数返回标准 JSON 响应。
- 请求参数校验失败时返回 HTTP 400，资源不存在返回 404。
- 路由装饰器与函数定义之间不空行。

## 8. 安全规范

- **严禁**使用 `eval()`、`exec()`、`compile()` 执行用户输入。
- 表达式解析仅允许白名单字符与白名单函数/常量。
- 数据库操作使用参数化查询（`?` 占位符），禁止字符串拼接 SQL。
- 用户输入在输出前必须经过转义或校验。

## 9. Git 提交规范

- 提交信息格式：`<type>: <description>`
  - `feat`: 新功能
  - `fix`: 修复 Bug
  - `docs`: 文档变更
  - `style`: 代码格式调整
  - `refactor`: 重构
  - `test`: 测试相关
- 示例：`feat: add base conversion endpoint`
