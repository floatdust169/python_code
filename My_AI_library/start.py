#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能知识库检索系统 - 启动脚本
统一的服务器启动入口
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def main():
    """主启动函数"""
    print("🚀 启动AI智能知识库检索系统...")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    server_file = script_dir / "library_server.py"
    
    if not server_file.exists():
        print(f"❌ 找不到服务器文件: {server_file}")
        sys.exit(1)
    
    try:
        # 启动服务器
        print("🌐 启动服务器...")
        process = subprocess.Popen([
            sys.executable, str(server_file)
        ], cwd=str(script_dir))
        
        print(f"✅ 服务器进程已启动 (PID: {process.pid})")
        print("📱 访问地址:")
        print("   本地: http://localhost:5000")
        print("   公网: http://152.136.167.211:5000")
        print("=" * 50)
        print("按 Ctrl+C 停止服务器")
        
        # 等待进程结束
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭服务器...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("强制终止服务器进程...")
            process.kill()
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
