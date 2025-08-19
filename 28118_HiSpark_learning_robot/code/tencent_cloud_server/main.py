import asyncio
import threading
from tcp_server            import tcp_server
from websocket_server      import WebSocketServer
from logger                import logger

def run_tcp_server():
    """运行TCP服务器"""
    tcp_server.start()

def run_websocket_server():
    """运行WebSocket服务器"""
    websocket_server = WebSocketServer()
    asyncio.run(websocket_server.start())

def main():
    """主程序入口"""
    logger.info("云服务器端启动...")
    
    # 创建并启动TCP服务器线程
    tcp_thread = threading.Thread(
        target=run_tcp_server,
        name="TCP-Server",
        daemon=True
    )
    tcp_thread.start()
    
    # 在主线程运行WebSocket服务器
    run_websocket_server()

if __name__ == "__main__":
    main()