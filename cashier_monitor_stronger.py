import os
import time
import zipfile
import smtplib
import json # <--- 新增导入
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# 在文件顶部添加缺失的导入
from config import APPIUM_CONFIG, EMAIL_CONFIG, SCREENSHOT_CONFIG
import ssl

# 在文件顶部添加导入
from popup_handler import PopupHandler

class CashierMonitor:
    def __init__(self):
        # 移除这行：self.app_config = APPS_CONFIG  # 修正变量名
        self.appium_config = APPIUM_CONFIG
        self.appium_server_url = self.appium_config['server_url']  # 使用配置中的URL
        self.driver = None
        self.popup_handler = None  # 添加弹窗处理器属性
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 修改截图目录逻辑，每次运行时创建一个新的带时间戳的文件夹
        self.screenshots_dir = os.path.join(SCREENSHOT_CONFIG['directory'], self.timestamp)
        
        # 创建截图目录
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
    
    def setup_driver(self, app_info=None):
        """初始化Appium驱动"""
        capabilities = {
            'platformName': self.appium_config['platformName'],
            'automationName': self.appium_config['automationName'],
            'deviceName': self.appium_config['deviceName'],
            'noReset': True,
            'skipServerInstallation': True,  # 关键修复：跳过服务器安装
            'newCommandTimeout': 600,
            'settingsAppLaunchTimeout': 10000,  # 延长设置App的启动超时时间
            'androidInstallTimeout': 10000  # 延长APK安装超时时间
        }
        
        # 如果指定了应用信息，添加应用相关配置
        if app_info:
            capabilities.update({
                'appPackage': app_info.get('package_name'),
                'appActivity': app_info.get('main_activity', None)
            })
        
        try:
            self.driver = webdriver.Remote(
                self.appium_server_url, 
                options=UiAutomator2Options().load_capabilities(capabilities)  # 修正：使用capabilities而不是self.capabilities
            )
            # 初始化弹窗处理器
            self.popup_handler = PopupHandler(self.driver)
            print("Appium驱动初始化成功")
            return True
        except Exception as e:
            print(f"Appium驱动初始化失败: {e}")
            return False
    
    def close_driver(self):
        """关闭驱动"""
        if self.driver:
            self.driver.quit()
            print("驱动已关闭")
    
    def take_screenshot(self, app_name, scene_name):
        """截图并保存"""
        try:
            filename = f"{app_name}_{scene_name}_{self.timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            self.driver.save_screenshot(filepath)
            print(f"截图已保存: {filepath}")
            return filepath
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    def handle_modal_dialogs(self, max_attempts=3):
        """调用弹窗处理器"""
        if self.popup_handler:
            self.popup_handler.handle_popups(max_attempts)
    
    def open_app(self, package_name, activity_name=None):
        """打开指定应用"""
        try:
            if activity_name:
                self.driver.start_activity(package_name, activity_name)
            else:
                self.driver.activate_app(package_name)
            time.sleep(5)  # 延长等待时间以应对启动缓慢
            print(f"应用 {package_name} 已打开")
            # 移除无条件的弹窗处理调用
            return True
        except Exception as e:
            print(f"打开应用失败: {e}")
            # 只在失败时处理弹窗
            self.handle_modal_dialogs()
            return False

    def perform_safe_action(self, step):
        """一个带自动弹窗处理和重试机制的安全操作函数。"""
        action = step.get("action")
        by_string = step.get("locatorType")
        value = step.get("locatorValue")
        timeout = step.get("timeout", 10)
        input_text = step.get("inputText", "")
        
        # 将字符串类型的 locatorType 转换为 AppiumBy 对象
        try:
            by = getattr(AppiumBy, by_string)
        except AttributeError:
            print(f"错误：无效的 locatorType: {by_string}")
            return False

        attempts = 3  # 总共尝试次数
        for i in range(attempts):
            try:
                if action == 'click':
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((by, value))
                    )
                    element.click()
                elif action == 'send_keys':
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.visibility_of_element_located((by, value))
                    )
                    element.send_keys(input_text)
                elif action == 'wait':
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by, value))
                    )
                
                print(f"操作 '{action}' 成功。")
                # 移除操作成功后的弹窗检查
                time.sleep(3)
                return True

            except (TimeoutException, NoSuchElementException):
                print(f"尝试 #{i + 1}：元素未找到或不可操作。检查是否有弹窗...")
                # 只在操作失败时处理弹窗
                self.handle_modal_dialogs()

            except Exception as e:
                print(f"执行操作时发生未知错误: {e}")
                # 只在操作失败时处理弹窗
                self.handle_modal_dialogs()

        print(f"经过 {attempts} 次尝试后，操作最终失败: {value}")
        return False
        
    # ========== 新增：通用的链路执行器 ==========
    def execute_flow(self, flow_filepath):
        """
        执行一个基于配置文件的测试链路。
        """
        try:
            with open(flow_filepath, 'r', encoding='utf-8') as f:
                flow_config = json.load(f)
        except Exception as e:
            print(f"错误：无法读取或解析链路文件 {flow_filepath}: {e}")
            return None, False

        app_name = flow_config.get("appName", "UnknownApp")
        app_package = flow_config.get("appPackage")
        
        print(f"\n--- 开始执行 {app_name} 的测试链路 ---")

        if not self.open_app(app_package):
            print(f"未能启动APP: {app_package}")
            return app_name, False
            
        for i, step in enumerate(flow_config.get("steps", [])):
            print(f"步骤 {i + 1}/{len(flow_config['steps'])}: {step['description']}")
            
            success = self.perform_safe_action(step)

            if not success:
                is_mandatory = step.get("mandatory", True)
                if is_mandatory:
                    print(f"关键步骤失败，中断 {app_name} 的测试。")
                    return app_name, False
                else:
                    print("非关键步骤失败，继续执行...")
        
        print(f"--- {app_name} 链路执行成功 ---")
        return app_name, True
    
    # ========== 重构：监控主函数 ==========
    def monitor_cashier_apps(self):
        """
        通过读取配置文件，监控各个应用的收银台
        """
        # 注意：请确保在脚本同级目录下创建一个名为 'test_flows' 的文件夹
        # 并将所有app的json配置文件放入其中
        flow_dir = 'test_flows' 
        if not os.path.isdir(flow_dir):
            print(f"错误：请创建 '{flow_dir}' 目录并放入JSON流程配置文件。")
            return

        screenshot_files = []
        
        if not self.setup_driver():
            return

        for filename in sorted(os.listdir(flow_dir)):
            if filename.endswith(".json"):
                flow_path = os.path.join(flow_dir, filename)
                
                app_name, success = self.execute_flow(flow_path)
                
                if success:
                    screenshot = self.take_screenshot(app_name, 'cashier_success')
                    if screenshot:
                        screenshot_files.append(screenshot)
                else:
                    print(f"未能成功导航到 {app_name} 的收银台。")
                    screenshot = self.take_screenshot(app_name, 'cashier_failed')
                    if screenshot:
                        screenshot_files.append(screenshot)
                time.sleep(3) # 每个app之间留出间隔

        self.close_driver()

        if screenshot_files:
            zip_path = self.zip_screenshots()
            if zip_path:
                self.send_email_with_attachment(zip_path)

    def zip_screenshots(self):
        # 压缩包也保存在本次运行的截图文件夹内
        zip_filename = f"cashier_screenshots_{self.timestamp}.zip"
        zip_filepath = os.path.join(self.screenshots_dir, zip_filename)
        
        try:
            with zipfile.ZipFile(zip_filepath, 'w') as zipf:
                # 只压缩当前时间戳文件夹内的png文件
                for file in os.listdir(self.screenshots_dir):
                    if file.endswith(".png"):
                        full_path = os.path.join(self.screenshots_dir, file)
                        zipf.write(full_path, arcname=file)
                        print(f"已添加到压缩包: {file}")
                print(f"压缩包已创建: {zip_filepath}")
                return zip_filepath
        except Exception as e:
            print(f"创建压缩包失败: {e}")
            return None

    def send_email_with_attachment(self, attachment_path):
        email_config = EMAIL_CONFIG
        if not email_config.get('send_email'):
            print("邮件发送功能已禁用。")
            return
    
        msg = MIMEMultipart()
        msg['From'] = email_config['sender_email']
        msg['To'] = email_config['recipient_email']
        msg['Subject'] = email_config['subject'].format(timestamp=self.timestamp)
    
        body = "收银台监控截图见附件。"
        msg.attach(MIMEText(body, 'plain'))
    
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part)
    
            # 创建一个安全的SSL上下文
            context = ssl.create_default_context()
        
            # 使用 SMTP_SSL，因为端口是 465
            try:
                server = smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port'], timeout=20, context=context)
                server.set_debuglevel(0)
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
                server.quit()
                print("邮件发送成功！")
            except Exception as e:
                print(f"发送邮件失败: {e}")
        except Exception as e:
            print(f"处理附件失败: {e}")

if __name__ == '__main__':
    monitor = CashierMonitor()
    print("开始收银台监控...")
    monitor.monitor_cashier_apps()
    print("监控完成！")