# 用Python打造MQTT服务器与可视化管理平台——实战全流程

## 一、项目背景

物联网和实时数据采集场景中，MQTT协议因其轻量、发布/订阅模式、跨平台等优势被广泛应用。市面上虽然有如Mosquitto等成熟MQTT Broker，但如果你想要**自定义协议细节、集成Web管理、嵌入业务逻辑**，用Python自研一套MQTT服务器+管理平台是很有价值的实践。

本项目实现了：
- 纯Python编写的MQTT服务器（支持基本协议）
- FastAPI打造的Web管理界面，支持参数配置、用户管理、主题监控等
- 实时波形数据的发布与可视化（支持300点/秒）
- 支持命令行和GUI（PySide6+matplotlib）两种客户端

## 二、技术选型

- **Python 3.8+**：开发主语言，生态丰富，易于扩展
- **asyncio**：高并发异步网络通信
- **FastAPI**：现代Web API框架，自动文档、性能优异
- **paho-mqtt**：MQTT客户端库，兼容主流Broker
- **PySide6 + matplotlib**：桌面GUI与专业波形绘图
- **numpy**：高效数值计算，生成模拟波形

## 三、系统架构

```
+-------------------+         +-------------------+         +-------------------+
|   waveform_gui.py |<------->|   MQTT Broker     |<------->| waveform_publisher|
| (PySide6+matplot) |   MQTT  | (run.py/api_server|   MQTT  |   (数据发布脚本)   |
+-------------------+         +-------------------+         +-------------------+
         ^                        ^
         |                        |
         |  HTTP/WebSocket        |
         +------------------------+
         |   FastAPI管理界面      |
         +------------------------+
```
- **MQTT Broker**：可用本项目自带的run.py/api_server.py，也可用Mosquitto等第三方
- **Web管理界面**：通过FastAPI提供，支持配置、监控、测试
- **数据发布/订阅**：waveform_publisher.py定时发布波形，waveform_gui.py实时订阅并可视化

## 四、核心代码讲解

### 1. MQTT服务器（mqtt_server.py）
- 纯Python实现MQTT 3.1.1协议的核心流程：连接、认证、订阅、发布、心跳、断开
- 支持匿名/用户名密码认证、最大连接数、主题订阅管理
- 采用asyncio高并发处理多个客户端

**关键片段：**
```python
async def handle_client(reader, writer):
    # 解析MQTT协议包，处理CONNECT/PUBLISH/SUBSCRIBE等
    ...
    if packet_type == CONNECT:
        # 认证、分配client_id、返回CONNACK
    elif packet_type == PUBLISH:
        # 主题分发，转发消息给订阅者
    ...
```

### 2. FastAPI管理界面（api_server.py）
- 提供RESTful API和Web前端，支持：
  - 服务器参数配置
  - 用户管理
  - 客户端/主题监控
  - 在线测试MQTT连接、订阅、发布
- 支持通过Web动态调整MQTT参数，无需重启

**关键片段：**
```python
@app.get("/config")
async def get_config():
    return {
        "host": mqtt_config.host,
        "port": mqtt_config.port,
        ...
    }

@app.post("/publish")
async def publish_message(data: dict):
    await mqtt_publish("admin", data["topic"], data["message"].encode('utf-8'), data.get("qos", 0))
    return {"success": True}
```

### 3. 实时波形数据发布（waveform_publisher.py）
- 每秒生成300个点的模拟波形（正弦+噪声+高频分量）
- 通过MQTT定时发布到指定主题

**关键片段：**
```python
def generate_waveform(num_points=300):
    x = np.linspace(0, 4*np.pi, num_points)
    base_sine = np.sin(x)
    noise = np.random.normal(0, 0.1, num_points)
    high_freq = 0.2 * np.sin(10*x)
    waveform = base_sine + noise + high_freq
    return [round(float(val), 3) for val in waveform]

# 发布循环
while True:
    data = {"timestamp": time.time(), "points": 300, "data": generate_waveform(300)}
    client.publish(topic, json.dumps(data))
    time.sleep(1)
```

### 4. 实时波形可视化（waveform_gui.py）
- PySide6打造桌面GUI，matplotlib嵌入实时绘图
- 支持连接/断开、主题切换、数据统计、清除图表
- 自动适应数据范围，显示最小/最大/均值等统计信息

**关键片段：**
```python
class MatplotlibCanvas(FigureCanvas):
    def update_plot(self, data, stats=""):
        x = np.arange(len(data))
        self.line.set_data(x, data)
        self.axes.set_xlim(0, len(data)-1)
        ...
        self.fig.canvas.draw_idle()
```

## 五、常见问题与排查

### 1. 为什么不启动run.py也能通信？
- 你的系统可能已安装并运行了Mosquitto等MQTT Broker（默认监听1883端口）
- 发布者和订阅者只要连到同一个Broker即可，无论是本项目的还是系统服务

### 2. 如何检查和管理Mosquitto服务？
- Windows：
  - 任务管理器查找"mosquitto"进程
  - CMD下用服务命令：
    ```
    net start mosquitto   # 启动
    net stop mosquitto    # 停止
    ```
- Linux：
  ```bash
  sudo service mosquitto status
  sudo service mosquitto stop
  ```

### 3. 端口冲突怎么办？
- 关闭占用1883端口的服务，或将本项目MQTT端口改为1884等
- 客户端和发布者也要用相同端口

### 4. 如何确认MQTT链路正常？
- 先运行waveform_publisher.py，再运行waveform_gui.py
- GUI能实时显示波形即说明链路畅通

## 六、总结

本项目完整演示了如何用Python自研MQTT服务器、集成Web管理、实现实时数据采集与可视化。适合物联网、数据采集、教学演示等场景。你可以基于此项目：
- 深入学习MQTT协议原理
- 扩展更多业务逻辑（如数据存储、报警、权限控制等）
- 集成到自己的物联网平台

**开源即自由，欢迎Star和二次开发！** 