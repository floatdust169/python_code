import socket
import threading
import asyncio
import time
from logger import logger
from config import config
import json
from datetime import datetime

class TCPServer:
    def __init__(self):
        self.device_connection = None   # 单一开发板连接
        self.lock = threading.Lock()
        self.device_ready = False       # 开发板就绪状态
        self.ws_server_ref = None       # 引用WebSocket服务器
        self.last_heartbeat_time = 0                # 上次收到心跳的时间
        self.heartbeat_timeout = 5                 # 心跳超时时间（秒）
        self.heartbeat_monitor_running = False      # 心跳监控是否运行


    def _start_heartbeat_monitor(self):
        """启动心跳监控线程"""
        if not self.heartbeat_monitor_running:
            self.heartbeat_monitor_running = True
            threading.Thread(
                target=self._monitor_heartbeat,
                daemon=True
            ).start()
    
    def _monitor_heartbeat(self):
        """监控心跳，检查开发板是否在线"""
        while self.heartbeat_monitor_running:
            # 检查设备是否连接
            with self.lock:
                has_connection = self.device_connection is not None
                last_time = self.last_heartbeat_time
            
            # 如果有连接但超时，则认为设备离线
            if has_connection and time.time() - last_time > self.heartbeat_timeout:
                logger.warning("开发板心跳超时，强制断开连接")
                self._cleanup_disconnected_device()
            
            time.sleep(1)  # 每秒检查一次
    
    def _cleanup_disconnected_device(self):
        """清理断开连接的设备"""
        with self.lock:
            if self.device_connection:
                try:
                    # 尝试关闭连接
                    self.device_connection.close()
                except:
                    pass
                
                # 重置状态
                self.device_connection = None
                self.device_ready = False
                self.last_heartbeat_time = 0
                
                # 通知设备离线
                self._notify_device_status("off")
                logger.info("开发板已强制断开")
    
    def set_ws_server(self, ws_server):
        """设置WebSocket服务器引用"""
        self.ws_server_ref = ws_server
    
    def _notify_device_status(self, status):
        """通知设备状态变化(如果有WebSocket服务器引用)"""
        if self.ws_server_ref:
            try:
                # 在线程中运行异步通知
                asyncio.run_coroutine_threadsafe(
                    self.ws_server_ref.broadcast_device_status(status),
                    self.ws_server_ref.loop
                )
            except Exception as e:
                logger.error(f"通知设备状态失败: {str(e)}")

    def _handle_client(self, conn: socket.socket, addr: tuple):
        """处理TCP客户端连接"""
        client_ip = addr[0]
        with self.lock:
            self.device_connection = conn
            self.device_ready = True
            self.last_heartbeat_time = time.time()  # 更新心跳时间
        
        logger.info(f"开发板已连接: {client_ip}")
        self._notify_device_status("on")        # 通知设备上线

        # 启动心跳监控
        if not self.heartbeat_monitor_running:
            self._start_heartbeat_monitor()

        try:
            # 发送初始化消息
            conn.sendall("SERVER_CONNECTED@".encode())
            
            while True:
                # TCP服务器接收开发板送来的消息
                data = conn.recv(65535)
                if not data:
                    break

                try:
                    # 先尝试UTF-8解码（覆盖大部分现代设备）
                    message = data.decode('utf-8').strip()
                except UnicodeDecodeError:
                    try:
                        # 尝试GB2312解码（兼容旧设备/中文环境）
                        message = data.decode('gb2312').strip()
                    except:
                        # 终极回退方案：用错误占位符解码
                        message = data.decode(errors='replace').strip()

                logger.info(f"收到开发板消息: {message}") # 包含心跳保活信息
                
                # 更新心跳时间
                with self.lock:
                    self.last_heartbeat_time = time.time()
                # 处理心跳消息
                if message == "Hello from device":
                    # 忽略心跳消息的处理
                    continue

                # logger.info(f"收到开发板消息: {message}")

                # 处理开发板状态消息
                if message == "GetTime":
                    # 获取当前时间并格式化为YYYYMMDDHHMMSS
                    now = datetime.now()
                    time_str = now.strftime("%Y%m%d%H%M%S")
                    logger.info(f"收到时间请求，返回: {time_str}")
                    conn.sendall(time_str.encode())
                elif message.startswith("T:") and "H:" in message:
                    # 解析温湿度数据
                    temp_part = message.split("T:")[1].split("H:")[0]
                    hum_part = message.split("H:")[1]
                    
                    # 转换为浮点数
                    temperature = float(temp_part)
                    humidity = float(hum_part)
                    
                    # 构造环境数据JSON
                    env_data = {
                        "type": "environment",
                        "temperature": temperature,
                        "humidity": humidity
                    }
                    # 转发给所有WebSocket客户端
                    if self.ws_server_ref:
                        asyncio.run_coroutine_threadsafe(
                            self.ws_server_ref.broadcast_message(json.dumps(env_data)),
                            self.ws_server_ref.loop
                        )
                        logger.info(f"已转发环境数据: T={temperature}, H={humidity}")
                elif message.startswith("delete:"):
                    # 提取任务内容
                    task_content = message.split("delete:", 1)[1]
                    
                    # 构造删除任务JSON
                    delete_data = {
                        "type": "delete",
                        "task": task_content
                    }
                    
                    # 转发给所有WebSocket客户端
                    if self.ws_server_ref:
                        asyncio.run_coroutine_threadsafe(
                            self.ws_server_ref.broadcast_message(json.dumps(delete_data)),
                            self.ws_server_ref.loop
                        )
                        logger.info(f"已转发删除任务: {task_content}")
                
        except Exception as e:
            logger.error(f"开发板通信错误: {str(e)}")
        finally:
            """开发板离线"""
            with self.lock:
                if self.device_connection == conn:
                    self.device_connection = None
                    self.device_ready = False
                    self.last_heartbeat_time = 0
                    self._notify_device_status("off")  # 通知设备离线
            try:
                conn.close()
            except:
                pass
            
            logger.info(f"开发板断开连接")

    def _broadcast_image_data(self, image_data: bytes):
        """广播图像数据到所有WebSocket客户端"""
        if self.ws_server_ref:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.ws_server_ref.broadcast_image(image_data),
                    self.ws_server_ref.loop
                )
                logger.debug(f"已广播图像数据 ({len(image_data)} 字节)")
            except Exception as e:
                logger.error(f"广播图像数据失败: {str(e)}")

    def send_to_device(self, message: str) -> bool:
        """向开发板发送消息"""
        with self.lock:
            conn = self.device_connection
            ready = self.device_ready
        
        if conn and ready:
            try:
                conn.sendall(message.encode('gb2312'))
                logger.info(f"已发送消息到开发板: {message}")
                return True
            except Exception as e:
                logger.error(f"发送消息到开发板失败: {str(e)}")
                return False
        else:
            logger.warning("开发板未连接或未就绪")
            return False
    
    def start(self):
        """启动TCP服务器"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((config.tcp_host, config.tcp_port))
            s.listen()
            logger.info(f"TCP服务器启动 {config.tcp_host}:{config.tcp_port}")
            
            while True:
                conn, addr = s.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                thread.start()

# 全局TCP服务器实例
tcp_server = TCPServer()