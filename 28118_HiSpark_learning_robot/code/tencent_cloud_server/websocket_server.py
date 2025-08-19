import asyncio
import websockets
import json
from websockets.server import serve
from logger import logger
from tcp_server import tcp_server
from config import config

async def message_process(websocket, data):
    """处理WebSocket消息"""
    # 验证消息格式
    if 'type' not in data:
        await websocket.send(json.dumps({
            "status": "ERROR",
            "message": "Missing 'type' field in message"
        }))
        return False

    # 处理控制类消息
    if data['type'] == 'control':
        command = data['command']
        
        if command in ["led_on", "led_off"]:
            success = tcp_server.send_to_device(command)
            response = {
                "status": "SUCCESS" if success else "ERROR",
                "message": f"{command}_SUCCESS" if success else "DEVICE_NOT_CONNECTED"
            }
            await websocket.send(json.dumps(response))
        else:
            await websocket.send(json.dumps({
                "status": "ERROR",
                "message": f"Unknown command: {command}"
            }))
    elif data['type'] == 'task_list':
        if 'tasks' not in data:
            await websocket.send(json.dumps({
                "status": "ERROR",
                "message": "Task_list message requires 'tasks' field"
            }))
            return False
            
        tasks = data['tasks']
        # 将任务列表转换为特定格式字符串
        task_string = ''.join(f"*{task}@" for task in tasks) + '#'

        logger.info(f"转换后任务字符串: {task_string}")
        
        # 通过TCP发送给开发板
        success = tcp_server.send_to_device(task_string)
        response = {
            "status": "SUCCESS" if success else "ERROR",
            "message": "TASK_SENT" if success else "TASK_SEND_FAILED"
        }
        await websocket.send(json.dumps(response))
    else:
        await websocket.send(json.dumps({
            "status": "ERROR",
            "message": f"Unsupported message type: {data['type']}"
        }))
    return True

class WebSocketServer:
    def __init__(self):
        self.active_connections = set()  # 存储所有活跃的WebSocket连接
        self.loop = None                 # 存储当前事件循环

    async def broadcast_message(self, message: str):
        """向所有客户端广播文本消息"""
        if not self.active_connections:
            return
        
        logger.info(f"广播消息: {message}")
        
        # 向所有活跃连接发送消息
        for connection in self.active_connections.copy():  # 使用副本避免在迭代时修改集合
            try:
                await connection.send(message)
            except websockets.exceptions.ConnectionClosed:
                # 如果连接已关闭，从集合中移除
                self.active_connections.discard(connection)
            except Exception as e:
                logger.error(f"发送消息到客户端失败: {str(e)}")
        
    async def broadcast_device_status(self, status):
        """向所有连接的小程序客户端广播设备状态"""
        message = json.dumps({
            "type": "device_status",
            "status": status
        })
        
        logger.info(f"广播设备状态: {status}")
        
        # 向所有活跃连接发送消息
        for connection in self.active_connections.copy():  # 使用副本避免在迭代时修改集合
            try:
                await connection.send(message)
            except websockets.exceptions.ConnectionClosed:
                # 如果连接已关闭，从集合中移除
                self.active_connections.discard(connection)
    
    async def handler(self, websocket):
        """处理微信小程序建立的WebSocket连接"""
        client_ip = websocket.remote_address[0]
        logger.info(f"小程序连接来自 {client_ip}")
        
        self.active_connections.add(websocket) # 将新连接添加到活跃连接集合

        try:
            # 客户端连接后立即发送设备状态
            with tcp_server.lock:
                status = "on" if tcp_server.device_ready else "off"
                
            await websocket.send(json.dumps({
                "type": "device_status",
                "status": status
            }))

            await websocket.send(json.dumps({"status": "SERVER_READY"}))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"收到小程序消息: {data}")

                    # 这里必须使用await调用协程
                    await message_process(websocket, data)
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "status": "ERROR",
                        "message": "Invalid JSON format"
                    }))
                    logger.error("收到非JSON格式消息")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("小程序断开连接")
        except Exception as e:
            logger.error(f"WebSocket处理错误: {str(e)}")
        finally:
            # 确保连接关闭时从活跃连接中移除
            self.active_connections.discard(websocket)

    async def start(self):
        # 存储当前事件循环
        self.loop = asyncio.get_running_loop()
        
        # 设置TCP服务器的WebSocket引用
        tcp_server.set_ws_server(self)
        
        async with serve(
            self.handler,
            config.websocket_host,
            config.websocket_port
        ):
            logger.info(f"WebSocket服务器启动 {config.websocket_host}:{config.websocket_port}")
            await asyncio.Future()