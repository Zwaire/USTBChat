import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import threading
from bin.state.AppState import AppState

def _get_response(request: dict, timeout: float = 5.0) -> dict:
    '''
    发送请求到服务器，阻塞等待第一条响应后返回。
    利用 AppState 中存储的 ChatClient 实例发送数据，
    并临时替换其 callback 以捕获响应，完成后恢复原 callback。

    Args:
        request (dict): 待发送的请求数据
        timeout (float): 等待响应的超时秒数，默认 5 秒
    Returns:
        dict: 服务器返回的响应，超时或未连接时返回空 dict
    '''
    client = AppState().client
    if client is None or not client.running:
        return {}

    event = threading.Event()
    response_holder = {}
    original_callback = client.callback

    def _temp_callback(msg: dict):
        response_holder.update(msg)
        event.set()
        client.callback = original_callback  # 恢复原 callback

    client.callback = _temp_callback
    client.send_data(request)
    event.wait(timeout)

    # 超时时也要恢复 callback，防止泄漏
    if not event.is_set():
        client.callback = original_callback

    return response_holder
