import os
import json
import time
import zipfile
import smtplib
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
from config import APPS_CONFIG, APPIUM_CONFIG, EMAIL_CONFIG, SCREENSHOT_CONFIG
import ssl

class CashierMonitor:
    def __init__(self):
        self.app_config = APPS_CONFIG  # 修正变量名
        self.appium_config = APPIUM_CONFIG
        self.appium_server_url = self.appium_config['server_url']  # 使用配置中的URL
        self.driver = None
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
            'newCommandTimeout': 600
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
        """通用弹窗处理器，尝试关闭常见的模态弹窗。"""
        for _ in range(max_attempts):
            try:
                # 常见的关闭按钮文本或ID
                close_buttons = [
                    (AppiumBy.ID, "com.tencent.mm:id/j0"), # 微信青少年模式弹窗的'我知道了'
                    (AppiumBy.ID, "com.eg.android.AlipayGphone:id/update_cancel_tv"), # 支付宝更新弹窗的'稍后'
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("同意")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("允许")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("跳过")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("关闭")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.ImageView").description("关闭")'),
                    (AppiumBy.XPATH, "//*[@content-desc='关闭']"),
                    (AppiumBy.XPATH, "//*[contains(@resource-id, 'close')] | //*[contains(@resource-id, 'cancel')]")
                ]

                found_and_closed = False
                for by, value in close_buttons:
                    elements = self.driver.find_elements(by, value)
                    if elements:
                        try:
                            elements[0].click()
                            print(f"检测到并关闭了一个弹窗: {value}")
                            found_and_closed = True
                            time.sleep(2) # 等待弹窗关闭动画
                            break # 关闭一个后重新开始检测
                        except Exception:
                            pass # 元素可能已经消失
                
                if not found_and_closed:
                    return # 没有找到弹窗，退出循环

            except NoSuchElementException:
                return # 没有找到弹窗，正常返回
            except Exception as e:
                print(f"处理弹窗时发生错误: {e}")
                return
    
    def open_app(self, package_name, activity_name=None):
        """打开指定应用"""
        try:
            if activity_name:
                self.driver.start_activity(package_name, activity_name)
            else:
                self.driver.activate_app(package_name)
            time.sleep(5)  # 延长等待时间以应对启动缓慢和弹窗
            print(f"应用 {package_name} 已打开")
            self.handle_modal_dialogs() # 打开应用后立即处理弹窗
            return True
        except Exception as e:
            print(f"打开应用失败: {e}")
            return False
    
    def find_and_click_element(self, locator_type, locator_value, timeout=10):
        """查找并点击元素"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((locator_type, locator_value)))
            element.click()
            time.sleep(2)
            return True
        except TimeoutException:
            print(f"元素未找到或不可点击: {locator_value}")
            return False
        except Exception as e:
            print(f"点击元素失败: {e}")
            return False
    
    def navigate_to_cashier_wechat(self):
        """导航到微信收银台"""
        try:
            # 打开微信
            if not self.open_app('com.tencent.mm'):
                return False
            
            # 点击发现
            if self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("发现")'):
                # 点击小程序
                if self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("小程序")'):
                    # 搜索收银台相关小程序
                    self.find_and_click_element(AppiumBy.ID, 'com.tencent.mm:id/gam')
                    time.sleep(1)
                    # 输入搜索关键词
                    search_box = self.driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/cd7')
                    search_box.send_keys('收银台')
                    # 点击搜索
                    self.find_and_click_element(AppiumBy.ID, 'com.tencent.mm:id/ga_')
            
            return True
        except Exception as e:
            print(f"导航到微信收银台失败: {e}")
            return False
    
    def navigate_to_cashier_alipay(self):
        """导航到支付宝收银台"""
        try:
            # 打开支付宝
            if not self.open_app('com.eg.android.AlipayGphone'):
                return False
            
            # 点击收钱
            if self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("收钱")'):
                time.sleep(2)
                return True
            
            # 如果找不到收钱按钮，尝试其他方式
            self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("更多")')
            self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("商家服务")')
            
            return True
        except Exception as e:
            print(f"导航到支付宝收银台失败: {e}")
            return False
    
    def navigate_to_cashier_meituan(self):
        """导航到美团收银台"""
        try:
            # 打开美团
            if not self.open_app('com.sankuai.meituan'):
                return False
            
            # 点击我的
            if self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的")'):
                # 查找商家入口
                self.find_and_click_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("商家")')
                time.sleep(2)
                return True
            
            return True
        except Exception as e:
            print(f"导航到美团收银台失败: {e}")
            return False
    
    def monitor_cashier_apps(self):
        """监控各个应用的收银台"""
        apps_config = [
            {
                'name': 'WeChat',
                'package': 'com.tencent.mm',
                'navigator': self.navigate_to_cashier_wechat
            },
            {
                'name': 'Alipay',
                'package': 'com.eg.android.AlipayGphone',
                'navigator': self.navigate_to_cashier_alipay
            },
            {
                'name': 'Meituan',
                'package': 'com.sankuai.meituan',
                'navigator': self.navigate_to_cashier_meituan
            }
        ]
        
        screenshot_files = []
        
        # 首先，设置一个通用的驱动实例
        if not self.setup_driver():
            return

        for app in apps_config:
            print(f"\n开始监控 {app['name']} 收银台...")
            if app['navigator']():
                screenshot = self.take_screenshot(app['name'], 'cashier_success')
                if screenshot:
                    screenshot_files.append(screenshot)
            else:
                print(f"未能成功导航到 {app['name']} 的收银台。")
                # 即使失败也截图
                screenshot = self.take_screenshot(app['name'], 'cashier_failed')
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