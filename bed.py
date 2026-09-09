#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>카드뉴스 생성기 - 이미지 조합</title>
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
        .image-item { background: #0f0f0f; border: 1px solid #333; border-radius: 8px; overflow: hidden; position: relative; cursor: pointer; }
        .image-item img { width: 100%; height: 150px; object-fit: cover; }
        .image-item .delete-btn { position: absolute; top: 4px; right: 4px; background: rgba(255, 0, 0, 0.8); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 12px; }
        .image-item.selected { border: 2px solid #4a9eff; }
        
        .btn { width: 100%; padding: 14px; background: #4a9eff; color: #0f0f0f; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; }
        .btn:hover { opacity: 0.9; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-secondary { background: #333; color: #4a9eff; margin-bottom: 8px; }
        
        .error { background: #4a1a1a; color: #ff9999; padding: 12px; border-radius: 4px; margin-bottom: 12px; border: 1px solid #8a3a3a; }
        .success { background: #1a4a2a; color: #99ff99; padding: 12px; border-radius: 4px; margin-bottom: 12px; border: 1px solid #3a8a5a; }
        
        .preview-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: 16px; }
        .preview-card { background: #0f0f0f; border: 1px solid #333; border-radius: 8px; overflow: hidden; cursor: pointer; transition: all 0.2s; }
        .preview-card:hover { border-color: #4a9eff; }
        .preview-card img { width: 100%; height: 180px; object-fit: cover; }
        .preview-card.active { border: 2px solid #4a9eff; }
        
        .full-preview { background: #0f0f0f; padding: 20px; border: 1px solid #333; border-radius: 8px; margin-top: 20px; display: none; }
        .full-preview.show { display: block; }
        .full-preview img { width: 100%; max-width: 400px; margin-bottom: 16px; border-radius: 6px; }
        .full-preview textarea { width: 100%; min-height: 80px; padding: 12px; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; border-radius: 4px; }
        
        .results { display: none; }
        .results.show { display: block; }
        
        .download-btn { background: #51cf66; color: #000; }
        
        #fileInput { display: none; }
        
        @media (max-width: 900px) {
            .images-grid { grid-template-columns: repeat(2, 1fr); }
            .preview-grid { grid-template-columns: repeat(2, 1fr); }
        }
        
        @media (max-width: 600px) {
            .images-grid { grid-template-columns: 1fr; }
            .preview-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>🎨 카드뉴스 생성기</h1>
        <p>이미지 5개 + 기사 텍스트 조합으로 카드 생성</p>
    </div>
    
    <!-- 이미지 업로드 섹션 -->
    <div class="section">
        <div class="section-title">📷 Step 1: 이미지 업로드 (5개)</div>
        <div id="msg"></div>
        
        <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
            <p>📁 이미지를 클릭 또는 드래그해서 업로드</p>
            <small style="color: #666;">PNG, JPG (권장: 1080×1350 또는 1080×1920)</small>
        </div>
        <input type="file" id="fileInput" multiple accept="image/*" onchange="handleFiles(event)">
        
        <div class="images-grid" id="imagesGrid"></div>
    </div>
    
    <!-- 기사 정보 섹션 -->
    <div class="section">
        <div class="section-title">📰 Step 2: 기사 링크 입력</div>
        
        <div class="input-group">
            <label>🔗 기사 링크</label>
            <input type="text" id="link" placeholder="https://news.naver.com/... 또는 기타 뉴스 링크">
        </div>
        
        <button class="btn btn-secondary" onclick="extractArticle()">📄 기사 내용 추출</button>
    </div>
    
    <!-- 텍스트 편집 섹션 -->
    <div class="section">
        <div class="section-title">✏️ Step 3: 텍스트 편집</div>
        
        <div class="input-group">
            <label>제목</label>
            <textarea id="titleText" placeholder="카드 제목을 입력하세요"></textarea>
        </div>
        
        <div class="input-group">
            <label>내용 (5개 슬라이드)</label>
            <textarea id="contentText" placeholder="각 줄이 한 슬라이드의 텍스트가 됩니다&#10;&#10;줄1&#10;줄2&#10;줄3&#10;줄4&#10;줄5"></textarea>
            <small style="color: #666;">각 줄을 Enter로 구분 (5줄)</small>
        </div>
        
        <button class="btn" onclick="generateCards()">🎨 카드 생성하기</button>
    </div>
    
    <!-- 결과 섹션 -->
    <div class="section results" id="results">
        <div class="section-title">🎊 생성 완료!</div>
        
        <div class="preview-grid" id="previewGrid"></div>
        
        <div class="full-preview" id="fullPreview">
            <h3 id="previewTitle"></h3>
            <img id="previewImage">
            <p id="previewText"></p>
            <textarea id="editableText" readonly></textarea>
            <button class="btn download-btn" onclick="downloadAll()" style="margin-top: 12px;">⬇️ 모두 다운로드</button>
        </div>
    </div>
</div>

<script>
let uploadedImages = [];
let generatedCards = [];
let selectedCardIndex = 0;

// 드래그 앤 드롭
const uploadArea = document.getElementById('uploadArea');
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

uploadArea.addEventListener('dragover', () => uploadArea.classList.add('dragover'));
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
uploadArea.addEventListener('drop', (e) => {
    uploadArea.classList.remove('dragover');
    handleFiles({ target: { files: e.dataTransfer.files } });
});

function handleFiles(e) {
    const files = Array.from(e.target.files);
    if (uploadedImages.length + files.length > 5) {
        msg('최대 5개까지만 업로드 가능합니다');
        return;
    }
    
    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
            uploadedImages.push(event.target.result);
            renderImages();
        };
        reader.readAsDataURL(file);
    });
}

function renderImages() {
    document.getElementById('imagesGrid').innerHTML = uploadedImages.map((img, i) => `
        <div class="image-item">
            <img src="${img}">
            <button class="delete-btn" onclick="deleteImage(${i})">✕</button>
        </div>
    `).join('');
}

function deleteImage(i) {
    uploadedImages.splice(i, 1);
    renderImages();
}

function msg(text, type = 'error') {
    const msgDiv = document.getElementById('msg');
    msgDiv.innerHTML = `<div class="${type}">${text}</div>`;
    setTimeout(() => { msgDiv.innerHTML = ''; }, 5000);
}

async function extractArticle() {
    const link = document.getElementById('link').value;
    if (!link) {
        msg('링크를 입력해주세요');
        return;
    }
    
    try {
        const res = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link })
        });
        
        const data = await res.json();
        if (!res.ok) { msg(data.error); return; }
        
        document.getElementById('titleText').value = data.title;
        document.getElementById('contentText').value = data.content;
        msg('✅ 추출 완료!', 'success');
    } catch(e) {
        msg('오류: ' + e.message);
    }
}

function generateCards() {
    if (uploadedImages.length === 0) {
        msg('이미지를 먼저 업로드해주세요');
        return;
    }
    
    const title = document.getElementById('titleText').value;
    const contents = document.getElementById('contentText').value.split('\n').filter(x => x.trim());
    
    if (contents.length < 5) {
        msg('5개의 텍스트 줄을 입력해주세요');
        return;
    }
    
    generatedCards = uploadedImages.map((img, i) => ({
        image: img,
        title: title,
        text: contents[i] || ''
    }));
    
    document.getElementById('previewGrid').innerHTML = generatedCards.map((c, i) => `
        <div class="preview-card ${i === 0 ? 'active' : ''}" onclick="selectCard(${i})">
            <img src="${c.image}">
        </div>
    `).join('');
    
    document.getElementById('results').classList.add('show');
    selectCard(0);
    msg('✅ 카드 생성 완료!', 'success');
}

function selectCard(i) {
    selectedCardIndex = i;
    const c = generatedCards[i];
    
    document.querySelectorAll('.preview-card').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.preview-card')[i].classList.add('active');
    
    document.getElementById('previewTitle').textContent = c.title;
    document.getElementById('previewImage').src = c.image;
    document.getElementById('previewText').textContent = c.text;
    document.getElementById('editableText').value = c.text;
    document.getElementById('fullPreview').classList.add('show');
    
    // 텍스트 수정 가능하게
    document.getElementById('editableText').onchange = () => {
        generatedCards[i].text = document.getElementById('editableText').value;
    };
}

async function downloadAll() {
    for (let i = 0; i < generatedCards.length; i++) {
        const a = document.createElement('a');
        a.href = generatedCards[i].image;
        a.download = `card-${i+1}.png`;
        a.click();
        await new Promise(r => setTimeout(r, 300));
    }
}
</script>
</body>
</html>
'''

def get_article_content(url):
    """기사 링크에서 제목과 내용 추출"""
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 제목
        title_elem = soup.find(['h1', 'h2', 'title'])
        title = title_elem.text if title_elem else 'Title'
        title = title.strip()[:100]
        
        # 본문
        paragraphs = soup.find_all(['p', 'article', 'div'], class_=lambda x: x and 'content' in x.lower())
        if not paragraphs:
            paragraphs = soup.find_all('p')
        
        content = '\n'.join([p.text.strip() for p in paragraphs[:10] if p.text.strip()])
        content = content[:500]
        
        return title, content
    except Exception as e:
        return 'Article', f'기사를 불러올 수 없습니다: {str(e)}'

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/extract', methods=['POST'])
def extract():
    try:
        data = request.json
        link = data.get('link')
        
        title, content = get_article_content(link)
        
        # 내용을 5줄로 요약 (간단한 방식)
        sentences = content.split('.')
        lines = []
        for s in sentences:
            s = s.strip()
            if s:
                lines.append(s)
                if len(lines) >= 5:
                    break
        
        content_5lines = '\n'.join(lines[:5])
        
        return jsonify({'title': title, 'content': content_5lines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
