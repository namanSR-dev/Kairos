import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    # Force Windows to use the ProactorEventLoop which supports subprocesses (Playwright)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run the Uvicorn server (MUST explicitly set loop="asyncio" to prevent overrides)
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True, loop="asyncio")
