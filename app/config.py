"""应用配置"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).parent.parent
    JOBS_DIR: Path = BASE_DIR / "jobs"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    
    # Whisper 配置
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"  # cpu, cuda
    
    # Resolve 配置
    RESOLVE_SCRIPT_PATH: str = ""  # 自动检测或手动设置
    
    # LLM 配置
    OPENAI_API_KEY: str = ""  # OpenAI API Key
    OPENAI_MODEL: str = "gpt-4o"  # 推荐使用长窗口模型
    OPENAI_BASE_URL: str = ""  # 可选：自定义 API 端点（如 Azure）
    
    # 本地视觉模型配置（Ollama / LM Studio）
    USE_LOCAL_VISION: bool = True  # 是否使用本地视觉模型（推荐）
    LOCAL_VISION_PROVIDER: str = "ollama"  # ollama 或 lmstudio
    LOCAL_VISION_MODEL: str = "moondream"  # moondream 或 llava-phi3
    OLLAMA_HOST: str = "http://localhost:11434"  # Ollama 服务地址
    
    # LM Studio 配置
    LMSTUDIO_HOST: str = "http://localhost:1234/v1"  # LM Studio API 地址
    LMSTUDIO_MODEL: str = "auto"  # auto 表示使用当前加载的模型
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 确保目录存在
settings.JOBS_DIR.mkdir(exist_ok=True)
settings.UPLOADS_DIR.mkdir(exist_ok=True)
