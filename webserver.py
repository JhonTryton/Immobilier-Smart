from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "SmartImmoBot is running."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render utilisera automatiquement cette variable
    app.run(host='0.0.0.0', port=port)
  
