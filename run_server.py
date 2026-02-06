"""启动 FastAPI 服务器"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("AutoCut Director - Starting Server")
    print("=" * 60)
    print("\nServer: http://localhost:8787")
    print("API Docs: http://localhost:8787/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8787,
        reload=True,
        log_level="info"
    )
