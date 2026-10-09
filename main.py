import os
import sys
import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if "raahi" not in sys.modules:
    raahi_pkg = types.ModuleType("raahi")
    raahi_pkg.__path__ = [BASE_DIR]
    sys.modules["raahi"] = raahi_pkg

from api.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
