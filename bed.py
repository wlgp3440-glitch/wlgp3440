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

HTML = r'''<!DOCTYPE html>
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
        .header h1 { font-size: 32px; color: #fff; }
        .section { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section-title { font-size: 16px; color: #4a9eff; margin-bottom: 16px; font-weight: 600; }
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-size: 13px; color: #aaa; margin-bottom: 8px; }
        .input-group input, .input-group textarea { width: 100%; padding: 12px; background: #0f0f0f; border: 1px solid #333; border-radius: 4px; color: #e0e0e0; }
        .input-group textarea { min-height: 80px; }
        .upload-area { border: 2px dashed #333; border-radius: 8px; padding: 20px; text-align: center; cursor: pointer; }
        .images-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: 12px; }
        .image-item { background: #0f0f0f; border: 1px solid #333; border-radius: 8px; overflow: hidden; position: relative; }
        .image-item img { width: 100%; height: 150px; object-fit: cover; }
        .delete-btn { position: absolute; top: 4px; right: 4px; background: red; color: white; border: none; width: 24px; height: 24px; cursor: pointer; border-radius: 50%; }
        .btn { width: 100%; padding: 14px; background: #4a9eff; color: #0f0f0f; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-bottom: 8px; }
        .btn:hover { opacity: 0.9; }
        .btn-secondary { background: #333; color: #4a9eff; }
        .msg { padding: 12px; border-radius: 4px; margin-bottom: 12px; }
        .error { background: #4a1a1a; color: #ff9999; border: 1px solid #8a3a3a; }
        .success { background: #1a4a2a; color: #99ff99; border: 1px solid #3a8a5a; }
        .preview-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: 16px; }
        .preview-card { background: #0f0f0f; border: 1px solid #333; border-radius: 8px; overflow: hidden; cursor: pointer; }
        .preview-card img { width: 100%; height: 180px; object-fit: cover; }
        .preview-card.active { border: 2px solid #4a9eff; }
        .full-preview { background: #0f0f0f; padding: 20px; border: 1px solid #333; border-radius: 8px; margin-top: 20px; display: none; }
        .full-preview.show { display: block; }
        .full-preview img { width: 100%; max-width: 400px; margin-bottom: 16px; border-radius: 6px; }
        .results { display: none; }
        .results.show { display: block; }
        .download-btn { background: #51cf66; color: #000; }
        #fileInput { display: none; }
    </style>
</head>
<body>
<div class="container">
    <div class="header"><h1>카드뉴스 생성기</h1></div>
    <div class="section">
        <div class="section-title">Step 1: 이미지 업로드</div>
        <div id="msg"></div>
        <div class="upload-area" onclick="document.getElementById('fileInput').click()">클릭 또는 드래그</div>
        <input type="file" id="fileInput" multiple accept="image/*" onchange="handleFiles(event)">
        <div class="images-grid" id="imagesGrid"></div>
    </div>
    <div class="section">
        <div class="section-title">Step 2: 기사 링크</div>
        <div class="input-group">
            <label>링크</label>
            <input type="text" id="link" placeholder="https://news.naver.com/...">
        </div>
        <button class="btn btn-secondary" onclick="extractArticle()">기사 추출</button>
    </div>
    <div class="section">
        <div class="section-title">Step 3: 텍스트 편집</div>
        <div class="input-group">
            <label>제목</label>
            <textarea id="titleText"></textarea>
        </div>
        <div class="input-group">
            <label>내용 (5줄)</label>
            <textarea id="contentText"></textarea>
        </div>
        <button class="btn" onclick="generateCards()">카드 생성</button>
    </div>
    <div class="section results" id="results">
        <div class="section-title">완료!</div>
        <div class="preview-grid" id="previewGrid"></div>
        <div class="full-preview" id="fullPreview">
            <h3 id="previewTitle"></h3>
            <img id="previewImage">
            <p id="previewText"></p>
            <button class="btn download-btn" onclick="downloadAll()">모두 다운로드</button>
        </div>
    </div>
</div>
<script>
let uploadedImages = [];
let generatedCards = [];
function handleFiles(e) {
    const files = Array.from(e.target.files);
    if (uploadedImages.length + files.length > 5) {
        showMsg('최대 5개까지만', 'error');
        return;
    }
    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = event => {
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
            <button class="delete-btn" onclick="deleteImage(${i})">X</button>
        </div>
    `).join('');
}
function deleteImage(i) {
    uploadedImages.splice(i, 1);
    renderImages();
}
function showMsg(text, type) {
    const msgDiv = document.getElementById('msg');
    msgDiv.innerHTML = `<div class="msg ${type}">${text}</div>`;
    setTimeout(() => { msgDiv.innerHTML = ''; }, 5000);
}
async function extractArticle() {
    const link = document.getElementById('link').value;
    if (!link) { showMsg('링크를 입력하세요', 'error'); return; }
    try {
        const res = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({link})
        });
        const data = await res.json();
        if (!res.ok) { showMsg(data.error, 'error'); return; }
        document.getElementById('titleText').value = data.title;
        document.getElementById('contentText').value = data.content;
        showMsg('추출 완료!', 'success');
    } catch(e) {
        showMsg('오류: ' + e.message, 'error');
    }
}
function generateCards() {
    if (uploadedImages.length === 0) { showMsg('이미지를 업로드하세요', 'error'); return; }
    const title = document.getElementById('titleText').value;
    const contents = document.getElementById('contentText').value.split('\n').filter(x => x.trim());
    if (contents.length < 5) { showMsg('5줄을 입력하세요', 'error'); return; }
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
    showMsg('생성 완료!', 'success');
}
function selectCard(i) {
    const c = generatedCards[i];
    document.querySelectorAll('.preview-card').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.preview-card')[i].classList.add('active');
    document.getElementById('previewTitle').textContent = c.title;
    document.getElementById('previewImage').src = c.image;
    document.getElementById('previewText').textContent = c.text;
    document.getElementById('fullPreview').classList.add('show');
}
async function downloadAll() {
    for (let i = 0; i < generatedCards.length; i++) {
        const a = document.createElement('a');
        a.href = generatedCards[i].image;
        a.download = 'card-' + (i+1) + '.png';
        a.click();
        await new Promise(r => setTimeout(r, 300));
    }
}
</script>
</body>
</html>'''

def get_article(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.find(['h1', 'h2', 'title'])
        title = title.text.strip()[:100] if title else 'Title'
        paragraphs = soup.find_all('p')
        full_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
        sentences = [s.strip() for s in full_text.split('.') if s.strip()]
        summary = '\n'.join(sentences[:5])
        return title, summary
    except:
        return 'Article', '기사를 불러올 수 없습니다'

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    try:
        link = request.json.get('link')
        title, content = get_article(link)
        return jsonify({'title': title, 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
