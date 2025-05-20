#!/usr/bin/env python
"""
MQTT服务器启动脚本
"""
import argparse
import sys
from api_server import main as api_main
from mqtt_server import mqtt_config

def parse_args():
    parser = argparse.ArgumentParser(description='MQTT服务器')
    parser.add_argument('--mqtt-host', type=str, default='0.0.0.0', help='MQTT服务器主机地址')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT服务器端口')
    parser.add_argument('--web-port', type=int, default=8000, help='Web管理界面端口')
    parser.add_argument('--allow-anonymous', type=bool, default=True, help='是否允许匿名连接')
    parser.add_argument('--max-connections', type=int, default=100, help='最大连接数')
    parser.add_argument('--max-keepalive', type=int, default=60, help='最大保持连接时间(秒)')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # 更新MQTT配置
    mqtt_config.host = args.mqtt_host
    mqtt_config.port = args.mqtt_port
    mqtt_config.allow_anonymous = args.allow_anonymous
    mqtt_config.max_connections = args.max_connections
    mqtt_config.max_keepalive = args.max_keepalive
    
    # 打印欢迎信息
    print("=" * 50)
    print("MQTT服务器启动")
    print("=" * 50)
    print(f"MQTT服务器地址: {mqtt_config.host}:{mqtt_config.port}")
    print(f"Web管理界面: http://127.0.0.1:{args.web_port}")
    print(f"允许匿名连接: {'是' if mqtt_config.allow_anonymous else '否'}")
    print(f"最大连接数: {mqtt_config.max_connections}")
    print(f"最大保持连接时间: {mqtt_config.max_keepalive}秒")
    print("-" * 50)
    print("按Ctrl+C退出")
    print("=" * 50)
    
    try:
        # 启动服务器
        api_main()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0) 