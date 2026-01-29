#!/usr/bin/env python3
"""调试版本的main.py - 用于排查Zeabur启动问题"""

import os
import sys
import traceback

def main():
    print("=== DEBUG: 开始启动 ===", flush=True)
    print(f"Python版本: {sys.version}", flush=True)
    print(f"工作目录: {os.getcwd()}", flush=True)
    print(f"环境变量:", flush=True)

    # 打印关键环境变量
    env_vars = ['PORT', 'STORAGE_MODE', 'API_KEY', 'ADMIN_PASSWORD', 'X_STATSIG_ID']
    for var in env_vars:
        value = os.getenv(var, 'NOT_SET')
        # 隐藏敏感信息
        if var in ['API_KEY', 'ADMIN_PASSWORD'] and value != 'NOT_SET':
            value = value[:8] + '...'
        print(f"  {var}={value}", flush=True)

    try:
        print("=== DEBUG: 导入模块 ===", flush=True)
        from fastapi import FastAPI
        print("FastAPI导入成功", flush=True)

        from app.core.config import setting
        print("配置模块导入成功", flush=True)

        from app.core.logger import logger
        print("日志模块导入成功", flush=True)

        print("=== DEBUG: 创建应用 ===", flush=True)
        app = FastAPI(title="Debug Grok2API")

        @app.get("/health")
        async def health():
            return {"status": "healthy", "debug": True}

        print("=== DEBUG: 启动服务器 ===", flush=True)
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        print(f"启动端口: {port}", flush=True)

        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

    except Exception as e:
        print(f"=== DEBUG: 错误发生 ===", flush=True)
        print(f"错误类型: {type(e).__name__}", flush=True)
        print(f"错误信息: {str(e)}", flush=True)
        print("=== DEBUG: 完整堆栈 ===", flush=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()