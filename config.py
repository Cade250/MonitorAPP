# 应用配置

# Appium配置
APPIUM_CONFIG = {
    'platformName': 'Android',
    'automationName': 'uiautomator2',
    'deviceName': '9b7dc92d',  # 请确保这是你通过 adb devices 获取到的设备ID
    'skipServerInstallation': True, # 添加此行以跳过服务器安装和设置修改
    'server_url': 'http://127.0.0.1:4723'
}

# 邮件配置
EMAIL_CONFIG = {
    'send_email': True,  # 设置为 True 来启用邮件发送
    'smtp_server': 'smtp.qq.com',  # 更改为QQ邮箱的SMTP服务器
    'smtp_port': 465,  # 更改为QQ邮箱SSL协议的端口
    'sender_email': '2779217256@qq.com',  # 请填入您的发送邮箱
    'sender_password': 'zygtjwauzopddcde',  # 请填入您的邮箱应用密码
    'recipient_email': 'lilongjie7@jd.com',  # 请填入接收邮箱
    'subject': '收银台监控报告 - {timestamp}' # 添加邮件主题
}

# 截图配置
SCREENSHOT_CONFIG = {
    'directory': 'screenshots',
    'formats': ['png'],
    'quality': 90
}