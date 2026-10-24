"""Run with: python run.py (after installing requirements.txt)."""
import os
from server import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')), debug=False)

