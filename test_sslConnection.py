import socket
import ssl

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
