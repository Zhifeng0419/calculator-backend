"""Flask application: calculator backend API.

Endpoints
---------
POST   /api/calculate          Evaluate a math expression.
POST   /api/convert/base       Convert a number between bases.
POST   /api/convert/unit       Convert a value between units.
GET    /api/history            List history records (paginated, searchable).
DELETE /api/history/<id>       Delete a single history record.
DELETE /api/history            Clear all history records.
GET    /api/stats              Return basic calculation statistics.
GET    /api/units              List available unit categories and units.
GET    /api/health             Health check.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request
from flask_cors import CORS

import calculator
import converters
import database

app = Flask(__name__)
CORS(app)  # 允许前端（HBuilderX 运行的 uni-app H5）跨域访问

# 确保数据库表存在
database.init_db()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def ok(data=None, message: str = "success"):
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message: str, code: int = 1, status: int = 400):
    return jsonify({"code": code, "message": message, "data": None}), status


# --------------------------------------------------------------------------- #
# Calculation
# --------------------------------------------------------------------------- #

@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    payload = request.get_json(silent=True) or {}
    expression = (payload.get("expression") or "").strip()
    if not expression:
        return fail("表达式不能为空")

    try:
        result = calculator.calculate(expression)
        result_str = calculator.format_result(result)
    except calculator.CalculatorError as exc:
        return fail(str(exc), status=400)

    record_id = database.add_record(expression, result_str, "calculate")
    return ok({"id": record_id, "expression": expression, "result": result_str})


# --------------------------------------------------------------------------- #
# Conversions
# --------------------------------------------------------------------------- #

@app.route("/api/convert/base", methods=["POST"])
def api_convert_base():
    payload = request.get_json(silent=True) or {}
    value = str(payload.get("value", "")).strip()
    from_base = payload.get("from_base")
    to_base = payload.get("to_base")

    if not value:
        return fail("待转换数值不能为空")
    try:
        from_base = int(from_base)
        to_base = int(to_base)
    except (TypeError, ValueError):
        return fail("进制必须是整数")

    try:
        result = converters.convert_base(value, from_base, to_base)
    except converters.ConvertError as exc:
        return fail(str(exc), status=400)

    expr = f"{from_base}进制({value}) → {to_base}进制"
    record_id = database.add_record(expr, result, "base")
    return ok({"id": record_id, "expression": expr, "result": result})


@app.route("/api/convert/unit", methods=["POST"])
def api_convert_unit():
    payload = request.get_json(silent=True) or {}
    try:
        value = float(payload.get("value"))
    except (TypeError, ValueError):
        return fail("数值必须是数字")

    from_unit = str(payload.get("from_unit", "")).strip()
    to_unit = str(payload.get("to_unit", "")).strip()
    category = str(payload.get("category", "")).strip()

    if not category or not from_unit or not to_unit:
        return fail("单位类别、源单位、目标单位均不能为空")

    try:
        result = converters.convert_unit(value, from_unit, to_unit, category)
    except converters.ConvertError as exc:
        return fail(str(exc), status=400)

    result_str = f"{result:.10g}"
    expr = f"{category}: {value}{from_unit} → {to_unit}"
    record_id = database.add_record(expr, result_str, "unit")
    return ok({"id": record_id, "expression": expr, "result": result_str})


@app.route("/api/units", methods=["GET"])
def api_units():
    return ok(converters.list_units())


# --------------------------------------------------------------------------- #
# History
# --------------------------------------------------------------------------- #

@app.route("/api/history", methods=["GET"])
def api_history():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    search = request.args.get("search", type=str)
    record_type = request.args.get("type", type=str)
    data = database.get_records(page, page_size, search, record_type)
    return ok(data)


@app.route("/api/history/<int:record_id>", methods=["DELETE"])
def api_delete_history(record_id: int):
    if database.delete_record(record_id):
        return ok({"deleted": record_id}, "删除成功")
    return fail(f"未找到 ID 为 {record_id} 的记录", status=404)


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    count = database.clear_all_records()
    return ok({"deleted_count": count}, f"已清空 {count} 条记录")


# --------------------------------------------------------------------------- #
# Stats & health
# --------------------------------------------------------------------------- #

@app.route("/api/stats", methods=["GET"])
def api_stats():
    return ok(database.get_stats())


@app.route("/api/health", methods=["GET"])
def api_health():
    return ok({"status": "ok"})


# --------------------------------------------------------------------------- #
# Error handlers
# --------------------------------------------------------------------------- #

@app.errorhandler(404)
def not_found(_):
    return fail("接口不存在", status=404)


@app.errorhandler(405)
def method_not_allowed(_):
    return fail("请求方法不允许", status=405)


@app.errorhandler(500)
def internal_error(err):
    app.logger.exception("Internal error: %s", err)
    return fail("服务器内部错误", status=500)


if __name__ == "__main__":
    host = os.environ.get("CALCULATOR_HOST", "0.0.0.0")
    port = int(os.environ.get("CALCULATOR_PORT", "5000"))
    debug = os.environ.get("CALCULATOR_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
