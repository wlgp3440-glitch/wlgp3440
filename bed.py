#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>카드뉴스 생성기</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0f0f0f; color: #e0e0e0; font-family: -apple-system, sans-serif; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 32px; }
        .header h1 { font-size: 32px; color: #fff; margin-bottom: 8px; }
        .header p { color: #999; font-size: 14px; }
        
        .section { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section-title { font-size: 16px; color: #4a9eff; margin-bottom: 16px; font-weight: 600; }
        
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-size: 13px; color: #aaa; margin-bottom: 8px; font-weight: 500; }
        .input-group input, .input-group textarea { width: 100%; padding: 12px; background: #0f0f0f; border: 1px solid #333; border-radius: 4px; color: #e0e0e0; }
        .input-group textarea { resize: vertical; min-height: 80px; }
        .input-group input:focus, .input-group textarea:focus { outline: none; border-color: #4a9eff; }
        
        .upload-area { border: 2px dashed #333; border-radius: 8px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .upload-area:hover { border-color: #4a9eff; background: rgba(74, 158, 255, 0.05); }
        .upload-area.dragover { border-color: #4a9eff; background: rgba(74, 158, 255, 0.1); }
        
        .images-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: 12px; }
        .image-item { background: #0f0f0f; border: 1px solid #333; border-radius: 8px; overflow: hidden; position: relative; }
        .image-item img { width: 100%; height: 150px; object-fit: cover; }
        .image-item .delete-btn { position: absolute; top: 4px; right: 4px; background: rgba(255, 0, 0, 0.8); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; }
        
        .btn { width: 100%; padding: 14px; background: #4a9eff; color: #0f0f0f; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s; margin-bottom: 8px; }
        .btn:hover { opacity: 0.9; }
