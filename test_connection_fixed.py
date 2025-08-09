from appium import webdriver
from appium.options.android import UiAutomator2Options
import time
import subprocess
import os

ADB_PATH = r"D:\SoftWare\AndroidSDK\platform-tools\adb.exe"

def force_restart_adb():
    """强制重启ADB服务"""
    try:
        print("1. 强制终止所有ADB进程...")
        subprocess.run(['taskkill', '/f', '/im', 'adb.exe'], capture_output=True, timeout=10)
        time.sleep(2)
        
        print("2. 使用完整路径重启ADB...")
        env = os.environ.copy()
        env['PATH'] = os.path.dirname(ADB_PATH) + ";" + env['PATH']
        
        result = subprocess.run([ADB_PATH, 'start-server'], capture_output=True, text=True, timeout=15, env=env)
        
        if result.returncode == 0 and not "failed to start server" in result.stderr:
            print("✅ ADB服务启动成功")
            result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True, timeout=10, env=env)
            print(f"设备列表:\n{result.stdout}")
            return True
        else:
            print(f"❌ ADB启动失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 重启ADB时出错: {e}")
        return False

def cleanup_uiautomator2_server():
    """清理设备上的UIAutomator2服务"""
    print("\n3. 清理旧的UIAutomator2服务...")
    try:
        subprocess.run([ADB_PATH, 'uninstall', 'io.appium.uiautomator2.server'], capture_output=True, timeout=15)
        subprocess.run([ADB_PATH, 'uninstall', 'io.appium.uiautomator2.server.test'], capture_output=True, timeout=15)
        print("✅ UIAutomator2服务清理完成 (如果存在)。")
        return True
    except Exception as e:
        print(f"❌ 清理UIAutomator2服务时出错: {e}")
        return False

def test_appium_with_reinstall():
    """通过重装服务来测试Appium连接"""
    print("\n4. 测试Appium连接 (将重新安装服务)...")
    driver = None
    try:
        capabilities = {
            'platformName': 'Android',
            'automationName': 'uiautomator2',
            'deviceName': '9b7dc92d',
            'appPackage': 'com.android.settings', # 使用设置应用来稳定启动
            'appActivity': '.Settings',
            'skipDeviceInitialization': True,
            'skipUnlock': True,
            'skipLogcatCapture': True,
            'forceAppLaunch': True, # 强制启动应用
            'noReset': True,
            'newCommandTimeout': 300,
            'adbExecTimeout': 40000 # 增加超时以备安装
        }
        
        print("正在连接Appium服务器并安装服务...")
        driver = webdriver.Remote(
            'http://127.0.0.1:4723',
            options=UiAutomator2Options().load_capabilities(capabilities)
        )
        
        print("✅ Appium连接成功！")
        print(f"成功启动应用: {driver.current_package}")
        
        time.sleep(3)
        print("测试完成，正在退出...")
        return True
        
    except Exception as e:
        print(f"❌ Appium连接失败: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def main():
    print("=== ADB与Appium深度修复测试 ===")
    
    if not force_restart_adb():
        print("\n❌ ADB问题未能解决，请手动检查或重启电脑。")
        return

    if not cleanup_uiautomator2_server():
        print("\n⚠️ 未能清理UIAutomator2服务，但仍将继续尝试连接。")

    if test_appium_with_reinstall():
        print("\n🎉 恭喜！ADB和Appium连接均已成功！")
        print("现在您可以尝试运行您的主监控脚本了。")
    else:
        print("\n❌ Appium连接测试失败。请检查Appium服务器日志获取详细错误信息。")

if __name__ == '__main__':
    main()