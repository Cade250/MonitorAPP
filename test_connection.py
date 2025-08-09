from appium import webdriver
from appium.options.android import UiAutomator2Options
import time
import subprocess
import sys
import os
import psutil
import socket
import ssl

def kill_adb_processes():
    """强制终止所有ADB进程"""
    try:
        print("正在终止所有ADB进程...")
        # 使用taskkill命令
        subprocess.run(['taskkill', '/f', '/im', 'adb.exe'], 
                      capture_output=True, timeout=10)
        
        # 使用psutil确保所有进程都被终止
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'adb' in proc.info['name'].lower():
                    proc.kill()
                    print(f"终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        time.sleep(3)
        print("✅ ADB进程清理完成")
        return True
    except Exception as e:
        print(f"❌ 终止ADB进程时出错: {e}")
        return False

def get_adb_path():
    """获取ADB可执行文件的路径"""
    # 常见的ADB路径
    possible_paths = [
        r"D:\SoftWare\AndroidSDK\platform-tools\adb.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe",
        r"C:\Android\Sdk\platform-tools\adb.exe",
        r"C:\Program Files\Android\Android Studio\bin\adb.exe"
    ]
    
    # 检查PATH中的adb
    try:
        result = subprocess.run(['where', 'adb'], capture_output=True, text=True)
        if result.returncode == 0:
            paths = result.stdout.strip().split('\n')
            possible_paths.extend(paths)
    except:
        pass
    
    # 查找存在的路径
    for path in possible_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print(f"找到ADB: {expanded_path}")
            return expanded_path
    
    print("❌ 未找到ADB可执行文件")
    return None

def restart_adb_with_path(adb_path):
    """使用指定路径重启ADB服务"""
    try:
        print(f"使用路径重启ADB服务: {adb_path}")
        
        # 终止服务器
        subprocess.run([adb_path, 'kill-server'], 
                      capture_output=True, timeout=10)
        time.sleep(2)
        
        # 启动服务器
        result = subprocess.run([adb_path, 'start-server'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ ADB服务重启成功")
            return True
        else:
            print(f"❌ ADB服务重启失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 重启ADB服务时出错: {e}")
        return False

def check_adb_connection_with_path(adb_path):
    """使用指定路径检查ADB连接状态"""
    try:
        result = subprocess.run([adb_path, 'devices'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            devices = [line for line in lines[1:] if line.strip() and 'device' in line]
            if devices:
                print(f"✅ 发现 {len(devices)} 个设备:")
                for device in devices:
                    print(f"  - {device}")
                return True
            else:
                print("❌ 没有发现连接的设备")
                return False
        else:
            print(f"❌ ADB命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ ADB检查失败: {e}")
        return False

def check_adb_version(adb_path):
    """检查ADB版本"""
    try:
        result = subprocess.run([adb_path, 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"ADB版本信息:\n{result.stdout}")
            return True
        else:
            print(f"❌ 获取ADB版本失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 检查ADB版本时出错: {e}")
        return False

def test_appium_connection(adb_path):
    """测试Appium服务器连接"""
    print("正在连接Appium服务器...")
    try:
        capabilities = {
            'platformName': 'Android',
            'automationName': 'uiautomator2',
            'deviceName': '9b7dc92d',
            'skipServerInstallation': True,  # 跳过服务器安装
            'skipDeviceInitialization': True,  # 跳过设备初始化
            'skipUnlock': True,  # 跳过解锁
            'skipLogcatCapture': True,  # 跳过日志捕获
            'noReset': True,
            'dontStopAppOnReset': True,
            'newCommandTimeout': 300
        }
        appium_server_url = 'http://127.0.0.1:4723'
        
        driver = webdriver.Remote(
            appium_server_url, 
            options=UiAutomator2Options().load_capabilities(capabilities)
        )
        print("✅ Appium连接成功！")
        
        # 获取设备信息
        print(f"设备信息: {driver.capabilities.get('deviceName', 'Unknown')}")
        print(f"平台版本: {driver.capabilities.get('platformVersion', 'Unknown')}")
        
        # 简单测试：获取当前活动
        try:
            current_activity = driver.current_activity
            print(f"当前活动: {current_activity}")
        except Exception as e:
            print(f"获取当前活动失败: {e}")
        
        time.sleep(2)
        driver.quit()
        print("✅ 测试完成")
        return True
        
    except Exception as e:
        print(f"❌ Appium连接失败: {e}")
        return False

def main():
    print("=== Android设备连接诊断和修复工具 ===")
    
    # 1. 强制清理ADB进程
    print("\n1. 清理ADB进程...")
    kill_adb_processes()
    
    # 2. 获取ADB路径
    print("\n2. 查找ADB可执行文件...")
    adb_path = get_adb_path()
    if not adb_path:
        print("❌ 无法找到ADB，请确保Android SDK已正确安装")
        return False
    
    # 3. 检查ADB版本
    print("\n3. 检查ADB版本...")
    check_adb_version(adb_path)
    
    # 4. 重启ADB服务
    print("\n4. 重启ADB服务...")
    if not restart_adb_with_path(adb_path):
        print("❌ 无法重启ADB服务")
        return False
    
    # 5. 检查设备连接
    print("\n5. 检查设备连接...")
    if not check_adb_connection_with_path(adb_path):
        print("\n❌ 设备连接失败，请检查：")
        print("  - 设备是否已连接并开启USB调试")
        print("  - 是否信任了计算机的调试请求")
        print("  - 尝试重新插拔USB线")
        print("  - 重启设备和计算机")
        return False
    
    # 6. 测试Appium连接
    print("\n6. 测试Appium连接...")
    if test_appium_connection(adb_path): # 修正：传递 adb_path 参数
        print("\n🎉 所有测试通过！可以运行主程序了。")
        return True
    else:
        print("\n❌ Appium连接失败，请检查：")
        print("  - Appium服务器是否已启动 (appium)")
        print("  - 端口4723是否被占用")
        print("  - 设备名称是否正确")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)


host = 'smtp.qq.com'
port = 465

context = ssl.create_default_context()

try:
    print(f"正在尝试连接到 {host}:{port}...")
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print(f"成功连接到 {host}:{port}")
            print(f"服务器证书: {ssock.getpeercert()}\n")
            print("SSL 连接测试成功！")
except ssl.SSLError as e:
    print(f"SSL 错误: {e}")
    print("SSL 连接测试失败。这通常意味着 Python 环境缺少根证书，或者网络连接被防火墙/代理阻止。")
except Exception as e:
    print(f"发生未知错误: {e}")