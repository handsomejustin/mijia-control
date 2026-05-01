from flask import jsonify


def success(data=None, message="ok", status_code=200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def error(message="error", status_code=400, data=None):
    body = {"success": False, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code
