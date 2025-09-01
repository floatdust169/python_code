"""
AI智能知识库检索系统 - 依赖安装脚本
用于初始化项目环境
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装项目依赖"""
    print("🔧 正在安装项目依赖包...")
    print("=" * 50)
    
    dependencies = [
        "flask",
        "flask-cors", 
        "python-docx",
        "PyPDF2",
        "jieba",
        "volcengine-python-sdk"
    ]
    
    for package in dependencies:
        print(f"📦 安装 {package}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True)
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {package} 安装失败")
            return False
    
    print("=" * 50)
    print("🎉 所有依赖安装完成！")
    return True

def create_directories():
    """创建必要的目录"""
    print("📁 创建必要目录...")
    
    directories = [
        "uploads",
        "data",
        "pic"
    ]
    
    for dir_name in directories:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ 创建目录：{dir_name}")
        else:
            print(f"📂 目录已存在：{dir_name}")

def main():
    """主函数"""
    print("🚀 AI智能知识库检索系统 - 环境初始化")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        input("按任意键退出...")
        return False
    
    print(f"🐍 Python版本：{sys.version}")
    
    # 创建目录
    create_directories()
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，请检查网络连接")
        input("按任意键退出...")
        return False
    
    print("\n🎯 环境初始化完成！")
    print("💡 现在可以运行以下命令启动系统：")
    print("   python start.py")
    print("   或者双击：启动AI知识库.bat")
    
    input("按任意键退出...")
    return True

if __name__ == "__main__":
    main()
