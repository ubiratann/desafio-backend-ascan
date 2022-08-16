import os
from app import app

if __name__ == "__main__":
    
    HOST        = os.environ.get("APPLICATION_HOST", "localhost")
    PORT        = int(os.environ.get("APPLICATION_PORT", "5000"))
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "DEV")

    if(ENVIRONMENT == "DEV"):
        app.debug = True

    app.run(HOST, PORT)
    