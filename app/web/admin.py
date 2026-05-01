from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import Forbidden

from app.services.admin_service import AdminService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin",
                     template_folder="../templates")


@admin_bp.before_request
@login_required
def check_admin():
    if not current_user.is_admin:
        raise Forbidden()


@admin_bp.route("/")
def dashboard():
    stats = AdminService.get_system_stats()
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/users")
def users():
    page = request.args.get("page", 1, type=int)
    data = AdminService.list_users(page=page)
    return render_template("admin/users.html", **data)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def toggle_active(user_id):
    if user_id == current_user.id:
        flash("不能停用自己的账户", "error")
        return redirect(url_for("admin.users"))
    try:
        validate_csrf(request.form.get("csrf_token", ""))
    except Exception:
        flash("CSRF 验证失败，请重试", "error")
        return redirect(url_for("admin.users"))
    try:
        result = AdminService.toggle_user_active(user_id)
        status = "启用" if result["is_active"] else "停用"
        flash(f"已{status}用户", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin.users"))
