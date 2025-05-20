import asyncio
import json
import os
import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List, Optional
import threading

# 导入我们的MQTT服务器模块
from mqtt_server import mqtt_config, clients, topics, start_mqtt_server

# 创建FastAPI应用
app = FastAPI(title="MQTT服务器管理API")

# 配置模型
class MQTTConfigModel(BaseModel):
    host: str
    port: int
    allow_anonymous: bool
    max_connections: int
    max_keepalive: int

# 用户模型
class User(BaseModel):
    username: str
    password: str

# 路由
@app.get("/", response_class=HTMLResponse)
async def get_index():
    """返回简单的HTML页面，显示MQTT服务器配置表单"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MQTT服务器配置</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                background-color: #f5f5f5;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
            }
            h1 {
                color: #333;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input, select {
                width: 100%;
                padding: 8px;
                margin-bottom: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            .tabs {
                overflow: hidden;
                border: 1px solid #ccc;
                background-color: #f1f1f1;
                border-radius: 4px 4px 0 0;
            }
            .tab {
                background-color: inherit;
                float: left;
                border: none;
                outline: none;
                cursor: pointer;
                padding: 14px 16px;
                transition: 0.3s;
                font-size: 17px;
            }
            .tab:hover {
                background-color: #ddd;
            }
            .tab.active {
                background-color: #ccc;
            }
            .tabcontent {
                display: none;
                padding: 20px;
                border: 1px solid #ccc;
                border-top: none;
                border-radius: 0 0 4px 4px;
                animation: fadeEffect 1s;
            }
            @keyframes fadeEffect {
                from {opacity: 0;}
                to {opacity: 1;}
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid #ddd;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <h1>MQTT服务器配置</h1>
        
        <div class="tabs">
            <button class="tab active" onclick="openTab(event, 'config')">服务器配置</button>
            <button class="tab" onclick="openTab(event, 'users')">用户管理</button>
            <button class="tab" onclick="openTab(event, 'clients')">客户端连接</button>
            <button class="tab" onclick="openTab(event, 'topics')">主题订阅</button>
            <button class="tab" onclick="openTab(event, 'mqtt_client')">MQTT客户端测试</button>
        </div>

        <div id="config" class="tabcontent" style="display: block;">
            <h2>服务器配置</h2>
            <form id="configForm">
                <label for="host">主机地址:</label>
                <input type="text" id="host" name="host" required>
                
                <label for="port">端口:</label>
                <input type="number" id="port" name="port" required>
                
                <label for="allow_anonymous">允许匿名连接:</label>
                <select id="allow_anonymous" name="allow_anonymous">
                    <option value="true">是</option>
                    <option value="false">否</option>
                </select>
                
                <label for="max_connections">最大连接数:</label>
                <input type="number" id="max_connections" name="max_connections" required>
                
                <label for="max_keepalive">最大保持连接时间(秒):</label>
                <input type="number" id="max_keepalive" name="max_keepalive" required>
                
                <button type="button" onclick="updateConfig()">更新配置</button>
            </form>
        </div>

        <div id="users" class="tabcontent">
            <h2>用户管理</h2>
            <form id="userForm">
                <label for="username">用户名:</label>
                <input type="text" id="username" name="username" required>
                
                <label for="password">密码:</label>
                <input type="password" id="password" name="password" required>
                
                <button type="button" onclick="addUser()">添加用户</button>
            </form>
            
            <h3>用户列表</h3>
            <div id="userList">
                <table id="userTable">
                    <tr>
                        <th>用户名</th>
                        <th>操作</th>
                    </tr>
                </table>
            </div>
        </div>

        <div id="clients" class="tabcontent">
            <h2>客户端连接</h2>
            <div id="clientList">
                <table id="clientTable">
                    <tr>
                        <th>客户端ID</th>
                        <th>用户名</th>
                        <th>订阅主题数</th>
                        <th>状态</th>
                    </tr>
                </table>
            </div>
            <button type="button" onclick="refreshClients()">刷新</button>
        </div>

        <div id="topics" class="tabcontent">
            <h2>主题订阅</h2>
            <div id="topicList">
                <table id="topicTable">
                    <tr>
                        <th>主题</th>
                        <th>订阅客户端数</th>
                        <th>操作</th>
                    </tr>
                </table>
            </div>
            <button type="button" onclick="refreshTopics()">刷新</button>
        </div>

        <div id="mqtt_client" class="tabcontent">
            <h2>MQTT客户端测试</h2>
            <div class="container">
                <h3>连接</h3>
                <form id="connectForm">
                    <label for="clientId">客户端ID:</label>
                    <input type="text" id="clientId" name="clientId" value="webclient-" required>
                    
                    <label for="clientUsername">用户名 (可选):</label>
                    <input type="text" id="clientUsername" name="clientUsername">
                    
                    <label for="clientPassword">密码 (可选):</label>
                    <input type="password" id="clientPassword" name="clientPassword">
                    
                    <button type="button" id="connectBtn" onclick="connectClient()">连接</button>
                    <button type="button" id="disconnectBtn" onclick="disconnectClient()" disabled>断开连接</button>
                </form>
            </div>
            
            <div class="container">
                <h3>订阅</h3>
                <form id="subscribeForm">
                    <label for="subscribeTopic">主题:</label>
                    <input type="text" id="subscribeTopic" name="subscribeTopic" required>
                    
                    <label for="subscribeQos">QoS:</label>
                    <select id="subscribeQos" name="subscribeQos">
                        <option value="0">0</option>
                        <option value="1">1</option>
                    </select>
                    
                    <button type="button" id="subscribeBtn" onclick="subscribeTopic()" disabled>订阅</button>
                    <button type="button" id="unsubscribeBtn" onclick="unsubscribeTopic()" disabled>取消订阅</button>
                </form>
            </div>
            
            <div class="container">
                <h3>发布</h3>
                <form id="publishForm">
                    <label for="publishTopic">主题:</label>
                    <input type="text" id="publishTopic" name="publishTopic" required>
                    
                    <label for="publishPayload">消息内容:</label>
                    <input type="text" id="publishPayload" name="publishPayload" required>
                    
                    <label for="publishQos">QoS:</label>
                    <select id="publishQos" name="publishQos">
                        <option value="0">0</option>
                        <option value="1">1</option>
                    </select>
                    
                    <button type="button" id="publishBtn" onclick="publishMessage()" disabled>发布</button>
                </form>
            </div>
            
            <div class="container">
                <h3>消息记录</h3>
                <div id="messageLog" style="height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background-color: #fff;">
                </div>
                <button type="button" onclick="clearMessages()">清除</button>
            </div>
        </div>

        <script>
            // 获取并填充当前配置
            window.onload = function() {
                getConfig();
                getUsers();
                refreshClients();
                refreshTopics();
                
                // 添加随机数到客户端ID
                document.getElementById('clientId').value += Math.floor(Math.random() * 10000);
            };
            
            // 选项卡功能
            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tab");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }
            
            // 获取MQTT配置
            function getConfig() {
                fetch('/config')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('host').value = data.host;
                        document.getElementById('port').value = data.port;
                        document.getElementById('allow_anonymous').value = data.allow_anonymous.toString();
                        document.getElementById('max_connections').value = data.max_connections;
                        document.getElementById('max_keepalive').value = data.max_keepalive;
                    })
                    .catch(error => console.error('获取配置失败:', error));
            }
            
            // 更新MQTT配置
            function updateConfig() {
                const formData = {
                    host: document.getElementById('host').value,
                    port: parseInt(document.getElementById('port').value),
                    allow_anonymous: document.getElementById('allow_anonymous').value === 'true',
                    max_connections: parseInt(document.getElementById('max_connections').value),
                    max_keepalive: parseInt(document.getElementById('max_keepalive').value)
                };
                
                fetch('/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    alert('配置已更新');
                })
                .catch(error => console.error('更新配置失败:', error));
            }
            
            // 获取用户列表
            function getUsers() {
                fetch('/users')
                    .then(response => response.json())
                    .then(data => {
                        const userTable = document.getElementById('userTable');
                        // 清除现有行，保留表头
                        while (userTable.rows.length > 1) {
                            userTable.deleteRow(1);
                        }
                        
                        // 添加用户行
                        data.forEach(username => {
                            const row = userTable.insertRow();
                            const cell1 = row.insertCell(0);
                            const cell2 = row.insertCell(1);
                            
                            cell1.textContent = username;
                            cell2.innerHTML = `<button onclick="deleteUser('${username}')">删除</button>`;
                        });
                    })
                    .catch(error => console.error('获取用户失败:', error));
            }
            
            // 添加用户
            function addUser() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                fetch('/users', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert('用户已添加');
                    getUsers();
                    document.getElementById('username').value = '';
                    document.getElementById('password').value = '';
                })
                .catch(error => console.error('添加用户失败:', error));
            }
            
            // 删除用户
            function deleteUser(username) {
                fetch(`/users/${username}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    alert('用户已删除');
                    getUsers();
                })
                .catch(error => console.error('删除用户失败:', error));
            }
            
            // 刷新客户端列表
            function refreshClients() {
                fetch('/clients')
                    .then(response => response.json())
                    .then(data => {
                        const clientTable = document.getElementById('clientTable');
                        // 清除现有行，保留表头
                        while (clientTable.rows.length > 1) {
                            clientTable.deleteRow(1);
                        }
                        
                        // 添加客户端行
                        Object.keys(data).forEach(clientId => {
                            const client = data[clientId];
                            const row = clientTable.insertRow();
                            const cell1 = row.insertCell(0);
                            const cell2 = row.insertCell(1);
                            const cell3 = row.insertCell(2);
                            const cell4 = row.insertCell(3);
                            
                            cell1.textContent = clientId;
                            cell2.textContent = client.username || '匿名';
                            cell3.textContent = client.subscriptions.length;
                            cell4.textContent = client.connected ? '已连接' : '已断开';
                        });
                    })
                    .catch(error => console.error('获取客户端失败:', error));
            }
            
            // 刷新主题列表
            function refreshTopics() {
                fetch('/topics')
                    .then(response => response.json())
                    .then(data => {
                        const topicTable = document.getElementById('topicTable');
                        // 清除现有行，保留表头
                        while (topicTable.rows.length > 1) {
                            topicTable.deleteRow(1);
                        }
                        
                        // 添加主题行
                        Object.keys(data).forEach(topic => {
                            const subscribers = data[topic];
                            const row = topicTable.insertRow();
                            const cell1 = row.insertCell(0);
                            const cell2 = row.insertCell(1);
                            const cell3 = row.insertCell(2);
                            
                            cell1.textContent = topic;
                            cell2.textContent = subscribers.length;
                            cell3.innerHTML = `<button onclick="publishToTopic('${topic}')">发布消息</button>`;
                        });
                    })
                    .catch(error => console.error('获取主题失败:', error));
            }
            
            // 弹出对话框发布消息到主题
            function publishToTopic(topic) {
                const message = prompt(`发送消息到主题 ${topic}:`, '');
                if (message === null) return;
                
                fetch('/publish', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        topic: topic,
                        message: message,
                        qos: 0
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert('消息已发布');
                })
                .catch(error => console.error('发布消息失败:', error));
            }
            
            // ==== MQTT 客户端测试 ====
            
            // 添加消息到日志
            function addMessageToLog(message, type) {
                const logDiv = document.getElementById('messageLog');
                const now = new Date();
                const timeStr = now.toLocaleTimeString();
                const msgSpan = document.createElement('div');
                msgSpan.style.marginBottom = '5px';
                
                if (type === 'info') {
                    msgSpan.style.color = 'blue';
                } else if (type === 'error') {
                    msgSpan.style.color = 'red';
                } else if (type === 'success') {
                    msgSpan.style.color = 'green';
                } else if (type === 'received') {
                    msgSpan.style.color = 'purple';
                }
                
                msgSpan.innerHTML = `<strong>[${timeStr}]</strong> ${message}`;
                logDiv.appendChild(msgSpan);
                logDiv.scrollTop = logDiv.scrollHeight;
            }
            
            // 清除消息日志
            function clearMessages() {
                document.getElementById('messageLog').innerHTML = '';
            }
            
            // 连接MQTT客户端
            function connectClient() {
                const clientId = document.getElementById('clientId').value;
                const username = document.getElementById('clientUsername').value;
                const password = document.getElementById('clientPassword').value;
                
                fetch('/mqtt/connect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: clientId,
                        username: username || null,
                        password: password || null
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addMessageToLog('已连接到MQTT服务器', 'success');
                        document.getElementById('connectBtn').disabled = true;
                        document.getElementById('disconnectBtn').disabled = false;
                        document.getElementById('subscribeBtn').disabled = false;
                        document.getElementById('publishBtn').disabled = false;
                        
                        // 开始长轮询接收消息
                        pollMessages(clientId);
                    } else {
                        addMessageToLog(`连接失败: ${data.message}`, 'error');
                    }
                })
                .catch(error => {
                    console.error('连接失败:', error);
                    addMessageToLog(`连接错误: ${error.message}`, 'error');
                });
            }
            
            // 断开MQTT客户端连接
            function disconnectClient() {
                const clientId = document.getElementById('clientId').value;
                
                fetch('/mqtt/disconnect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: clientId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    addMessageToLog('已断开连接', 'info');
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('disconnectBtn').disabled = true;
                    document.getElementById('subscribeBtn').disabled = true;
                    document.getElementById('unsubscribeBtn').disabled = true;
                    document.getElementById('publishBtn').disabled = true;
                })
                .catch(error => {
                    console.error('断开连接失败:', error);
                    addMessageToLog(`断开连接错误: ${error.message}`, 'error');
                });
            }
            
            // 订阅主题
            function subscribeTopic() {
                const clientId = document.getElementById('clientId').value;
                const topic = document.getElementById('subscribeTopic').value;
                const qos = parseInt(document.getElementById('subscribeQos').value);
                
                fetch('/mqtt/subscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: clientId,
                        topic: topic,
                        qos: qos
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addMessageToLog(`已订阅主题: ${topic}, QoS=${qos}`, 'success');
                        document.getElementById('unsubscribeBtn').disabled = false;
                    } else {
                        addMessageToLog(`订阅失败: ${data.message}`, 'error');
                    }
                })
                .catch(error => {
                    console.error('订阅失败:', error);
                    addMessageToLog(`订阅错误: ${error.message}`, 'error');
                });
            }
            
            // 取消订阅主题
            function unsubscribeTopic() {
                const clientId = document.getElementById('clientId').value;
                const topic = document.getElementById('subscribeTopic').value;
                
                fetch('/mqtt/unsubscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: clientId,
                        topic: topic
                    })
                })
                .then(response => response.json())
                .then(data => {
                    addMessageToLog(`已取消订阅主题: ${topic}`, 'info');
                    document.getElementById('unsubscribeBtn').disabled = true;
                })
                .catch(error => {
                    console.error('取消订阅失败:', error);
                    addMessageToLog(`取消订阅错误: ${error.message}`, 'error');
                });
            }
            
            // 发布消息
            function publishMessage() {
                const clientId = document.getElementById('clientId').value;
                const topic = document.getElementById('publishTopic').value;
                const payload = document.getElementById('publishPayload').value;
                const qos = parseInt(document.getElementById('publishQos').value);
                
                fetch('/mqtt/publish', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: clientId,
                        topic: topic,
                        message: payload,
                        qos: qos
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addMessageToLog(`已发布消息到主题: ${topic}, 消息: ${payload}`, 'success');
                    } else {
                        addMessageToLog(`发布失败: ${data.message}`, 'error');
                    }
                })
                .catch(error => {
                    console.error('发布失败:', error);
                    addMessageToLog(`发布错误: ${error.message}`, 'error');
                });
            }
            
            // 长轮询接收消息
            function pollMessages(clientId) {
                if (!document.getElementById('disconnectBtn').disabled) {
                    fetch(`/mqtt/messages/${clientId}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.messages && data.messages.length > 0) {
                                data.messages.forEach(msg => {
                                    addMessageToLog(`接收到消息: 主题=${msg.topic}, 内容=${msg.payload}`, 'received');
                                });
                            }
                            
                            // 继续轮询
                            setTimeout(() => pollMessages(clientId), 1000);
                        })
                        .catch(error => {
                            console.error('获取消息失败:', error);
                            setTimeout(() => pollMessages(clientId), 5000);
                        });
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

# 获取配置
@app.get("/config")
async def get_config():
    """获取MQTT服务器配置"""
    return {
        "host": mqtt_config.host,
        "port": mqtt_config.port,
        "allow_anonymous": mqtt_config.allow_anonymous,
        "max_connections": mqtt_config.max_connections,
        "max_keepalive": mqtt_config.max_keepalive
    }

# 更新配置
@app.post("/config")
async def update_config(config: MQTTConfigModel):
    """更新MQTT服务器配置"""
    mqtt_config.host = config.host
    mqtt_config.port = config.port
    mqtt_config.allow_anonymous = config.allow_anonymous
    mqtt_config.max_connections = config.max_connections
    mqtt_config.max_keepalive = config.max_keepalive
    
    return {"success": True, "message": "配置已更新"}

# 获取用户列表
@app.get("/users")
async def get_users():
    """获取MQTT用户列表"""
    return list(mqtt_config.users.keys())

# 添加用户
@app.post("/users")
async def add_user(user: User):
    """添加MQTT用户"""
    mqtt_config.users[user.username] = user.password
    return {"success": True, "message": "用户已添加"}

# 删除用户
@app.delete("/users/{username}")
async def delete_user(username: str):
    """删除MQTT用户"""
    if username in mqtt_config.users:
        del mqtt_config.users[username]
        return {"success": True, "message": "用户已删除"}
    else:
        raise HTTPException(status_code=404, detail="用户不存在")

# 获取客户端列表
@app.get("/clients")
async def get_clients():
    """获取已连接客户端列表"""
    result = {}
    for client_id, client in clients.items():
        result[client_id] = {
            "username": client.username,
            "connected": client.connected,
            "subscriptions": list(client.subscriptions)
        }
    return result

# 获取主题订阅列表
@app.get("/topics")
async def get_topics():
    """获取主题订阅列表"""
    return topics

# 向主题发布消息
@app.post("/publish")
async def publish_message(data: dict):
    """向主题发布消息"""
    topic = data.get("topic")
    message = data.get("message")
    qos = data.get("qos", 0)
    
    if not topic or message is None:
        raise HTTPException(status_code=400, detail="主题和消息不能为空")
    
    # 导入必要的函数
    from mqtt_server import publish_message as mqtt_publish
    
    # 发布消息
    await mqtt_publish("admin", topic, message.encode('utf-8'), qos)
    
    return {"success": True, "message": "消息已发布"}

# ==== Web MQTT客户端API ====

# 存储Web客户端的消息队列
web_client_messages = {}

# 连接MQTT客户端
@app.post("/mqtt/connect")
async def connect_mqtt_client(data: dict):
    """连接MQTT客户端"""
    client_id = data.get("client_id")
    username = data.get("username")
    password = data.get("password")
    
    if not client_id:
        raise HTTPException(status_code=400, detail="客户端ID不能为空")
    
    # 检查是否已经存在此客户端
    if client_id in clients:
        return {"success": False, "message": "客户端已存在"}
    
    # 初始化消息队列
    web_client_messages[client_id] = []
    
    # 这里我们模拟客户端连接到服务器
    # 在实际情况下，应该使用MQTT协议连接
    # 由于我们的MQTT服务器和API服务器在同一个进程中，
    # 我们可以直接在服务器端模拟一个客户端
    
    # 返回成功
    return {"success": True, "message": "连接成功"}

# 断开MQTT客户端连接
@app.post("/mqtt/disconnect")
async def disconnect_mqtt_client(data: dict):
    """断开MQTT客户端连接"""
    client_id = data.get("client_id")
    
    if not client_id:
        raise HTTPException(status_code=400, detail="客户端ID不能为空")
    
    # 清理消息队列
    if client_id in web_client_messages:
        del web_client_messages[client_id]
    
    return {"success": True, "message": "已断开连接"}

# 订阅主题
@app.post("/mqtt/subscribe")
async def subscribe_topic(data: dict):
    """订阅主题"""
    client_id = data.get("client_id")
    topic = data.get("topic")
    qos = data.get("qos", 0)
    
    if not client_id or not topic:
        raise HTTPException(status_code=400, detail="客户端ID和主题不能为空")
    
    # 添加订阅
    if topic not in topics:
        topics[topic] = []
    if client_id not in topics[topic]:
        topics[topic].append(client_id)
    
    return {"success": True, "message": "订阅成功"}

# 取消订阅主题
@app.post("/mqtt/unsubscribe")
async def unsubscribe_topic(data: dict):
    """取消订阅主题"""
    client_id = data.get("client_id")
    topic = data.get("topic")
    
    if not client_id or not topic:
        raise HTTPException(status_code=400, detail="客户端ID和主题不能为空")
    
    # 移除订阅
    if topic in topics and client_id in topics[topic]:
        topics[topic].remove(client_id)
        if not topics[topic]:
            del topics[topic]
    
    return {"success": True, "message": "取消订阅成功"}

# 发布消息
@app.post("/mqtt/publish")
async def publish_mqtt_message(data: dict):
    """发布MQTT消息"""
    client_id = data.get("client_id")
    topic = data.get("topic")
    message = data.get("message")
    qos = data.get("qos", 0)
    
    if not client_id or not topic or message is None:
        raise HTTPException(status_code=400, detail="客户端ID、主题和消息不能为空")
    
    # 导入必要的函数
    from mqtt_server import publish_message as mqtt_publish
    
    # 发布消息
    await mqtt_publish(client_id, topic, message.encode('utf-8'), qos)
    
    return {"success": True, "message": "消息已发布"}

# 获取消息
@app.get("/mqtt/messages/{client_id}")
async def get_mqtt_messages(client_id: str):
    """获取MQTT消息"""
    if client_id not in web_client_messages:
        web_client_messages[client_id] = []
    
    messages = web_client_messages[client_id].copy()
    web_client_messages[client_id] = []
    
    return {"success": True, "messages": messages}

# 添加消息到Web客户端
async def add_message_to_web_client(client_id, topic, payload):
    """添加消息到Web客户端的消息队列"""
    if client_id in web_client_messages:
        web_client_messages[client_id].append({
            "topic": topic,
            "payload": payload
        })

# 启动MQTT服务器的函数
def start_mqtt_server_thread():
    """在单独的线程中启动MQTT服务器"""
    asyncio.run(start_mqtt_server())

# 主程序
def main():
    # 在单独的线程中启动MQTT服务器
    mqtt_thread = threading.Thread(target=start_mqtt_server_thread, daemon=True)
    mqtt_thread.start()
    
    # 启动FastAPI服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 