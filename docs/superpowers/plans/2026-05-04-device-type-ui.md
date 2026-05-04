# 设备类型专属控制页 实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为每种设备类型创建专属控制页 UI，提供友好的可视化控制体验。

**Architecture:** 扩展 DeviceCategory 枚举，在路由层根据设备类型选择对应模板。共享组件（面包屑、设备头部、状态指示器）抽成 include 复用。每种设备类型一个独立 HTML 模板，使用 Tailwind CSS + Alpine.js。

**Tech Stack:** Flask, Jinja2, Tailwind CSS, Alpine.js, 现有 map_device() 分类器

**Design Spec:** `docs/superpowers/specs/2026-05-04-device-type-ui-design.md`

---

## Chunk 1: 基础设施 — 分类扩展 + 路由选择 + 共享组件

### Task 1: 扩展 DeviceCategory 枚举和映射规则

**Files:**
- Modify: `app/homekit/mapper.py:12-22` (DeviceCategory 枚举)
- Modify: `app/homekit/mapper.py:25-46` (_MODEL_RULES)

- [ ] **Step 1: 在 DeviceCategory 枚举中新增 DEHUMIDIFIER**

在 `app/homekit/mapper.py` 的 `DeviceCategory` 类中，在 `HEATER` 之后添加：
```python
DEHUMIDIFIER = "dehumidifier"
```

- [ ] **Step 2: 更新 _MODEL_RULES 中除湿机的映射**

将 `("derh", DeviceCategory.THERMOSTAT)` 改为 `("derh", DeviceCategory.DEHUMIDIFIER)`。
将 `("deye.derh", DeviceCategory.DEHUMIDIFIER)` 添加在 `("derh", ...)` 之前（更精确的匹配优先）。

- [ ] **Step 3: 验证分类正确**

Run:
```bash
cd D:/python/mijia-control && venv/Scripts/python.exe -c "
from app import create_app
app = create_app()
with app.app_context():
    from app.models.device_cache import DeviceCache
    from app.homekit.mapper import map_device
    d = DeviceCache.query.filter(DeviceCache.model.like('%derh%')).first()
    cat = map_device({'model': d.model, 'spec_data': d.spec_data})
    assert cat.value == 'dehumidifier', f'Expected dehumidifier, got {cat.value}'
    print(f'OK: {d.name} → {cat.value}')
"
```
Expected: `OK: 地下室除湿机 → dehumidifier`

- [ ] **Step 4: 提交**

```bash
git add app/homekit/mapper.py
git commit -m "feat: 扩展 DeviceCategory 新增 dehumidifier 类型"
```

---

### Task 2: 路由层模板选择逻辑

**Files:**
- Modify: `app/web/routes.py:161-175` (device_control 视图函数)

- [ ] **Step 1: 在 routes.py 顶部添加 import**

```python
from app.homekit.mapper import map_device
```

- [ ] **Step 2: 修改 device_control 视图函数**

将函数体改为：
```python
@bp.route("/devices/<did>")
@login_required
def device_control(did):
    try:
        device = DeviceService.get_device(current_user.id, did)
    except Exception as e:
        flash(f"获取设备信息失败: {e}", "error")
        return redirect(url_for("web.devices"))

    breadcrumb = _device_breadcrumb(current_user.id, device)

    # 根据设备类型选择专属模板
    category = map_device(device)
    template_map = {
        "dehumidifier": "devices/control_dehumidifier.html",
        "light": "devices/control_light.html",
        "heater": "devices/control_heater.html",
        "thermostat": "devices/control_thermostat.html",
        "temperature_sensor": "devices/control_sensor.html",
        "switch": "devices/control_switch.html",
        "camera": "devices/control_camera.html",
    }
    template = template_map.get(category, "devices/control.html")

    return render_template(
        template, device=device, go2rtc_url=current_app.config.get("GO2RTC_URL", ""),
        breadcrumb=breadcrumb,
    )
```

- [ ] **Step 3: 验证路由不报错**

```bash
cd D:/python/mijia-control && venv/Scripts/python.exe -c "
from app.homekit.mapper import map_device
result = map_device({'model': 'deye.derh.z20'})
print(f'dehumidifier: {result.value}')
result2 = map_device({'model': 'philips.light.sread1'})
print(f'light: {result2.value}')
"
```
Expected: dehumidifier, light

- [ ] **Step 4: 提交**

```bash
git add app/web/routes.py
git commit -m "feat: 路由层根据设备类型选择专属模板"
```

---

### Task 3: 共享组件 — breadcrumb + device_header + status_indicator

**Files:**
- Create: `app/templates/devices/components/breadcrumb.html`
- Create: `app/templates/devices/components/device_header.html`
- Create: `app/templates/devices/components/status_indicator.html`

- [ ] **Step 1: 从现有 control.html 提取 breadcrumb 组件**

创建 `app/templates/devices/components/breadcrumb.html`，内容为现有 control.html 第 6-31 行的面包屑导航（保持不变，用 `{% macro breadcrumb(breadcrumb, device) %}` 包装或直接 include）。

实际上使用 include 参数方式，不需要 macro。直接把面包屑代码提取为独立文件：

```html
{# devices/components/breadcrumb.html — 面包屑导航 #}
{% if breadcrumb %}
<nav class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
    <a href="{{ url_for('web.dashboard') }}" class="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">首页</a>
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
    <a href="{{ url_for('web.homes') }}" class="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">家庭</a>
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
    <a href="{{ url_for('web.homes') }}" class="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">{{ breadcrumb.home.name }}</a>
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
    {% if breadcrumb.room %}
    <a href="{{ url_for('web.room_devices', home_id=breadcrumb.home.home_id, room_id=breadcrumb.room.id) }}" class="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">{{ breadcrumb.room.name }}</a>
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
    {% endif %}
    <span class="text-slate-900 dark:text-white font-medium">{{ device.name }}</span>
</nav>
{% else %}
<nav class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
    <a href="{{ url_for('web.dashboard') }}" class="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">首页</a>
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
    <a href="{{ url_for('web.devices') }}" class="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">设备列表</a>
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
    <span class="text-slate-900 dark:text-white font-medium">{{ device.name }}</span>
</nav>
{% endif %}
```

- [ ] **Step 2: 创建 device_header 共享组件**

```html
{# devices/components/device_header.html — 设备头部 #}
{% set has_on_prop = device.spec_data and device.spec_data.properties | selectattr('name', 'equalto', 'on') | list | length > 0 %}
<div class="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/50 p-5 sm:p-6">
    <div class="flex items-center justify-between">
        <div>
            <div class="flex items-center gap-3 mb-2">
                <span id="device-online-dot" class="inline-block w-3 h-3 rounded-full {% if device.is_online %}bg-emerald-400{% else %}bg-slate-300 dark:bg-slate-600{% endif %}"></span>
                <h1 class="font-heading text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">{{ device.name }}</h1>
            </div>
            <p class="text-sm text-slate-500 dark:text-slate-400">
                型号: <span class="font-mono">{{ device.model or '未知' }}</span>
            </p>
        </div>
        {% if has_on_prop %}
        <div x-data="{ on: false, loading: false }" x-init="getProp('on').then(v => on = v)"
             class="w-16 h-16 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300"
             :class="on ? 'bg-blue-500 shadow-[0_0_0_8px_rgba(59,130,246,0.15),0_4px_12px_rgba(59,130,246,0.3)]' : 'bg-slate-200 dark:bg-slate-700 shadow-none'"
             :disabled="loading"
             @click="toggleProp('on'); on = !on">
            <svg class="w-7 h-7 transition-colors" :class="on ? 'text-white' : 'text-slate-400 dark:text-slate-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.636 5.636a9 9 0 1012.728 0M12 3v6"/>
            </svg>
        </div>
        {% endif %}
    </div>
</div>
```

注意：device_header 中的 `getProp`/`toggleProp` 函数需要由各模板的 `<script>` 提供。

- [ ] **Step 3: 创建 status_indicator 共享组件**

```html
{# devices/components/status_indicator.html
   参数: icon, label, ok_text, ok, error_text
   用法: {% include "devices/components/status_indicator.html" %} 并在 include 前设置变量
#}
<div class="text-center p-2.5 rounded-xl" :class="ok ? 'bg-slate-50 dark:bg-slate-700/50' : 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800'">
    <div class="text-lg mb-1">{{ icon }}</div>
    <p class="text-xs font-medium" :class="ok ? 'text-slate-500 dark:text-slate-400' : 'text-amber-600 dark:text-amber-400'"
       x-text="ok ? '{{ ok_text }}' : '{{ error_text }}'"></p>
</div>
```

- [ ] **Step 4: 提交**

```bash
git add app/templates/devices/components/
git commit -m "feat: 提取共享组件 breadcrumb/device_header/status_indicator"
```

---

## Chunk 2: 设备专属模板

### Task 4: 除湿机控制页

**Files:**
- Create: `app/templates/devices/control_dehumidifier.html`
- Reference: `app/static/mockup_dehumidifier.html` (已验证的 mockup)

**关键属性 (deye.derh.z20):**
- `on` (bool, rw) — 开关
- `mode` (uint, rw, 0=除湿/1=干衣)
- `target-humidity` (uint, rw, 25-80%, step 5)
- `fan-level` (uint, rw, 0=低风/1=高风)
- `relative-humidity` (uint, r) — 当前湿度
- `temperature` (int, r) — 当前温度
- `water` (uint, r, 0=正常/1=水满)
- `frost` (uint, r, 0=正常/1=化霜)
- `fanstate` (uint, r, 0=停止/1=运行)
- `physical-controls-locked` (bool, rw) — 童锁

- [ ] **Step 1: 基于 mockup 创建 control_dehumidifier.html**

将 `app/static/mockup_dehumidifier.html` 的 UI 结构迁移为 Jinja2 模板：
- 继承 `base.html`
- 使用 `{% include "devices/components/breadcrumb.html" %}`
- 使用 `{% include "devices/components/device_header.html" %}`
- 属性值通过 `x-init` 在页面加载时从 API 读取
- 使用 spec_data 动态渲染控件（兼容不同型号除湿机）

模板需在 `<script>` 中提供 `getProp`/`setProp`/`toggleProp` 函数（复用现有 control.html 的 JS 逻辑）。

页面结构：
1. 面包屑
2. 设备头部（含电源按钮）
3. 当前湿度/温度双卡片
4. 目标湿度滑块
5. 模式选择（除湿/干衣）+ 风速选择（低风/高风）并排
6. 运行状态指示器（水箱、化霜、风机）
7. 童锁 toggle

- [ ] **Step 2: 在浏览器中验证**

启动 Flask 开发服务器，访问 `http://127.0.0.1:5000/devices/782251256`（除湿机 DID），确认页面渲染正确。

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_dehumidifier.html
git commit -m "feat: 除湿机专属控制页"
```

---

### Task 5: 灯光控制页

**Files:**
- Create: `app/templates/devices/control_light.html`

**关键属性:**
- `on` (bool, rw) — 开关
- `brightness` (uint, rw, 1-100%) — 亮度
- `color-temperature` (uint, rw, 2700-6500K) — 色温（部分灯有）
- `mode` (uint, w) — 预设模式（部分灯有）

- [ ] **Step 1: 创建 control_light.html**

继承 `base.html`，使用共享组件。

页面结构：
1. 面包屑
2. 设备头部（含电源按钮）
3. 亮度圆形大数字显示 + 亮度滑块
4. 色温滑块（如有 color-temperature 属性，标注 2700K 暖白 ←→ 6500K 冷白）
5. 预设模式按钮（如有 mode 属性，根据 value_list 渲染）
6. 其他只读属性小标签

属性检测逻辑：遍历 `device.spec_data.properties`，按 name 匹配渲染对应 UI 块。

- [ ] **Step 2: 浏览器验证**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_light.html
git commit -m "feat: 灯光专属控制页"
```

---

### Task 6: 取暖器控制页

**Files:**
- Create: `app/templates/devices/control_heater.html`

**关键属性 (leshow.heater.bs2):**
- `on` (bool, rw)
- `target-temperature` (uint, rw, 18-28°C)
- `temperature` (int, r) — 当前温度
- `environment-temperature` (int, r) — 环境温度
- `relative-humidity` (uint, r) — 湿度
- `mode` (uint, rw, value_list: 0/1)
- `countdown-time` (uint, rw, 0-720 min)
- `physical-controls-locked` (bool, rw)
- `brightness` (uint, rw, 0/1/2) — 显示亮度

- [ ] **Step 1: 创建 control_heater.html**

页面结构：
1. 面包屑
2. 设备头部（含电源按钮）
3. 当前温度/目标温度双卡片
4. 目标温度滑块 (18-28°C)
5. 模式分段选择器
6. 状态区（环境温度、湿度、定时关闭）
7. 童锁 + 显示亮度

- [ ] **Step 2: 浏览器验证**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_heater.html
git commit -m "feat: 取暖器专属控制页"
```

---

### Task 7: 空调伴侣控制页

**Files:**
- Create: `app/templates/devices/control_thermostat.html`

**关键属性 (iot.acpartner.x2 / lmkj.acpartner.wsd001):**
- `on` (bool, rw)
- `mode` (uint, rw, 0=制冷/1=制热/2=自动/3=送风/4=除湿)
- `target-temperature` (uint|float, rw, 16-30°C)
- `fan-level` (uint, rw, 0=自动/1=低风/2=中风/3=高风)
- `vertical-swing` (bool, rw) — 上下摆风
- `temperature` (float, r) — 当前温度（部分有）
- `relative-humidity` (float, r) — 当前湿度（部分有）

- [ ] **Step 1: 创建 control_thermostat.html**

页面结构：
1. 面包屑
2. 设备头部（含电源按钮）
3. 当前温度/目标温度双卡片（如有只读温度属性）
4. 目标温度滑块 (16-30°C)
5. 模式分段选择器（制冷/制热/自动/送风/除湿）
6. 风速分段选择器（自动/低风/中风/高风）
7. 上下摆风 toggle
8. 其他只读状态

- [ ] **Step 2: 浏览器验证**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_thermostat.html
git commit -m "feat: 空调伴侣专属控制页"
```

---

### Task 8: 温湿度传感器控制页

**Files:**
- Create: `app/templates/devices/control_sensor.html`

**关键属性 (xiaomi.sensor_ht.mini):**
- `temperature` (float, r, -30~100°C)
- `relative-humidity` (uint, r, 0-100%)
- `battery-level` (uint, r, 0-100%)

- [ ] **Step 1: 创建 control_sensor.html**

页面结构（纯只读）：
1. 面包屑
2. 设备头部（无电源按钮）
3. 温度大卡片（大数字 + 只读进度条 -30~50°C）
4. 湿度大卡片（大数字 + 只读进度条 0-100%）
5. 电池电量标签

页面加载时自动读取所有属性值。

- [ ] **Step 2: 浏览器验证**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_sensor.html
git commit -m "feat: 温湿度传感器专属页面"
```

---

### Task 9: 开关类控制页（扫地机/空气净化器）

**Files:**
- Create: `app/templates/devices/control_switch.html`

**关键属性 (narwa.vacuum.j5 扫地机):**
- `on` (bool, rw)
- `status` (uint, r) — 运行状态
- `sweep-mop-type` (uint, rw, 扫地/拖地/扫拖/先扫后拖)
- `suction-level` (uint, rw, 静音/标准/强力/全速)
- `battery-level` (uint, r)
- `charging-state` (uint, r)

**关键属性 (roidmi.carairpuri.v1 车载净化器):**
- 无 spec_data（使用通用模板渲染）

- [ ] **Step 1: 创建 control_switch.html**

页面结构：
1. 面包屑
2. 设备头部（含电源按钮）
3. 运行状态卡片（如有 status 属性，展示中文状态描述）
4. 核心控制项：根据 spec_data.properties 动态渲染分段选择器/滑块
5. 状态指示器（电量、充电状态等）
6. 其他属性收折展示

对于属性极多的设备（如扫地机），只展示核心可写属性（on, sweep-mop-type, suction-level, mop-water-output-level），其余属性放在"高级设置"折叠区。

- [ ] **Step 2: 浏览器验证**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_switch.html
git commit -m "feat: 开关类设备专属控制页"
```

---

### Task 10: 摄像头控制页

**Files:**
- Create: `app/templates/devices/control_camera.html`

- [ ] **Step 1: 从现有 control.html 提取摄像头相关部分**

将现有 control.html 中 `{% if device.is_camera and go2rtc_url %}` 块提取为 control_camera.html，加上共享组件和属性控制区。

- [ ] **Step 2: 浏览器验证**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control_camera.html
git commit -m "feat: 摄像头专属控制页（从通用模板提取）"
```

---

## Chunk 3: 通用兜底模板升级 + 清理

### Task 11: 升级通用兜底模板

**Files:**
- Modify: `app/templates/devices/control.html`

- [ ] **Step 1: 重写 control.html 使用共享组件**

将现有 control.html 改为：
1. 使用 `{% include "devices/components/breadcrumb.html" %}`
2. 使用 `{% include "devices/components/device_header.html" %}`
3. 属性列表保留，但视觉升级：每个属性用卡片包裹，电源属性提到顶部
4. 保留原有 JS 逻辑

- [ ] **Step 2: 验证未知设备类型仍能正确渲染**

- [ ] **Step 3: 提交**

```bash
git add app/templates/devices/control.html
git commit -m "refactor: 升级通用设备控制页使用共享组件"
```

---

### Task 12: 清理 mockup 文件 + 最终验证

**Files:**
- Delete: `app/static/mockup_dehumidifier.html`

- [ ] **Step 1: 删除临时 mockup 文件**

```bash
git rm app/static/mockup_dehumidifier.html
```

- [ ] **Step 2: 全设备类型回归测试**

在浏览器中逐一访问所有设备，确认每种类型都正确渲染：
- 除湿机 → dehumidifier 模板
- 台灯 × 2 → light 模板
- 取暖器 → heater 模板
- 空调 × 2 → thermostat 模板
- 温湿度传感器 → sensor 模板
- 扫地机 → switch 模板
- 车载净化器 → switch 或 generic 模板
- 摄像头 × 2 → camera 模板
- 路由器/行车记录仪/电水壶 → generic 兜底模板

- [ ] **Step 3: 代码检查**

```bash
cd D:/python/mijia-control && venv/Scripts/python.exe -m ruff check app/web/routes.py app/homekit/mapper.py
```

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "chore: 清理 mockup 文件，完成设备类型专属控制页"
```
