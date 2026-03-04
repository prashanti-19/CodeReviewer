"""
Entry point for Hugging Face Spaces deployment.
Hugging Face Spaces expects the app on port 7860.
"""
import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
