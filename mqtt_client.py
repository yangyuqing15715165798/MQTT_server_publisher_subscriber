import asyncio
import json
import time
import random
from paho.mqtt import client as mqtt_client

class MQTTClient:
    def __init__(self, broker='localhost', port=1883, client_id=None, username=None, password=None):
        # 如果没有提供客户端ID，则生成一个随机ID
        self.client_id = client_id or f'mqtt-client-{random.randint(0, 1000)}'
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        self.subscribed_topics = set()
        self.messages = []

    def connect(self):
        """连接到MQTT代理服务器"""
        # 创建客户端实例
        # self.client = mqtt_client.Client(client_id=self.client_id)
        self.client = mqtt_client.Client(client_id=self.client_id, 
                                         callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1)
        
        # 设置认证信息（如果提供）
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # 设置回调函数
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # 连接到代理服务器
        try:
            self.client.connect(self.broker, self.port)
            # 启动循环
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开与MQTT代理服务器的连接"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            print("已断开连接")
            return True
        return False

    def subscribe(self, topic, qos=0):
        """订阅主题"""
        if not self.client or not self.connected:
            print("未连接到服务器")
            return False
        
        result = self.client.subscribe(topic, qos)
        if result[0] == 0:
            self.subscribed_topics.add(topic)
            print(f"已订阅主题: {topic}, QoS: {qos}")
            return True
        else:
            print(f"订阅失败: {result}")
            return False

    def unsubscribe(self, topic):
        """取消订阅主题"""
        if not self.client or not self.connected:
            print("未连接到服务器")
            return False
        
        result = self.client.unsubscribe(topic)
        if result[0] == 0:
            if topic in self.subscribed_topics:
                self.subscribed_topics.remove(topic)
            print(f"已取消订阅主题: {topic}")
            return True
        else:
            print(f"取消订阅失败: {result}")
            return False

    def publish(self, topic, payload, qos=0, retain=False):
        """发布消息"""
        if not self.client or not self.connected:
            print("未连接到服务器")
            return False
        
        # 如果payload不是字符串，则转换为JSON字符串
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        
        result = self.client.publish(topic, payload, qos, retain)
        if result[0] == 0:
            print(f"已发布消息: {topic} -> {payload}")
            return True
        else:
            print(f"发布失败: {result}")
            return False

    def get_messages(self):
        """获取接收到的消息"""
        messages = self.messages.copy()
        self.messages = []
        return messages

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调函数"""
        if rc == 0:
            self.connected = True
            print("已连接到MQTT代理服务器")
            
            # 重新订阅之前的主题
            for topic in self.subscribed_topics:
                client.subscribe(topic)
        else:
            print(f"连接失败，返回码: {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调函数"""
        self.connected = False
        if rc != 0:
            print(f"意外断开连接，返回码: {rc}")
        else:
            print("已断开连接")

    def _on_message(self, client, userdata, msg):
        """消息接收回调函数"""
        try:
            payload = msg.payload.decode()
            print(f"收到消息: {msg.topic} -> {payload}")
            self.messages.append({
                "topic": msg.topic,
                "payload": payload,
                "qos": msg.qos,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"处理消息时出错: {e}")

def main():
    """主函数，用于测试MQTT客户端"""
    import argparse
    parser = argparse.ArgumentParser(description='MQTT客户端测试工具')
    parser.add_argument('--broker', type=str, default='localhost', help='MQTT代理服务器地址')
    parser.add_argument('--port', type=int, default=1883, help='MQTT代理服务器端口')
    parser.add_argument('--client-id', type=str, help='客户端ID')
    parser.add_argument('--username', type=str, help='用户名')
    parser.add_argument('--password', type=str, help='密码')
    args = parser.parse_args()
    
    # 创建客户端
    client = MQTTClient(
        broker=args.broker,
        port=args.port,
        client_id=args.client_id,
        username=args.username,
        password=args.password
    )
    
    # 连接
    if not client.connect():
        print("连接失败，退出程序")
        return
    
    # 交互式命令行界面
    try:
        while True:
            command = input("\n输入命令 (subscribe/unsubscribe/publish/exit): ").strip().lower()
            
            if command == 'exit':
                break
            
            elif command == 'subscribe':
                topic = input("输入主题: ").strip()
                qos = int(input("输入QoS (0/1): ").strip() or "0")
                client.subscribe(topic, qos)
            
            elif command == 'unsubscribe':
                topic = input("输入要取消订阅的主题: ").strip()
                client.unsubscribe(topic)
            
            elif command == 'publish':
                topic = input("输入主题: ").strip()
                payload = input("输入消息内容: ").strip()
                qos = int(input("输入QoS (0/1): ").strip() or "0")
                client.publish(topic, payload, qos)
            
            else:
                print("未知命令")
    
    except KeyboardInterrupt:
        print("\n程序退出")
    
    finally:
        client.disconnect()

if __name__ == "__main__":
    main() 