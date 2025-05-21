# MQTT服务器和客户端

这是一个使用Python实现的MQTT服务器和客户端，包括一个基于FastAPI的Web管理界面。

## 功能

- 完整的MQTT服务器实现（支持MQTT 3.1.1协议的主要功能）
- FastAPI构建的HTTP API和Web管理界面
- 简单的MQTT客户端，用于测试通信
- 支持用户认证、订阅管理、消息发布等功能

## 安装

1. 克隆或下载本仓库
2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动顺序

1. 首先安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动MQTT服务器和Web管理界面（只需选择其中一种方式）：

   **方式一**：使用run.py（推荐）
   ```bash
   python run.py
   ```
   
   **方式二**：直接使用api_server.py
   ```bash
   python api_server.py
   ```

3. 服务器启动后，通过浏览器访问Web管理界面：
   ```
   http://127.0.0.1:8000
   ```

4. 如果需要使用命令行客户端测试MQTT通信，运行：
   ```bash
   python mqtt_client.py
   ```

### 启动MQTT服务器的高级选项

使用`run.py`启动可以指定更多参数：

```bash
python run.py --mqtt-host 0.0.0.0 --mqtt-port 1883 --web-port 8000 --allow-anonymous True --max-connections 100 --max-keepalive 60
```

参数说明：
- `--mqtt-host` - MQTT服务器监听地址（默认：0.0.0.0）
- `--mqtt-port` - MQTT服务器端口（默认：1883）
- `--web-port` - Web管理界面端口（默认：8000）
- `--allow-anonymous` - 是否允许匿名连接（默认：True）
- `--max-connections` - 最大连接数（默认：100）
- `--max-keepalive` - 最大保持连接时间(秒)（默认：60）

### 使用MQTT客户端测试通信

```bash
python mqtt_client.py [选项]
```

选项:
- `--broker` - MQTT服务器地址（默认为localhost）
- `--port` - MQTT服务器端口（默认为1883）
- `--client-id` - 客户端ID（可选，默认随机生成）
- `--username` - 用户名（可选）
- `--password` - 密码（可选）

例如：

```bash
python mqtt_client.py --broker localhost --port 1883 --username admin --password admin

python run.py --mqtt-port 1883 --web-port 8000 --allow-anonymous True
```

## Web管理界面

通过访问 `http://127.0.0.1:8000`（或服务器IP地址）即可使用Web管理界面。界面提供以下功能：

1. **服务器配置**：
   - 设置服务器主机地址和端口
   - 设置是否允许匿名连接
   - 设置最大连接数和保持连接时间

2. **用户管理**：
   - 添加、删除用户
   - 设置用户名和密码

3. **客户端连接**：
   - 查看当前连接的客户端列表
   - 查看客户端状态和订阅信息

4. **主题订阅**：
   - 查看所有已订阅的主题
   - 查看每个主题的订阅者列表
   - 向主题发布消息

5. **MQTT客户端测试**：
   - 内置的Web MQTT客户端，用于测试连接、订阅和发布消息
   - 支持QoS 0和QoS 1
   - 实时显示接收到的消息

## API接口

Web服务器提供以下REST API接口：

- `GET /config` - 获取MQTT服务器配置
- `POST /config` - 更新MQTT服务器配置
- `GET /users` - 获取用户列表
- `POST /users` - 添加用户
- `DELETE /users/{username}` - 删除用户
- `GET /clients` - 获取客户端列表
- `GET /topics` - 获取主题订阅列表
- `POST /publish` - 向主题发布消息

## 注意事项

- 这是一个简单的MQTT服务器实现，不建议在生产环境中直接使用
- 默认监听所有网络接口（0.0.0.0），在公共网络上使用时请注意安全性
- 默认允许匿名连接，如需安全连接，请在Web界面中禁用匿名连接并添加用户

## 支持的MQTT功能

- 客户端连接和断开连接
- 主题订阅和取消订阅
- 消息发布和接收
- 基本的QoS支持（QoS 0和QoS 1）
- 简单的保活机制
- 用户认证 

## 故障排除

### 关于MQTT服务器(Broker)的说明

在某些情况下，您可能会发现不需要运行`run.py`，只需运行发布者(`waveform_publisher.py`)和订阅者(`waveform_gui.py`)即可成功通信。这是因为您的系统中可能已经有MQTT代理服务器在后台运行。

MQTT通信需要三个组件：
1. **MQTT代理服务器(Broker)** - 负责消息的中转和分发
2. **发布者(Publisher)** - 发送消息到特定主题
3. **订阅者(Subscriber)** - 接收特定主题的消息

以下情况可能导致MQTT代理服务器已在后台运行：

1. **系统已安装Mosquitto或其他MQTT服务器**：
   - Mosquitto是常见的MQTT代理服务器，它可能已经被安装并配置为系统服务
   - 默认情况下，它监听`localhost:1883`端口

2. **之前运行的服务器实例未完全关闭**：
   - 如果之前运行过`run.py`，进程可能仍在后台运行

### 如何检查系统中运行的MQTT服务器

1. **检查进程**：
   - Windows: 
     ```
     任务管理器 > 详细信息/进程 > 查找"mosquitto"或含有"mqtt"的进程
     打开cmd:
     通过服务管理器启动mosquitto指令为：
     net start mosquitto
     

     通过服务管理器停止mosquitto指令为：
     net stop mosquitto
     

     ```
     ![38fccc553f2cae1a1bafa76673b01bf9](https://github.com/user-attachments/assets/4287607a-7e07-4094-af7c-7ca6df493a0c)
     ![1747730214715_D484391A-F32C-4f76-863D-00C519DD065D](https://github.com/user-attachments/assets/b1a1695f-26af-4270-9fdf-877a15401862)
     
   - Linux/Mac: 
     ```bash
     ps aux | grep mqtt
     ps aux | grep mosquitto
     ```

2. **检查端口使用情况**：
   - Windows: 
     ```
     netstat -ano | findstr 1883
     ```
   - Linux/Mac: 
     ```bash
     netstat -an | grep 1883
     lsof -i :1883
     ```

### 解决端口冲突问题

如果您想使用自己的MQTT服务器实现而不是系统中已有的服务器：

1. **关闭现有服务**：
   - Windows: 
     ```
     通过任务管理器终止相关进程，或停止Mosquitto服务
     ```
   - Linux: 
     ```bash
     sudo service mosquitto stop    # 对于使用systemd的系统
     sudo /etc/init.d/mosquitto stop  # 对于使用init.d的系统
     ```

2. **更改端口**：
   如果无法关闭现有服务，可以更改本项目使用的端口：
   ```bash
   python run.py --mqtt-port 1884  # 使用1884端口而不是默认的1883
   ```
   
   然后在客户端和发布者中也使用相同的端口：
   ```bash
   python mqtt_client.py --port 1884
   ```

### 如何确认MQTT服务是否工作正常

如果您不确定MQTT通信是否正常工作，可以运行以下测试：

1. 运行发布者：
   ```bash
   python waveform_publisher.py
   ```

2. 运行GUI客户端订阅者：
   ```bash
   python waveform_gui.py
   ```

3. 如果GUI能显示波形数据，说明MQTT通信正常工作

无论使用哪种MQTT服务器，只要所有组件连接到同一个代理服务器，就可以实现通信。 
