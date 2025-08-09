import subprocess
import sys

def install_and_run_certifi():
    """Install certifi and run its installation script."""
    try:
        # 安装 certifi 包
        print("正在安装/更新 certifi 模块...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "certifi"])
        print("certifi 模块已安装/更新。")

        # 导入 certifi 并运行其安装程序
        print("正在运行 certifi 证书安装程序...")
        import certifi
        import os
        import stat

        # 获取 certifi 的 cacert.pem 路径
        cafile = certifi.where()

        # 这是 Python for Windows 安装程序应该运行的脚本
        # 来安装 certifi 的 cacert.pem
        # 作为 OpenSSL 的可信证书。
        post_install_script = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "certifi", "python", "install_ssl_certificates.py")

        if os.path.exists(post_install_script):
            print(f"找到证书安装脚本: {post_install_script}")
            # 运行脚本
            subprocess.check_call([sys.executable, post_install_script])
            print("证书安装脚本执行完毕。")
        else:
            # 如果脚本不存在，我们尝试手动处理
            # 这部分逻辑比较复杂，通常 certifi 会自带脚本
            print("警告: 未找到 certifi 的证书安装脚本。请尝试手动更新您的 Python 环境或系统证书。")
            print("Certifi's CA bundle is at:", cafile)

        print("SSL 证书应该已经安装/更新。")

    except Exception as e:
        print(f"在安装证书过程中发生错误: {e}")

if __name__ == "__main__":
    install_and_run_certifi()