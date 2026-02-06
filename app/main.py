"""FastAPI 主应用入口（最小骨架）"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager

from .api.routes_ingest import router as ingest_router
from .api.routes_analyze import router as analyze_router
from .api.routes_execute import router as execute_router
from .api.routes_llm import router as llm_router
from .api.routes_jobs import router as jobs_router
from .api.routes_projects import router as projects_router
from .api.routes_exports import router as exports_router
from .api.routes_assembly import router as assembly_router
from .api.routes_visual import router as visual_router
from .api.routes_storyteller import router as storyteller_router
from .api.routes_orchestrator import router as orchestrator_router
from .api.routes_runtime import router as runtime_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("\n" + "="*60)
    print("🚀 AutoCut Director 启动中...")
    print("="*60)
    
    # 1. 检测运行时配置
    from .core.runtime_profile import get_runtime_profile, save_runtime_profile
    from .core.execution_policy import get_execution_policy
    from .core.runtime_monitor import start_runtime_monitor, get_runtime_monitor
    from .config import settings
    
    print("\n📊 检测运行时配置...")
    profile = get_runtime_profile()
    
    # 保存到磁盘
    profile_path = settings.BASE_DIR / "runtime_profile.json"
    save_runtime_profile(profile_path)
    print(f"✓ 配置文件已保存: {profile_path}")
    
    # 显示配置说明
    print("\n" + profile.get_explanation())
    
    # 2. 生成执行策略
    print("\n📋 生成执行策略...")
    policy = get_execution_policy()
    print(f"✓ Vision: {policy.vision.provider} / {policy.vision.model}")
    print(f"✓ Planning: {policy.planning.provider} / {policy.planning.model}")
    print(f"✓ Editing: {policy.editing.executor}")
    
    # 3. 启动运行时监控
    print("\n🔍 启动运行时监控...")
    monitor = get_runtime_monitor()
    
    # 注册降级回调
    def on_degradation(reason: str):
        print(f"\n⚠️  自动降级触发: {reason}")
        from .core.execution_policy import degrade_execution_policy
        degrade_execution_policy(reason)
    
    monitor.register_degradation_callback(on_degradation)
    start_runtime_monitor()
    
    print("\n" + "="*60)
    print("✅ AutoCut Director 启动完成")
    print("="*60 + "\n")
    
    yield
    
    # 关闭时清理
    print("\n🛑 AutoCut Director 关闭中...")
    from .core.runtime_monitor import stop_runtime_monitor
    stop_runtime_monitor()
    print("✅ 已关闭")


app = FastAPI(
    title="AutoCut Director",
    description="AI-driven video editing automation with DaVinci Resolve",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 注册产品级路由（优先）
app.include_router(projects_router)  # 项目管理（已包含 /api/projects 前缀）
app.include_router(assembly_router)  # 零散镜头组装（已包含 /api/assembly 前缀）
app.include_router(exports_router)   # 导出管理（已包含 /api/exports 前缀）

# 注册技术级路由（开发者专用）
app.include_router(runtime_router)   # 运行时配置路由（已包含 /api/runtime 前缀）
app.include_router(orchestrator_router)  # 调度器路由（已包含 /api/orchestrator 前缀）
app.include_router(ingest_router)  # Ingest 路由（已包含 /api/ingest 前缀）
app.include_router(jobs_router)    # Jobs 路由（已包含 /api/jobs 前缀）
app.include_router(visual_router)  # 视觉分析路由（已包含 /api/visual 前缀）
app.include_router(storyteller_router)  # 视觉叙事路由（已包含 /api/storyteller 前缀）
app.include_router(analyze_router, prefix="/api/analyze", tags=["analyze"])
app.include_router(execute_router, prefix="/api/execute", tags=["execute"])
app.include_router(llm_router, prefix="/api/llm", tags=["llm"])


@app.get("/")
async def root():
    """根路径 - 返回用户 UI"""
    app_file = Path(__file__).parent / "static" / "app.html"
    if app_file.exists():
        return FileResponse(app_file)
    
    # 返回运行时状态
    from .core.runtime_profile import get_runtime_profile
    from .core.execution_policy import get_execution_policy
    
    profile = get_runtime_profile()
    policy = get_execution_policy()
    
    return {
        "name": "AutoCut Director",
        "version": "2.0.0",
        "status": "running",
        "ui": "/app",
        "runtime": {
            "profile_class": profile.profile_class,
            "degraded": profile.degraded,
            "vision_provider": policy.vision.provider,
            "vision_model": policy.vision.model
        }
    }


@app.get("/app")
async def app_ui():
    """用户界面"""
    app_file = Path(__file__).parent / "static" / "app.html"
    if app_file.exists():
        return FileResponse(app_file)
    return {"error": "UI not found"}


@app.get("/admin")
async def admin_redirect():
    """管理员 - 重定向到 API 文档"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
