"""简化的配置管理器 - 直接从环境变量读取配置，无需启动脚本"""

import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional, Literal


# 默认配置
DEFAULT_GROK = {
    "api_key": "",
    "proxy_url": "",
    "proxy_urls": [],
    "proxy_pool_url": "",
    "proxy_pool_interval": 300,
    "cache_proxy_url": "",
    "cf_clearance": "",
    "x_statsig_id": "ZTpUeXBlRXJyb3I6IENhbm5vdCByZWFkIHByb3BlcnRpZXMgb2YgdW5kZWZpbmVkIChyZWFkaW5nICdjaGlsZE5vZGVzJyk=",
    "dynamic_statsig": True,
    "filtered_tags": "xaiartifact,xai:tool_usage_card",
    "show_thinking": True,
    "temporary": False,
    "max_upload_concurrency": 20,
    "max_request_concurrency": 100,
    "stream_first_response_timeout": 30,
    "stream_chunk_timeout": 120,
    "stream_total_timeout": 600,
    "retry_status_codes": [401, 429],
}

DEFAULT_GLOBAL = {
    "base_url": "http://localhost:8000",
    "log_level": "INFO",
    "image_mode": "url",
    "admin_password": "admin",
    "admin_username": "admin",
    "image_cache_max_size_mb": 512,
    "video_cache_max_size_mb": 1024,
    "max_upload_concurrency": 20,
    "max_request_concurrency": 50,
    "batch_save_interval": 1.0,
    "batch_save_threshold": 10,
    "log_max_count": 10000,
    "token_refresh_interval": 3600,
    "token_refresh_scope": "expired",
    "token_zero_expire_threshold": 3,
    "assumed_chat_quota_per_token": 80,
}


class SimpleConfigManager:
    """简化的配置管理器 - 优先从环境变量读取"""

    def __init__(self) -> None:
        """初始化配置"""
        self.config_path: Path = Path(__file__).parents[2] / "data" / "setting.toml"
        self._storage: Optional[Any] = None
        self._ensure_exists()
        self.global_config: Dict[str, Any] = self._load_with_env("global")
        self.grok_config: Dict[str, Any] = self._load_with_env("grok")

    def _ensure_exists(self) -> None:
        """确保配置存在"""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._create_default()

    def _create_default(self) -> None:
        """创建默认配置"""
        default = {"grok": DEFAULT_GROK.copy(), "global": DEFAULT_GLOBAL.copy()}
        with open(self.config_path, "w", encoding="utf-8") as f:
            toml.dump(default, f)

    def _load_with_env(self, section: Literal["global", "grok"]) -> Dict[str, Any]:
        """加载配置并用环境变量覆盖"""
        # 先加载默认配置
        if section == "grok":
            config = DEFAULT_GROK.copy()
        else:
            config = DEFAULT_GLOBAL.copy()

        # 尝试从文件加载
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = toml.load(f).get(section, {})
                    config.update(file_config)
        except Exception:
            pass  # 忽略文件读取错误，使用默认配置

        # 用环境变量覆盖
        if section == "grok":
            # Grok 配置的环境变量映射
            env_mappings = {
                "API_KEY": "api_key",
                "PROXY_URL": "proxy_url",
                "PROXY_TOKEN": "proxy_token",  # 新增代理token
                "X_STATSIG_ID": "x_statsig_id",
                "CF_CLEARANCE": "cf_clearance",
            }

            for env_key, config_key in env_mappings.items():
                if env_value := os.getenv(env_key):
                    config[config_key] = env_value

        elif section == "global":
            # Global 配置的环境变量映射
            env_mappings = {
                "ADMIN_PASSWORD": "admin_password",
                "PASSWORD": "admin_password",  # 兼容
                "BASE_URL": "base_url",
                "LOG_LEVEL": "log_level",
            }

            for env_key, config_key in env_mappings.items():
                if env_value := os.getenv(env_key):
                    config[config_key] = env_value

        return config

    def set_storage(self, storage: Any) -> None:
        """设置存储实例"""
        self._storage = storage

    def load(self, section: Literal["global", "grok"]) -> Dict[str, Any]:
        """加载配置节"""
        return self._load_with_env(section)

    async def reload(self) -> None:
        """重新加载配置"""
        self.global_config = self._load_with_env("global")
        self.grok_config = self._load_with_env("grok")


# 创建全局配置实例
setting = SimpleConfigManager()