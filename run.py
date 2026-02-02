# run.py
import uvicorn
import os

if __name__ == "__main__":
    # Get port from env (Render uses PORT) or default to 8000
    port = int(os.environ.get("PORT", 8000))
    #uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)