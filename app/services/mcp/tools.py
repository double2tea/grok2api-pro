# -*- coding: utf-8 -*-
"""MCP Tools - Grok AI 对话工具"""

import json
from typing import Optional, List, Dict, Any
from app.services.grok.client import GrokClient
from app.core.logger import logger
from app.core.exception import GrokApiException
from app.models.grok_models import Models


async def ask_grok_impl(
    query: str, model: str = "grok-3-fast", system_prompt: Optional[str] = None
) -> str:
    """
    内部实现: 调用Grok API并收集完整响应

    Args:
        query: 用户问题
        model: 模型名称
        system_prompt: 系统提示词

    Returns:
        str: 完整的Grok响应内容
    """
    try:
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        # 构建请求
        request_data = {"model": model, "messages": messages, "stream": True}

        logger.info(f"[MCP] ask_grok 调用, 模型: {model}")

        # 调用Grok客户端(流式)
        response_iterator = await GrokClient.openai_to_grok(request_data)

        # 收集所有流式响应块
        content_parts = []
        async for chunk in response_iterator:
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")

            # 解析SSE格式
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        if content := delta.get("content"):
                            content_parts.append(content)
                except json.JSONDecodeError:
                    continue

        result = "".join(content_parts)
        logger.info(f"[MCP] ask_grok 完成, 响应长度: {len(result)}")
        return result

    except GrokApiException as e:
        logger.error(f"[MCP] Grok API错误: {str(e)}")
        raise Exception(f"Grok API调用失败: {str(e)}")
    except Exception as e:
        logger.error(f"[MCP] ask_grok异常: {str(e)}", exc_info=True)
        raise Exception(f"处理请求时出错: {str(e)}")


async def generate_image_impl(prompt: str, model: str = "grok-3-fast") -> str:
    """
    内部实现: 调用Grok API生成图片
    """
    # Grok通过在提示词中包含特定关键词触发绘图
    # 这里我们包装一下提示词以确保触发
    enhanced_prompt = f"generate an image of {prompt}"
    return await ask_grok_impl(enhanced_prompt, model)


async def generate_video_impl(
    prompt: str, image_url: str, model: str = "grok-imagine-0.9"
) -> str:
    """
    内部实现: 调用Grok API生成视频
    """
    try:
        # 构建消息列表 (多模态)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        # 构建请求
        request_data = {"model": model, "messages": messages, "stream": True}

        logger.info(f"[MCP] generate_video 调用, 模型: {model}")

        # 调用Grok客户端
        response_iterator = await GrokClient.openai_to_grok(request_data)

        # 收集响应
        content_parts = []
        async for chunk in response_iterator:
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")

            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        if content := delta.get("content"):
                            content_parts.append(content)
                except:
                    continue

        result = "".join(content_parts)
        logger.info("[MCP] generate_video 完成")
        return result

    except Exception as e:
        logger.error(f"[MCP] 视频生成失败: {str(e)}")
        raise Exception(f"视频生成失败: {str(e)}")


async def list_models_impl() -> str:
    """
    内部实现: 获取可用模型列表
    """
    try:
        model_names = Models.get_all_model_names()
        # 格式化为Markdown列表
        result = "### Available Grok Models\n\n"
        result += "| Model ID | Type | Image Gen | Video Gen |\n"
        result += "|----------|------|-----------|-----------|\n"

        for model_name in model_names:
            model_info = Models.get_model_info(model_name)
            mid = model_name
            mtype = "Basic/Super"
            # 检查是否是视频模型
            is_video_model = model_info.get("is_video_model", False)
            img = "✅"  # 大部分模型都支持绘图（通过提示词触发）
            vid = "✅" if is_video_model else "❌"
            result += f"| `{mid}` | {mtype} | {img} | {vid} |\n"

        return result
    except Exception as e:
        return f"Failed to list models: {str(e)}"
