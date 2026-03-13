#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用 Python ollama 库测试连通性与持续通信。

示例：
python3 AI_assistant/mylocal/ollama_connect_test.py
python3 AI_assistant/mylocal/ollama_connect_test.py --host 192.168.1.10 --port 11434 --count 5
python3 AI_assistant/mylocal/ollama_connect_test.py --model qwen2.5:7b
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import List, Tuple

try:
    from ollama import Client
except Exception:
    Client = None  # type: ignore


def _info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def _err(msg: str) -> None:
    print(f"[ERROR] {msg}")


def _build_host(host: str, port: int) -> str:
    host = str(host or "").strip()
    if not host:
        host = "127.0.0.1"

    if host.startswith("http://") or host.startswith("https://"):
        if re.search(r":\d+$", host.split("//", 1)[-1]):
            return host.rstrip("/")
        return f"{host.rstrip('/')}:{port}"

    return f"http://{host}:{port}"


def _extract_models(data) -> List[str]:
    models: List[str] = []

    # 兼容 dict / pydantic对象 / 普通对象
    items = None
    if isinstance(data, dict):
        items = data.get("models", [])
    else:
        items = getattr(data, "models", [])

    for item in items or []:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("model") or "").strip()
        else:
            name = str(
                getattr(item, "model", None)
                or getattr(item, "name", None)
                or ""
            ).strip()

        if name:
            models.append(name)

    return models

def _extract_reply(resp) -> str:
    if isinstance(resp, dict):
        return str(resp.get("message", {}).get("content", "")).strip()

    message = getattr(resp, "message", None)
    if message is None:
        return ""

    return str(getattr(message, "content", "") or "").strip()

def _choose_model(requested: str, models: List[str]) -> Tuple[str, str]:
    requested = str(requested or "").strip()
    if requested and requested in models:
        return requested, "使用你指定的模型"
    if requested and requested not in models:
        if models:
            return models[0], f"指定模型 {requested} 不在本地，回退到 {models[0]}"
        return "", f"指定模型 {requested}，但当前 Ollama 没有拉取任何模型"
    if models:
        return models[0], f"自动选择本地首个模型 {models[0]}"
    return "", "当前 Ollama 没有可用模型"


def run_test(host: str, port: int, model: str, timeout: int, count: int, interval: float, prompt: str) -> int:
    if Client is None:
        _err("未安装 Python ollama 库。请先执行：pip install ollama")
        return 10

    endpoint = _build_host(host, port)
    _info(f"Ollama endpoint: {endpoint}")

    try:
        client = Client(host=endpoint, timeout=timeout)  # type: ignore[arg-type]
    except TypeError:
        # 兼容旧版本 SDK：不支持 timeout 参数
        try:
            client = Client(host=endpoint)  # type: ignore[arg-type]
        except Exception as e:
            _err(f"创建 Ollama 客户端失败: {e}")
            return 1
    except Exception as e:
        _err(f"创建 Ollama 客户端失败: {e}")
        return 1

    # 1) 基础连通 + 模型列表
    try:
        lst = client.list()
        models = _extract_models(lst)
    except Exception as e:
        _err(f"无法连接 Ollama 或读取模型列表失败: {e}")
        return 2

    if not models:
        _err("已连接 Ollama，但没有可用模型。请先执行：ollama pull qwen2.5:1.5b")
        return 3

    _ok(f"检测到模型 {len(models)} 个")
    for idx, name in enumerate(models[:10], start=1):
        print(f"      {idx}. {name}")

    selected_model, reason = _choose_model(model, models)
    if not selected_model:
        _err(reason)
        return 4
    _info(reason)
    _info(f"测试模型: {selected_model}")

    # 2) 持续通信测试
    failures = 0
    for i in range(1, count + 1):
        content = f"{prompt}（第{i}轮）"
        t0 = time.time()
        try:
            resp = client.chat(
                model=selected_model,
                messages=[{"role": "user", "content": content}],
                stream=False,
                keep_alive="20m",
                options={"temperature": 0.2, "num_predict": 80},
            )
            # reply = str(resp.get("message", {}).get("content", "")).strip() if isinstance(resp, dict) else ""
            reply = _extract_reply(resp)
            if not reply:
                raise RuntimeError("模型返回为空")
            cost = int((time.time() - t0) * 1000)
            _ok(f"第{i}/{count}轮成功，耗时 {cost} ms，回复: {reply[:120]}")
        except Exception as e:
            failures += 1
            _err(f"第{i}/{count}轮失败: {e}")

        if i < count and interval > 0:
            time.sleep(interval)

    if failures == 0:
        _ok("测试通过：Python ollama 库可连接并持续通信。")
        return 0

    _err(f"测试完成：{failures}/{count} 轮失败。")
    return 5


def main() -> int:
    parser = argparse.ArgumentParser(description="测试 Python ollama 库连通性与持续通信")
    parser.add_argument("--host", default=os.environ.get("USTBCHAT_OLLAMA_HOST", "127.0.0.1"), help="Ollama 主机")
    parser.add_argument("--port", type=int, default=int(os.environ.get("USTBCHAT_OLLAMA_PORT", "11434")), help="Ollama 端口")
    parser.add_argument("--model", default=os.environ.get("USTBCHAT_OLLAMA_MODEL", ""), help="指定模型名（可选）")
    parser.add_argument("--timeout", type=int, default=25, help="请求超时（秒）")
    parser.add_argument("--count", type=int, default=3, help="持续通信轮数")
    parser.add_argument("--interval", type=float, default=1.0, help="轮次间隔（秒）")
    parser.add_argument("--prompt", default="你好，请回复“连接成功”", help="测试提示词")
    args = parser.parse_args()

    if args.count <= 0:
        _err("--count 必须 > 0")
        return 9
    if args.port <= 0 or args.port > 65535:
        _err("--port 必须在 1~65535")
        return 9

    return run_test(
        host=args.host,
        port=args.port,
        model=args.model,
        timeout=args.timeout,
        count=args.count,
        interval=args.interval,
        prompt=args.prompt,
    )


if __name__ == "__main__":
    sys.exit(main())
