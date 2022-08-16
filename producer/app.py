import os
import api.router.subscription as subscription

from flask import Flask

app = Flask(__name__)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "DEV")

if(ENVIRONMENT == "DEV"):
    app.config.from_pyfile("config.py")

version = os.environ.get("API_VERSION", "v1")

app.register_blueprint(subscription.blueprint, url_prefix=f"/api/{version}/subscriptions")