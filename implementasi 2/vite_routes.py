# vite_routes.py
from flask import Blueprint, send_from_directory, render_template
import os

vite_bp = Blueprint('vite_bp', __name__)

# Path ke folder hasil build Vite (biasanya "dist")
VITE_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'dist')

@vite_bp.route('/')
def serve_vite_index():
    """Serve file index.html hasil build Vite"""
    index_path = os.path.join(VITE_BUILD_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(VITE_BUILD_DIR, 'index.html')
    else:
        return "Vite build not found. Jalankan `npm run build` di folder frontend.", 404

@vite_bp.route('/assets/<path:filename>')
def serve_vite_assets(filename):
    """Serve asset JS/CSS hasil build Vite"""
    return send_from_directory(os.path.join(VITE_BUILD_DIR, 'assets'), filename)
