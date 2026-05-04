import requests as http_requests
from flask import Response, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import validate_csrf

from app.services.auth_service import AuthService
from app.services.automation_service import AutomationService
from app.services.device_group_service import DeviceGroupService
from app.services.device_service import DeviceService
from app.services.energy_service import EnergyService
from app.services.home_service import HomeService
from app.services.scene_service import SceneService
from app.services.xiaomi_auth_service import XiaomiAuthService


def _check_csrf():
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        try:
            validate_csrf(request.form.get("csrf_token", ""))
        except Exception:
            flash("CSRF 验证失败，请重试", "error")
            return True
    return False


def _device_breadcrumb(user_id: int, device: dict) -> dict | None:
    """查找设备所属的家庭和房间，返回面包屑上下文"""
    try:
        homes = HomeService.list_homes(user_id)
    except Exception:
        return None

    home_id = device.get("home_id")
    did = str(device["did"])
    for home in homes:
        if home["home_id"] != home_id:
            continue
        for room in (home.get("room_list") or []):
            if did in [str(d) for d in room.get("dids", [])]:
                return {
                    "home": {"home_id": home["home_id"], "name": home["name"]},
                    "room": {"id": room["id"], "name": room["name"]},
                }
    # 设备属于该家庭但不在任何房间中
    if home_id:
        for home in homes:
            if home["home_id"] == home_id:
                return {"home": {"home_id": home["home_id"], "name": home["name"]}, "room": None}
    return None


def register_routes(bp):
    @bp.route("/")
    @login_required
    def dashboard():
        try:
            homes = HomeService.list_homes(current_user.id)
            devices = DeviceService.list_devices(current_user.id)
            xiaomi_status = XiaomiAuthService.get_status(current_user.id)
        except Exception:
            homes, devices, xiaomi_status = [], [], {"linked": False}
        return render_template(
            "dashboard/index.html", homes=homes, devices=devices, xiaomi_status=xiaomi_status
        )

    @bp.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("web.dashboard"))
        if request.method == "POST":
            if _check_csrf():
                return render_template("auth/login.html")
            username = request.form.get("username")
            password = request.form.get("password")
            try:
                user = AuthService.authenticate(username, password)
                login_user(user)
                return redirect(url_for("web.dashboard"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("auth/login.html")

    @bp.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("web.dashboard"))
        if request.method == "POST":
            if _check_csrf():
                return render_template("auth/register.html")
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            try:
                user = AuthService.register(username, password, email)
                login_user(user)
                return redirect(url_for("web.dashboard"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("auth/register.html")

    @bp.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("web.login"))

    @bp.route("/change-password", methods=["GET", "POST"])
    @login_required
    def change_password():
        if request.method == "POST":
            if _check_csrf():
                return render_template("auth/change_password.html")
            old_password = request.form.get("old_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")
            if not old_password or not new_password:
                flash("请填写所有密码字段", "error")
                return render_template("auth/change_password.html")
            if new_password != confirm_password:
                flash("两次输入的新密码不一致", "error")
                return render_template("auth/change_password.html")
            try:
                AuthService.change_password(current_user.id, old_password, new_password)
                flash("密码修改成功", "success")
                return redirect(url_for("web.dashboard"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("auth/change_password.html")

    @bp.route("/link-xiaomi")
    @login_required
    def link_xiaomi():
        xiaomi_status = XiaomiAuthService.get_status(current_user.id)
        return render_template("auth/xiaomi_link.html", xiaomi_status=xiaomi_status)

    @bp.route("/devices")
    @login_required
    def devices():
        home_id = request.args.get("home_id")
        refresh = request.args.get("refresh", "false") == "true"
        try:
            device_list = DeviceService.list_devices(current_user.id, home_id=home_id, refresh=refresh)
            homes = HomeService.list_homes(current_user.id)
        except Exception as e:
            flash(f"获取设备列表失败: {e}", "error")
            device_list, homes = [], []
        # 精简设备数据用于 Alpine.js（去掉 spec_data 避免序列化过大）
        light_devices = [
            {
                "did": d["did"],
                "name": d["name"],
                "model": d.get("model"),
                "home_id": d.get("home_id"),
                "is_online": d.get("is_online"),
            }
            for d in device_list
        ]
        return render_template(
            "devices/list.html", devices=device_list, light_devices=light_devices, homes=homes, current_home_id=home_id
        )

    @bp.route("/devices/<did>")
    @login_required
    def device_control(did):
        try:
            device = DeviceService.get_device(current_user.id, did)
        except Exception as e:
            flash(f"获取设备信息失败: {e}", "error")
            return redirect(url_for("web.devices"))

        # 查找设备所属的家庭和房间，用于面包屑导航
        breadcrumb = _device_breadcrumb(current_user.id, device)
        return render_template(
            "devices/control.html", device=device, go2rtc_url=current_app.config.get("GO2RTC_URL", ""),
            breadcrumb=breadcrumb,
        )

    @bp.route("/camera-proxy/<path:path>", methods=["GET", "POST"])
    @login_required
    def camera_proxy(path):
        """反向代理 go2rtc，避免浏览器代理导致 401"""
        go2rtc_url = current_app.config.get("GO2RTC_URL", "http://127.0.0.1:1984")
        target = f"{go2rtc_url}/{path}"
        if request.query_string:
            target += f"?{request.query_string.decode()}"

        try:
            proxies = {"http": None, "https": None}
            if request.method == "GET":
                resp = http_requests.get(target, stream=True, proxies=proxies, timeout=30)
            else:
                resp = http_requests.post(target, data=request.get_data(), stream=True, proxies=proxies, timeout=30)
        except http_requests.ConnectionError:
            return Response("go2rtc 服务未启动", status=502)

        excluded_headers = {"transfer-encoding", "connection"}
        headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded_headers]
        return Response(resp.iter_content(chunk_size=8192), status=resp.status_code, headers=headers)

    @bp.route("/scenes")
    @login_required
    def scenes():
        home_id = request.args.get("home_id")
        refresh = request.args.get("refresh", "false") == "true"
        try:
            scene_list = SceneService.list_scenes(current_user.id, home_id=home_id, refresh=refresh)
        except Exception as e:
            flash(f"获取场景列表失败: {e}", "error")
            scene_list = []
        return render_template("scenes/list.html", scenes=scene_list)

    @bp.route("/homes")
    @login_required
    def homes():
        refresh = request.args.get("refresh", "false") == "true"
        try:
            home_list = HomeService.list_homes(current_user.id, refresh=refresh)
        except Exception as e:
            flash(f"获取家庭列表失败: {e}", "error")
            home_list = []
        return render_template("homes/detail.html", homes=home_list)

    @bp.route("/homes/<home_id>/rooms/<room_id>")
    @login_required
    def room_devices(home_id, room_id):
        try:
            data = HomeService.get_room_devices(current_user.id, home_id, room_id)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("web.homes"))
        except Exception as e:
            flash(f"获取房间设备失败: {e}", "error")
            return redirect(url_for("web.homes"))
        return render_template("homes/room.html", **data)

    # --- Device Groups ---
    @bp.route("/groups")
    @login_required
    def device_groups():
        try:
            groups = DeviceGroupService.list_groups(current_user.id)
        except Exception:
            groups = []
        return render_template("devices/groups.html", groups=groups)

    @bp.route("/groups/create", methods=["POST"])
    @login_required
    def create_group():
        if _check_csrf():
            return redirect(url_for("web.device_groups"))
        name = request.form.get("name")
        if not name:
            flash("分组名称不能为空", "error")
            return redirect(url_for("web.device_groups"))
        try:
            DeviceGroupService.create_group(current_user.id, name, icon=request.form.get("icon"))
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("web.device_groups"))

    @bp.route("/groups/<int:group_id>/delete", methods=["POST"])
    @login_required
    def delete_group(group_id):
        if _check_csrf():
            return redirect(url_for("web.device_groups"))
        try:
            DeviceGroupService.delete_group(current_user.id, group_id)
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("web.device_groups"))

    # --- Automations ---
    @bp.route("/automations")
    @login_required
    def automations():
        try:
            rules = AutomationService.list_rules(current_user.id)
            devices = DeviceService.list_devices(current_user.id)
            scenes = SceneService.list_scenes(current_user.id)
        except Exception:
            rules, devices, scenes = [], [], []
        return render_template("automations/list.html", rules=rules, devices=devices, scenes=scenes)

    @bp.route("/automations/create", methods=["POST"])
    @login_required
    def create_automation():
        if _check_csrf():
            return redirect(url_for("web.automations"))
        import json
        data = {
            "name": request.form.get("name"),
            "trigger_type": request.form.get("trigger_type"),
            "trigger_config": json.loads(request.form.get("trigger_config", "{}")),
            "action_type": request.form.get("action_type"),
            "action_config": json.loads(request.form.get("action_config", "{}")),
        }
        try:
            AutomationService.create_rule(current_user.id, data)
            flash("自动化规则已创建", "success")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("web.automations"))

    @bp.route("/automations/<int:rule_id>/delete", methods=["POST"])
    @login_required
    def delete_automation(rule_id):
        if _check_csrf():
            return redirect(url_for("web.automations"))
        try:
            AutomationService.delete_rule(current_user.id, rule_id)
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("web.automations"))

    @bp.route("/automations/<int:rule_id>/toggle", methods=["POST"])
    @login_required
    def toggle_automation(rule_id):
        if _check_csrf():
            return redirect(url_for("web.automations"))
        try:
            AutomationService.toggle_rule(current_user.id, rule_id)
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("web.automations"))

    # --- Energy ---
    @bp.route("/energy")
    @login_required
    def energy_dashboard():
        try:
            devices = DeviceService.list_devices(current_user.id)
        except Exception:
            devices = []
        return render_template("energy/dashboard.html", devices=devices)

    @bp.route("/energy/<did>")
    @login_required
    def energy_device(did):
        try:
            device = DeviceService.get_device(current_user.id, did)
            props = EnergyService.get_device_energy_props(current_user.id, did)
        except Exception as e:
            flash(f"获取能耗数据失败: {e}", "error")
            return redirect(url_for("web.energy_dashboard"))
        return render_template("energy/device.html", device=device, energy_props=props)
