import os
import gradio as gr
import webbrowser
import time
import threading
import socket
import logging
from queue import Queue


def get_available_port(start_port=7860):
    """获取可用端口"""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
        port += 1


def get_default_browser_info():
    """获取默认浏览器信息"""
    try:
        browser = webbrowser.get()
        return {
            'name': type(browser).__name__,
            'path': browser.name if hasattr(browser, 'name') else 'Unknown',
            'command': browser.args[0] if hasattr(browser, 'args') and browser.args else 'Unknown'
        }
    except Exception as e:
        return {'error': str(e)}


def simple_interface(name):
    """简单的Gradio界面函数"""
    return f"Hello, {name}! Testing browser launch behavior."


def run_gradio_app(port, with_autolaunch, browser_path=None):
    """运行Gradio应用"""
    # 设置环境变量（如果需要）
    if browser_path:
        os.environ["BROWSER"] = browser_path
        logging.info(f"Set BROWSER environment variable to: {browser_path}")

    # 创建接口
    iface = gr.Interface(
        fn=simple_interface,
        inputs=gr.Textbox(label="Your Name", value="Gradio Tester"),
        outputs=gr.Textbox(label="Greeting"),
        title="Browser Launch Test",
        description=f"Testing autolaunch={with_autolaunch}"
    )

    # 启动参数
    iface.launch(
        server_port=port,
        inbrowser=with_autolaunch,
        show_error=True
    )

    # 返回URL
    return f"http://localhost:{port}"


def run_test(test_queue):
    """运行单个测试"""
    while not test_queue.empty():
        test_name, autolaunch, set_env, path = test_queue.get()
        print(f"\n▶ 正在运行 {test_name}")

        # 获取端口
        port = get_available_port()
        logging.info(f"Using port: {port}")

        # 准备浏览器路径
        browser_path = path if set_env else None

        # 在后台线程运行Gradio
        gradio_thread = threading.Thread(
            target=run_gradio_app,
            args=(port, autolaunch, browser_path),
            daemon=True
        )
        gradio_thread.start()

        # 等待Gradio启动
        time.sleep(5)

        # 记录结果
        print(f"✅ {test_name} 已启动")
        print(f"   访问URL: http://localhost:{port}")
        print(f"   按回车继续下一个测试...")

        # 等待用户确认
        input()

        # 清理环境变量
        if set_env and "BROWSER" in os.environ:
            del os.environ["BROWSER"]

        print(f"⏳ 正在关闭 {test_name}...")
        # Gradio没有提供直接关闭的API，但会随着主线程结束而关闭


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 50)
    print("Gradio 浏览器启动行为测试 (改进版)")
    print("=" * 50)
    print("注意: 每个测试将在新端口启动，按回车继续下一个测试")
    print("=" * 50)

    # 配置测试参数
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # 创建测试队列
    test_queue = Queue()
    tests = [
        ("测试1: 使用 autolaunch (默认浏览器)", True, False, None),
        ("测试2: 禁用 autolaunch", False, False, None),
        ("测试3: 使用 autolaunch + 设置Chrome环境变量", True, True, CHROME_PATH)
    ]

    # 将测试加入队列
    for test in tests:
        test_queue.put(test)

    # 运行所有测试
    run_test(test_queue)

    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)
    print("分析结果:")
    print("1. 如果测试1使用联想浏览器 → 系统默认设置问题")
    print("2. 如果测试3使用联想浏览器 → 环境变量无效")
    print("3. 如果测试2自动打开浏览器 → 程序有特殊处理")
    print("\n按回车键退出...")
    input()