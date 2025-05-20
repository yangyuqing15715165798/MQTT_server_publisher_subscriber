import asyncio
import json
import os
from typing import Dict, List, Optional, Set

# MQTT服务器的配置类
class MQTTConfig:
    def __init__(self):
        self.host = "0.0.0.0"  # 监听所有网络接口
        self.port = 1883  # 默认MQTT端口
        self.allow_anonymous = True  # 允许匿名连接
        self.users = {}  # 用户名:密码
        self.max_connections = 100  # 最大连接数
        self.max_keepalive = 60  # 最大保持连接时间（秒）

# 全局配置实例
mqtt_config = MQTTConfig()

# 客户端连接记录
class Client:
    def __init__(self, client_id: str, reader, writer):
        self.client_id = client_id
        self.reader = reader
        self.writer = writer
        self.subscriptions: Set[str] = set()
        self.connected = True
        self.username: Optional[str] = None

# 全局变量
clients: Dict[str, Client] = {}
topics: Dict[str, List[str]] = {}  # topic -> [client_ids]

# MQTT 数据包类型
CONNECT = 1
CONNACK = 2
PUBLISH = 3
PUBACK = 4
SUBSCRIBE = 8
SUBACK = 9
UNSUBSCRIBE = 10
UNSUBACK = 11
PINGREQ = 12
PINGRESP = 13
DISCONNECT = 14

# MQTT 连接返回码
CONN_ACCEPTED = 0
CONN_REFUSED_PROTOCOL = 1
CONN_REFUSED_ID = 2
CONN_REFUSED_SERVER = 3
CONN_REFUSED_USER = 4
CONN_REFUSED_AUTH = 5

async def handle_client(reader, writer):
    """处理MQTT客户端连接"""
    client_id = None
    client = None
    
    try:
        while True:
            # 读取固定头
            first_byte = await reader.readexactly(1)
            packet_type = (first_byte[0] >> 4) & 0x0F
            
            # 读取剩余长度
            multiplier = 1
            remaining_length = 0
            while True:
                byte = await reader.readexactly(1)
                remaining_length += (byte[0] & 127) * multiplier
                multiplier *= 128
                if byte[0] & 128 == 0:
                    break
            
            # 读取剩余的数据包
            if remaining_length > 0:
                payload = await reader.readexactly(remaining_length)
            else:
                payload = bytes()
            
            # 处理不同类型的MQTT数据包
            if packet_type == CONNECT:
                protocol_name_len = (payload[0] << 8) | payload[1]
                protocol_name = payload[2:2+protocol_name_len].decode('utf-8')
                offset = 2 + protocol_name_len
                protocol_level = payload[offset]
                offset += 1
                connect_flags = payload[offset]
                offset += 1
                
                # 解析保持连接时间
                keepalive = (payload[offset] << 8) | payload[offset+1]
                offset += 2
                
                # 解析客户端ID
                client_id_len = (payload[offset] << 8) | payload[offset+1]
                offset += 2
                client_id = payload[offset:offset+client_id_len].decode('utf-8')
                offset += client_id_len
                
                # 处理用户名和密码认证
                username = None
                password = None
                
                if connect_flags & 0x80:  # 用户名标志
                    username_len = (payload[offset] << 8) | payload[offset+1]
                    offset += 2
                    username = payload[offset:offset+username_len].decode('utf-8')
                    offset += username_len
                
                if connect_flags & 0x40:  # 密码标志
                    password_len = (payload[offset] << 8) | payload[offset+1]
                    offset += 2
                    password = payload[offset:offset+password_len].decode('utf-8')
                
                # 检查认证
                conn_return_code = CONN_ACCEPTED
                
                if not mqtt_config.allow_anonymous and username is None:
                    conn_return_code = CONN_REFUSED_AUTH
                
                if username is not None and username in mqtt_config.users:
                    if mqtt_config.users[username] != password:
                        conn_return_code = CONN_REFUSED_AUTH
                
                if len(clients) >= mqtt_config.max_connections:
                    conn_return_code = CONN_REFUSED_SERVER
                
                # 发送CONNACK数据包
                connack = bytearray([
                    CONNACK << 4, 2,  # 固定头，剩余长度为2
                    0,  # 连接确认标志（没有会话）
                    conn_return_code  # 连接返回码
                ])
                writer.write(connack)
                await writer.drain()
                
                if conn_return_code == CONN_ACCEPTED:
                    # 如果客户端已存在，清理旧连接
                    if client_id in clients:
                        old_client = clients[client_id]
                        old_client.connected = False
                        old_client.writer.close()
                        await old_client.writer.wait_closed()
                        # 从主题中移除旧客户端的订阅
                        for topic in old_client.subscriptions:
                            if topic in topics and client_id in topics[topic]:
                                topics[topic].remove(client_id)
                    
                    # 创建新的客户端记录
                    client = Client(client_id, reader, writer)
                    client.username = username
                    clients[client_id] = client
                    print(f"客户端 {client_id} 已连接")
                else:
                    # 连接被拒绝，关闭连接
                    writer.close()
                    await writer.wait_closed()
                    return
            
            elif packet_type == PUBLISH:
                if client is None:
                    continue
                
                # QoS位在第一个字节的1、2位
                qos = (first_byte[0] >> 1) & 0x03
                
                # 解析主题
                topic_len = (payload[0] << 8) | payload[1]
                topic = payload[2:2+topic_len].decode('utf-8')
                offset = 2 + topic_len
                
                # 对于QoS>0，提取消息ID
                message_id = None
                if qos > 0:
                    message_id = (payload[offset] << 8) | payload[offset+1]
                    offset += 2
                
                # 提取消息内容
                message = payload[offset:]
                
                print(f"收到来自客户端 {client_id} 的发布消息: 主题={topic}, 消息={message.decode('utf-8')}")
                
                # 将消息转发给所有订阅此主题的客户端
                await publish_message(client_id, topic, message, qos)
                
                # 对于QoS 1，发送PUBACK
                if qos == 1 and message_id is not None:
                    puback = bytearray([
                        PUBACK << 4, 2,  # 固定头，剩余长度为2
                        (message_id >> 8) & 0xFF,  # 消息ID高位
                        message_id & 0xFF  # 消息ID低位
                    ])
                    writer.write(puback)
                    await writer.drain()
            
            elif packet_type == SUBSCRIBE:
                if client is None:
                    continue
                
                offset = 0
                message_id = (payload[offset] << 8) | payload[offset+1]
                offset += 2
                
                # 解析订阅的主题
                granted_qos = []
                while offset < len(payload):
                    topic_len = (payload[offset] << 8) | payload[offset+1]
                    offset += 2
                    topic = payload[offset:offset+topic_len].decode('utf-8')
                    offset += topic_len
                    requested_qos = payload[offset]
                    offset += 1
                    
                    # 添加到客户端的订阅列表
                    client.subscriptions.add(topic)
                    
                    # 添加到主题的订阅者列表
                    if topic not in topics:
                        topics[topic] = []
                    if client_id not in topics[topic]:
                        topics[topic].append(client_id)
                    
                    # QoS级别我们支持最高为1
                    granted_qos.append(min(requested_qos, 1))
                    
                    print(f"客户端 {client_id} 订阅了主题: {topic}, QoS={min(requested_qos, 1)}")
                
                # 发送SUBACK数据包
                suback = bytearray([
                    SUBACK << 4, 2 + len(granted_qos),  # 固定头
                    (message_id >> 8) & 0xFF,  # 消息ID高位
                    message_id & 0xFF  # 消息ID低位
                ] + granted_qos)
                writer.write(suback)
                await writer.drain()
            
            elif packet_type == UNSUBSCRIBE:
                if client is None:
                    continue
                
                offset = 0
                message_id = (payload[offset] << 8) | payload[offset+1]
                offset += 2
                
                # 解析要取消订阅的主题
                while offset < len(payload):
                    topic_len = (payload[offset] << 8) | payload[offset+1]
                    offset += 2
                    topic = payload[offset:offset+topic_len].decode('utf-8')
                    offset += topic_len
                    
                    # 从客户端的订阅列表中移除
                    if topic in client.subscriptions:
                        client.subscriptions.remove(topic)
                    
                    # 从主题的订阅者列表中移除
                    if topic in topics and client_id in topics[topic]:
                        topics[topic].remove(client_id)
                        print(f"客户端 {client_id} 取消订阅了主题: {topic}")
                
                # 发送UNSUBACK
                unsuback = bytearray([
                    UNSUBACK << 4, 2,  # 固定头
                    (message_id >> 8) & 0xFF,  # 消息ID高位
                    message_id & 0xFF  # 消息ID低位
                ])
                writer.write(unsuback)
                await writer.drain()
            
            elif packet_type == PINGREQ:
                # 回复PINGRESP
                pingresp = bytearray([PINGRESP << 4, 0])  # 固定头，剩余长度为0
                writer.write(pingresp)
                await writer.drain()
            
            elif packet_type == DISCONNECT:
                break
    
    except asyncio.IncompleteReadError:
        # 连接断开
        pass
    except Exception as e:
        print(f"处理客户端错误: {e}")
    finally:
        # 清理
        if client_id and client_id in clients:
            clients[client_id].connected = False
            del clients[client_id]
            
            # 从所有主题中移除此客户端
            for topic in list(topics.keys()):
                if client_id in topics[topic]:
                    topics[topic].remove(client_id)
                    if not topics[topic]:  # 如果主题没有订阅者，删除主题
                        del topics[topic]
            
            print(f"客户端 {client_id} 已断开连接")
        
        writer.close()
        await writer.wait_closed()

async def publish_message(sender_id, topic, message, qos=0):
    """将消息发布到指定主题的所有订阅者"""
    # 查找与主题匹配的所有订阅者
    matching_clients = set()
    
    for t, client_ids in topics.items():
        if topic_matches(t, topic):
            matching_clients.update(client_ids)
    
    # 向所有匹配的客户端发送消息
    for client_id in matching_clients:
        if client_id == sender_id:  # 不要发送给发布者自己
            continue
        
        if client_id in clients and clients[client_id].connected:
            client = clients[client_id]
            try:
                # 构建PUBLISH数据包
                first_byte = PUBLISH << 4
                if qos > 0:
                    first_byte |= 2  # 设置QoS位
                
                # 计算可变头和负载的总长度
                topic_bytes = topic.encode('utf-8')
                var_header_len = 2 + len(topic_bytes)
                
                if qos > 0:
                    var_header_len += 2  # 消息ID长度
                
                remaining_length = var_header_len + len(message)
                
                # 编码剩余长度
                remaining_length_bytes = encode_remaining_length(remaining_length)
                
                # 构建完整的数据包
                packet = bytearray([first_byte]) + remaining_length_bytes
                
                # 添加主题
                packet.extend([len(topic_bytes) >> 8, len(topic_bytes) & 0xFF])
                packet.extend(topic_bytes)
                
                # 添加消息ID（如果QoS > 0）
                if qos > 0:
                    message_id = 1  # 简化处理，使用固定的消息ID
                    packet.extend([(message_id >> 8) & 0xFF, message_id & 0xFF])
                
                # 添加消息内容
                packet.extend(message)
                
                # 发送数据包
                client.writer.write(packet)
                await client.writer.drain()
            except Exception as e:
                print(f"向客户端 {client_id} 发送消息失败: {e}")
                client.connected = False

def encode_remaining_length(length):
    """编码MQTT数据包的剩余长度字段"""
    result = bytearray()
    while True:
        byte = length & 0x7F
        length >>= 7
        if length > 0:
            byte |= 0x80
        result.append(byte)
        if length == 0:
            break
    return result

def topic_matches(subscription_topic, publish_topic):
    """检查发布主题是否与订阅主题匹配（支持通配符）"""
    # 简单实现，不支持+和#通配符
    return subscription_topic == publish_topic

async def start_mqtt_server():
    """启动MQTT服务器"""
    server = await asyncio.start_server(
        handle_client, mqtt_config.host, mqtt_config.port)
    
    print(f"MQTT服务器启动在 {mqtt_config.host}:{mqtt_config.port}")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(start_mqtt_server())
    except KeyboardInterrupt:
        print("服务器关闭") 