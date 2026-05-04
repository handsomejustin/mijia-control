# 设备类型专属控制页设计

**日期**: 2026-05-04
**状态**: 已批准

## 背景

当前设备控制页 (`control.html`) 是通用模板，所有设备共用同一个平铺属性列表。不同设备类型（除湿机、灯、空调、传感器等）差异很大，通用模板体验不佳。

## 方案

**方案 A：每种设备类型一个独立模板**，共享通用组件。

### 目录结构

```
app/templates/devices/
├── control.html                  ← 通用兜底模板（优化后）
├── components/
│   ├── breadcrumb.html           ← 面包屑导航
│   ├── device_header.html        ← 设备头部（名称+状态+电源按钮）
│   └── status_indicator.html     ← 状态指示器小组件
├── control_dehumidifier.html     ← 除湿机
├── control_light.html            ← 灯
├── control_heater.html           ← 取暖器
├── control_thermostat.html       ← 空调伴侣
├── control_sensor.html           ← 温湿度传感器
├── control_switch.html           ← 开关类（净化器/扫地机）
└── control_camera.html           ← 摄像头
```

### 模板选择

路由层根据 `map_device()` 返回的设备类型选择模板：

```python
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
```

### DeviceCategory 变更

- 新增 `DEHUMIDIFIER = "dehumidifier"` 枚举值
- `derh` model 规则从 `THERMOSTAT` 改为 `DEHUMIDIFIER`

## 各设备类型 UI 设计

### 共享组件

**device_header**: 设备名 + 在线状态点 + 型号 + 圆形电源按钮（仅有 `on` 属性的设备显示）

**status_indicator**: 参数化小组件（图标、文字、正常/异常状态、颜色），用于除湿机/取暖器等需展示多个只读状态的设备

### 除湿机 (dehumidifier)

参考 mockup: `/static/mockup_dehumidifier.html`

- 圆形电源按钮
- 当前湿度/温度双卡片（大数字）
- 目标湿度滑块 (25%-80%, 步进5%)
- 模式分段选择器（除湿/干衣）
- 风速分段选择器（低风/高风）
- 运行状态指示器（水箱、化霜、风机）
- 童锁 toggle

### 灯 (light)

- 电源按钮
- 亮度滑块
- 色温滑块（如有，标注暖白←→冷白）
- 只读属性显示为小标签

### 取暖器 (heater)

- 当前温度/目标温度双卡片
- 目标温度滑块
- 模式分段选择器
- 状态指示器

### 空调伴侣 (thermostat)

- 当前温度/目标温度双卡片
- 目标温度滑块 (16-30°C)
- 模式分段选择器（制冷/制热/自动/送风）
- 风速分段选择器（低/中/高）

### 温湿度传感器 (temperature_sensor)

- 纯只读展示，无控制项
- 温度/湿度大数字卡片 + 只读进度条
- 电池电量标签

### 开关类 (switch)

- 电源按钮
- 模式分段选择器
- 状态指示器
- 覆盖空气净化器、扫地机等

### 摄像头 (camera)

- 从现有模板提取摄像头相关部分
- 加上共享 header/breadcrumb

### 通用兜底 (control.html)

- 保持现有属性列表
- 视觉升级：卡片化、更好的分组、电源按钮提到顶部

## 技术要点

- 所有模板使用 Tailwind CSS + Alpine.js（与现有项目一致）
- 路由层通过 `map_device()` 判断类型，选择模板
- 模板内 JavaScript 复用现有的 `getProp`/`setProp`/`toggleProp` API 调用模式
- 页面加载时自动读取所有属性值填充 UI
