#!/usr/bin/env python3
"""
Start the API Gateway service from the project root.
This ensures proper Python path resolution.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to the project root directory
os.chdir(project_root)

# Import and run the API Gateway
if __name__ == "__main__":
    import uvicorn
    from services.api_gateway.main import app
    
    print("Starting API Gateway on http://localhost:8000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
