import time
import json
import math
import random
import numpy as np
from paho.mqtt import client as mqtt_client

# MQTT配置
broker = 'localhost'
# 第三方提供的公共MQTT Broke
# broker = "broker.hivemq.com"
port = 1883
topic = "realtime_waveform"
client_id = f'waveform-publisher-{random.randint(0, 1000)}'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("已连接到MQTT服务器!")
        else:
            print(f"连接失败，返回码 {rc}")

    # 创建客户端
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    return client

def generate_waveform(num_points=300):
    """生成模拟波形数据"""
    # 生成基本正弦波
    x = np.linspace(0, 4*np.pi, num_points)
    base_sine = np.sin(x)
    
    # 添加一些噪声使其看起来更真实
    noise = np.random.normal(0, 0.1, num_points)
    
    # 添加一些高频分量
    high_freq = 0.2 * np.sin(10*x)
    
    # 合并波形
    waveform = base_sine + noise + high_freq
    
    # 转换为列表并四舍五入到3位小数
    return [round(float(val), 3) for val in waveform]

def publish_waveform(client):
    """发布波形数据"""
    while True:
        try:
            # 生成波形数据
            waveform_data = generate_waveform(300)
            
            # 添加时间戳和其他元数据
            data = {
                "timestamp": time.time(),
                "points": 300,
                "sampling_rate": 300,  # 300Hz采样率
                "data": waveform_data
            }
            
            # 转换为JSON并发布
            msg = json.dumps(data)
            result = client.publish(topic, msg)
            
            # 检查发布结果
            status = result[0]
            if status == 0:
                print(f"发送波形数据: {len(waveform_data)}个数据点")
            else:
                print(f"发送失败，代码: {status}")
                
            # 等待1秒
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("发布已停止")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            time.sleep(1)

def run():
    client = connect_mqtt()
    print(f"开始发布波形数据到主题: {topic}")
    print("按Ctrl+C停止")
    publish_waveform(client)

if __name__ == '__main__':
    run()