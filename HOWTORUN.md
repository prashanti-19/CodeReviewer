Every Time You Want to Use the Program:
Step 1: Open PowerShell
    Search for PowerShell in your Windows start menu

Step 2: Navigate to the backend
    bashcd C:\..\backend\backend

Step 3: Start the backend
    bashpy -m uvicorn main:app --host 0.0.0.0 --port 8000

You should see:
    Application startup complete.
    Uvicorn running on http://0.0.0.0:8000

Step 4: Open a second PowerShell window
    Keep the first one open — don't close it!

Step 5: Navigate to the frontend
    bashcd C:\..\frontend

Step 6: Start the frontend
    bashnpm run dev

Step 7: Open your browser
    Go to http://localhost:5173

To Stop the App
    Press Ctrl+C in both PowerShell windows