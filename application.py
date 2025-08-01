# Elastic Beanstalk expects application.py with 'application' variable
import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from api_server import app as application
except ImportError as e:
    print(f"Import error: {e}")
    # Create a simple test app if import fails
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def hello():
        return "Hello! Import failed, but app is running."
    
    @application.route('/health')
    def health():
        return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    application.run(debug=False, host='0.0.0.0', port=port) 