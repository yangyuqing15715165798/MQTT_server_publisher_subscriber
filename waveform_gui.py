import sys
import json
import random
import time
import numpy as np
from paho.mqtt import client as mqtt_client
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QWidget, QGridLayout, QLineEdit)

# Matplotlib相关导入
import matplotlib
matplotlib.use('Qt5Agg')  # 使用Qt后端
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

#支持中文标题以及负号
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# MQTT配置
broker = 'localhost'

# 第三方提供的公共MQTT Broker
# broker = "broker.hivemq.com"
port = 1883
topic = "realtime_waveform"
client_id = f'waveform-gui-{random.randint(0, 1000)}'

class MatplotlibCanvas(FigureCanvas):
    """Matplotlib画布类"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # 创建图形
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)
        
        # 配置图形
        self.axes.grid(True)
        self.axes.set_title('实时波形数据')
        self.axes.set_xlabel('样本点')
        self.axes.set_ylabel('振幅')
        
        # 创建一个空的线条
        self.line, = self.axes.plot([], [], 'b-', linewidth=1.5)
        self.stats_text = self.fig.text(0.02, 0.95, "", fontsize=9)
        
        # 设置紧凑布局
        self.fig.tight_layout()
    
    def update_plot(self, data, stats=""):
        """更新波形图"""
        if data:
            # 更新数据
            x = np.arange(len(data))
            self.line.set_data(x, data)
            
            # 调整坐标轴范围
            self.axes.set_xlim(0, len(data)-1)
            y_min, y_max = min(data), max(data)
            y_range = max(y_max - y_min, 0.1)  # 防止范围太小
            self.axes.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
            
            # 更新统计文本
            self.stats_text.set_text(stats)
            
            # 重绘图形
            self.fig.canvas.draw_idle()

class MainWindow(QMainWindow):
    """主窗口类"""
    data_received = Signal(dict)
    connection_status = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("实时波形监测器 - Matplotlib版")
        self.resize(900, 600)
        
        # 创建MQTT客户端
        self.client = None
        self.connected = False
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 创建连接设置区域
        connection_layout = QGridLayout()
        
        # MQTT服务器设置
        self.broker_edit = QLineEdit(broker)
        connection_layout.addWidget(QLabel("服务器:"), 0, 0)
        connection_layout.addWidget(self.broker_edit, 0, 1)
        
        self.port_edit = QLineEdit(str(port))
        connection_layout.addWidget(QLabel("端口:"), 0, 2)
        connection_layout.addWidget(self.port_edit, 0, 3)
        
        self.topic_edit = QLineEdit(topic)
        connection_layout.addWidget(QLabel("主题:"), 1, 0)
        connection_layout.addWidget(self.topic_edit, 1, 1, 1, 3)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        control_layout.addWidget(self.connect_button)
        
        self.status_label = QLabel("未连接")
        control_layout.addWidget(self.status_label)
        
        self.clear_button = QPushButton("清除图表")
        self.clear_button.clicked.connect(self.clear_plot)
        control_layout.addWidget(self.clear_button)
        
        connection_layout.addLayout(control_layout, 2, 0, 1, 4)
        
        main_layout.addLayout(connection_layout)
        
        # 添加Matplotlib波形图
        self.canvas = MatplotlibCanvas(self, width=8, height=4, dpi=100)
        main_layout.addWidget(self.canvas, 1)  # 1表示拉伸比例
        
        # 添加状态栏
        self.status_bar = QLabel("准备就绪")
        main_layout.addWidget(self.status_bar)
        
        # 连接信号槽
        self.data_received.connect(self.update_waveform)
        self.connection_status.connect(self.update_connection_status)
        
        # 数据缓存
        self.last_timestamp = None
        self.timestamps = []
        self.data_buffer = []
        self.buffer_size = 10  # 存储最近10秒的数据
        
    def toggle_connection(self):
        """连接或断开MQTT服务器"""
        if not self.connected:
            self.connect_mqtt()
        else:
            self.disconnect_mqtt()
    
    def connect_mqtt(self):
        """连接到MQTT服务器"""
        try:
            broker_addr = self.broker_edit.text()
            port_num = int(self.port_edit.text())
            topic_name = self.topic_edit.text()
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self.connection_status.emit(True, "已连接")
                    client.subscribe(topic_name)
                else:
                    self.connection_status.emit(False, f"连接失败，代码: {rc}")
            
            # 创建客户端
            self.client = mqtt_client.Client(client_id=client_id, 
                                              callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1)
            self.client.on_connect = on_connect
            self.client.on_message = self.on_message
            self.client.connect(broker_addr, port_num)
            self.client.loop_start()
            
            self.status_bar.setText(f"正在连接到 {broker_addr}:{port_num}...")
            
        except Exception as e:
            self.status_bar.setText(f"连接错误: {str(e)}")
    
    def disconnect_mqtt(self):
        """断开MQTT连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self.connected = False
            self.connect_button.setText("连接")
            self.status_label.setText("已断开")
            self.status_bar.setText("已断开连接")
    
    def clear_plot(self):
        """清除图表"""
        self.canvas.line.set_data([], [])
        self.canvas.fig.canvas.draw_idle()
        self.data_buffer = []
        self.timestamps = []
        self.status_bar.setText("图表已清除")
    
    def on_message(self, client, userdata, msg):
        """处理接收到的MQTT消息"""
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            self.data_received.emit(data)
        except Exception as e:
            self.status_bar.setText(f"消息处理错误: {str(e)}")
    
    @Slot(dict)
    def update_waveform(self, data):
        """更新波形显示"""
        waveform = data.get("data", [])
        timestamp = data.get("timestamp", time.time())
        points = data.get("points", len(waveform))
        
        if waveform:
            # 保存这次数据到缓冲区
            self.timestamps.append(timestamp)
            self.data_buffer.append(waveform)
            
            # 只保留最近的buffer_size个数据
            if len(self.data_buffer) > self.buffer_size:
                self.data_buffer.pop(0)
                self.timestamps.pop(0)
            
            # 更新统计信息
            min_val = min(waveform)
            max_val = max(waveform)
            avg_val = sum(waveform) / len(waveform)
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            
            stats = f"时间: {time_str} | 数据点: {points} | 范围: {min_val:.2f} ~ {max_val:.2f} | 平均值: {avg_val:.2f}"
            
            # 更新matplotlib图表
            self.canvas.update_plot(waveform, stats)
            self.status_bar.setText(f"接收到波形数据 {time_str}")
    
    @Slot(bool, str)
    def update_connection_status(self, connected, message):
        """更新连接状态"""
        self.connected = connected
        self.status_label.setText(message)
        
        if connected:
            self.connect_button.setText("断开")
        else:
            self.connect_button.setText("连接")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.disconnect_mqtt()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())