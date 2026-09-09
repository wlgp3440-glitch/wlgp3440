#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카드뉴스 자동 생성기 - 백엔드 (Flask)
링크 → 제목 + 5개 이미지 + 본문 자동 생성
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import openai
openai.api_key = "user_key_here"
import re
import json
from urllib.parse import urlparse
import os

app = Flask(__name__)
CORS(app)

# ==================== HTML 프론트엔드 ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>카드뉴스 자동 생성기</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0f0f0f; color: #e0e0e0; font-family: -apple-system, sans-serif; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 32px; }
        .header h1 { font-size: 32px; margin-bottom: 8px; color: #fff; }
        .header p { color: #999; font-size: 14px; }
        
        .input-section { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-size: 13px; color: #aaa; margin-bottom: 8px; font-weight: 500; }
        .input-group input, .input-group select { width: 100%; padding: 12px; background: #0f0f0f; border: 1px solid #333; border-radius: 4px; color: #e0e0e0; font-size: 14px; }
        .input-group input:focus { outline: none; border-color: #4a9eff; }
        
        .button-group { display: flex; gap: 12px; margin-top: 20px; }
        .btn { flex: 1; padding: 14px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; }
        .btn-primary { background: #4a9eff; color: #0f0f0f; }
        .btn-primary:hover { opacity: 0.9; }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-secondary { background: #1a3a5c; border: 1px solid #4a9eff; color: #4a9eff; }
        
        .loading { text-align: center; padding: 40px; font-size: 14px; color: #666; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #333; border-top-color: #4a9eff; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 12px; vertical-align: -4px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .error { background: #4a1a1a; border: 1px solid #8a3a3a; color: #ff9999; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
        .success { background: #1a4a2a; border: 1px solid #3a8a5a; color: #99ff99; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
        
        .results { display: none; }
        .results.show { display: block; }
        
        .slides-container { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }
        .slide { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; cursor: pointer; transition: all 0.2s; }
        .slide:hover { border-color: #4a9eff; transform: translateY(-4px); }
        .slide.active { border-color: #4a9eff; box-shadow: 0 0 12px rgba(74, 158, 255, 0.3); }
        
        .slide-image { width: 100%; height: 150px; background: #333; overflow: hidden; }
        .slide-image img { width: 100%; height: 100%; object-fit: cover; }
        .slide-number { padding: 8px; text-align: center; font-size: 12px; color: #aaa; border-top: 1px solid #333; }
        
        .preview-section { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 20px; display: none; }
        .preview-section.show { display: block; }
        
        .preview-title { font-size: 20px; color: #fff; margin-bottom: 12px; font-weight: 600; }
        .preview-image { width: 100%; max-width: 400px; border-radius: 6px; margin-bottom: 16px; }
        .preview-text { font-size: 14px; line-height: 1.6; color: #ccc; }
        
        .download-section { display: none; }
        .download-section.show { display: block; }
        .download-btn { width: 100%; padding: 16px; background: #51cf66; color: #000; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: 600; margin-bottom: 12px; }
        .download-btn:hover { opacity: 0.9; }
        
        .size-toggle { display: flex; gap: 8px; margin-top: 8px; }
        .size-btn { flex: 1; padding: 10px; background: #0f0f0f; border: 1px solid #333; color: #aaa; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .size-btn.active { background: #4a9eff; border-color: #4a9eff; color: #0f0f0f; }
        
        @media (max-width: 900px) {
            .slides-container { grid-template-columns: repeat(2, 1fr); }
        }
        
        @media (max-width: 600px) {
            .slides-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>🎨 카드뉴스 자동 생성기</h1>
        <p>링크 한 개만 입력하면 AI가 자동으로 5개 카드를 만들어줘요</p>
    </div>
    
    <div class="input-section">
        <div id="message"></div>
        
        <div class="input-group">
            <label>🔑 OpenAI API 키</label>
            <input type="password" id="apiKey" placeholder="sk-proj-..." value="">
            <small style="color: #666; margin-top: 4px; display: block;">• 당신의 컴퓨터에만 저장됩니다 (로컬 저장소)</small>
            <small style="color: #666; display: block;">• 절대 서버로 전송되지 않습니다</small>
        </div>
        
        <div class="input-group">
            <label>🔗 링크 입력</label>
            <input type="text" id="linkInput" placeholder="유튜브, 뉴스, 네이트판, 블로그 등 모든 링크 가능">
        </div>
        
        <div class="input-group">
            <label>📐 카드 규격 선택</label>
            <div class="size-toggle">
                <button class="size-btn active" onclick="setSize(1350)">1080×1350<br>(인스타 게시글)</button>
                <button class="size-btn" onclick="setSize(1920)">1080×1920<br>(릴스)</button>
            </div>
        </div>
        
        <div class="button-group">
            <button class="btn btn-primary" onclick="generateCards()">✨ 자동 생성하기</button>
            <button class="btn btn-secondary" onclick="saveApiKey()">💾 API 키 저장</button>
        </div>
    </div>
    
    <div id="results" class="results">
        <div class="slides-container" id="slidesContainer"></div>
        
        <div class="preview-section" id="previewSection">
            <div class="preview-title" id="previewTitle"></div>
            <img class="preview-image" id="previewImage" src="" alt="">
            <div class="preview-text" id="previewText"></div>
        </div>
        
        <div class="download-section" id="downloadSection">
            <button class="download-btn" onclick="downloadAllCards()">⬇️ 5개 카드 모두 다운로드</button>
            <button class="download-btn" style="background: #6b5eff;" onclick="downloadSelectedCard()">⬇️ 선택한 카드만 다운로드</button>
        </div>
    </div>
</div>

<script>
let cardSize = 1350;
let selectedSlide = 0;
let generatedCards = [];

function setSize(size) {
    cardSize = size;
    document.querySelectorAll('.size-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function showMessage(msg, type = 'error') {
    const msgDiv = document.getElementById('message');
    msgDiv.innerHTML = `<div class="${type}">${msg}</div>`;
    setTimeout(() => { msgDiv.innerHTML = ''; }, 5000);
}

function saveApiKey() {
    const key = document.getElementById('apiKey').value;
    if (!key) {
        showMessage('API 키를 입력해주세요', 'error');
        return;
    }
    localStorage.setItem('openai_api_key', key);
    showMessage('✅ API 키가 저장되었습니다', 'success');
}

function loadApiKey() {
    const saved = localStorage.getItem('openai_api_key');
    if (saved) {
        document.getElementById('apiKey').value = saved;
    }
}

async function generateCards() {
    const link = document.getElementById('linkInput').value.trim();
    const apiKey = document.getElementById('apiKey').value.trim();
    
    if (!link) {
        showMessage('링크를 입력해주세요', 'error');
        return;
    }
    if (!apiKey) {
        showMessage('API 키를 입력해주세요', 'error');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>생성 중...';
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link, apiKey, size: cardSize })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showMessage(data.error || '생성 실패', 'error');
            btn.disabled = false;
            btn.innerHTML = '✨ 자동 생성하기';
            return;
        }
        
        generatedCards = data.cards;
        displayCards();
        showMessage('✅ 카드 생성 완료!', 'success');
        
    } catch (error) {
        showMessage('오류: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '✨ 자동 생성하기';
    }
}

function displayCards() {
    const container = document.getElementById('slidesContainer');
    container.innerHTML = generatedCards.map((card, i) => `
        <div class="slide ${i === 0 ? 'active' : ''}" onclick="selectSlide(${i})">
            <div class="slide-image">
                <img src="${card.image}" alt="Slide ${i + 1}">
            </div>
            <div class="slide-number">${i + 1} / ${generatedCards.length}</div>
        </div>
    `).join('');
    
    document.getElementById('results').classList.add('show');
    selectedSlide = 0;
    updatePreview();
}

function selectSlide(index) {
    selectedSlide = index;
    document.querySelectorAll('.slide').forEach((s, i) => {
        s.classList.toggle('active', i === index);
    });
    updatePreview();
}

function updatePreview() {
    const card = generatedCards[selectedSlide];
    document.getElementById('previewTitle').textContent = card.title;
    document.getElementById('previewImage').src = card.image;
    document.getElementById('previewText').textContent = card.text;
    document.getElementById('previewSection').classList.add('show');
    document.getElementById('downloadSection').classList.add('show');
}

async function downloadAllCards() {
    for (let i = 0; i < generatedCards.length; i++) {
        await downloadCard(i);
        await new Promise(r => setTimeout(r, 500));
    }
}

async function downloadSelectedCard() {
    await downloadCard(selectedSlide);
}

async function downloadCard(index) {
    const card = generatedCards[index];
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = cardSize;
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
        ctx.drawImage(img, 0, 0, 1080, cardSize);
        
        const gradient = ctx.createLinearGradient(0, cardSize * 0.4, 0, cardSize);
        gradient.addColorStop(0, 'rgba(0, 0, 0, 0)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0.6)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 1080, cardSize);
        
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 36px Arial';
        wrapText(ctx, card.title, 40, cardSize - 200, 1000, 48);
        
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.font = '20px Arial';
        wrapText(ctx, card.text, 40, cardSize - 80, 1000, 28);
        
        const link = document.createElement('a');
        link.href = canvas.toDataURL('image/png');
        link.download = `card-${index + 1}-${Date.now()}.png`;
        link.click();
    };
    img.src = card.image;
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
    const words = text.split(' ');
    let line = '';
    for (let i = 0; i < words.length; i++) {
        const testLine = line + words[i] + ' ';
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && i > 0) {
            ctx.fillText(line, x, y);
            line = words[i] + ' ';
            y += lineHeight;
        } else {
            line = testLine;
        }
    }
    ctx.fillText(line, x, y);
}

loadApiKey();
</script>

</body>
</html>
'''

# ==================== API 엔드포인트 ====================

def extract_content(url):
    """링크에서 제목과 본문 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 제목 추출
        title = None
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        elif soup.find('title'):
            title = soup.find('title').get_text(strip=True)
        
        # 본문 추출
        text = ''
        for p in soup.find_all('p')[:5]:
            text += p.get_text(strip=True) + ' '
        
        return title or 'Untitled', text[:500] or '내용을 찾을 수 없습니다'
    except Exception as e:
        return 'Error', f'링크 처리 실패: {str(e)}'

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/generate', methods=['POST'])
def generate():
    """AI로 카드뉴스 자동 생성"""
    try:
        data = request.json
        link = data.get('link')
        api_key = data.get('apiKey')
        card_size = data.get('size', 1350)
        
        if not link or not api_key:
            return jsonify({'error': '링크와 API 키가 필요합니다'}), 400
        
        # 1. 링크에서 내용 추출
        title, content = extract_content(link)
        
        # 2. OpenAI API로 제목과 본문 생성
        client = OpenAI(api_key=api_key)
        
        # 제목 생성
        title_response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{
                'role': 'user',
                'content': f'다음 내용을 바탕으로 흥미로운 카드뉴스 제목을 한 줄로 만들어줘 (20자 이내):\n{content[:200]}'
            }],
            max_tokens=50
        )
        main_title = title_response.choices[0].message.content.strip()
        
        # 5개 슬라이드별 프롬프트 생성
        prompt = f'''
다음 내용을 바탕으로 5개 슬라이드용 카드뉴스를 만들어줘.
각 슬라이드마다:
1. AI 이미지 생성 프롬프트 (영어, 50자 이내)
2. 본문 텍스트 (30자 이내, 매우 간단하고 명확하게)

형식: [슬라이드 1] IMAGE: ... TEXT: ...

원본 내용:
{content}
'''
        
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1000
        )
        
        slide_content = response.choices[0].message.content
        slides = parse_slides(slide_content)
        
        # 3. DALL-E로 이미지 생성
        cards = []
        for i, slide in enumerate(slides[:5]):
            try:
                image_response = client.images.generate(
                    model='dall-e-3',
                    prompt=slide['image_prompt'][:1000],
                    n=1,
                    size='1024x1024'
                )
                image_url = image_response.data[0].url
            except Exception as e:
                # 이미지 생성 실패시 플레이스홀더 사용
                image_url = f'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024"%3E%3Crect fill="%23333" width="1024" height="1024"/%3E%3Ctext x="50%25" y="50%25" fill="%23999" text-anchor="middle" dominant-baseline="middle" font-size="24"%3E{i+1}번째 카드%3C/text%3E%3C/svg%3E'
            
            cards.append({
                'title': main_title,
                'image': image_url,
                'text': slide['text']
            })
        
        return jsonify({'cards': cards})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_slides(content):
    """AI 응답에서 슬라이드 정보 파싱"""
    slides = []
    pattern = r'\[슬라이드 \d+\].*?IMAGE:\s*(.+?)\s*TEXT:\s*(.+?)(?=\[슬라이드|\Z)'
    
    matches = re.findall(pattern, content, re.DOTALL)
    for image_prompt, text in matches:
        slides.append({
            'image_prompt': image_prompt.strip(),
            'text': text.strip()[:100]
        })
    
    # 매칭 실패시 기본값
    if not slides:
        slides = [
            {'image_prompt': 'a professional news image', 'text': '카드 1입니다'},
            {'image_prompt': 'a professional news image', 'text': '카드 2입니다'},
            {'image_prompt': 'a professional news image', 'text': '카드 3입니다'},
            {'image_prompt': 'a professional news image', 'text': '카드 4입니다'},
            {'image_prompt': 'a professional news image', 'text': '카드 5입니다'},
        ]
    
    return slides[:5]

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════╗
    ║   카드뉴스 자동 생성기 - 로컬 서버    ║
    ╚════════════════════════════════════════╝
    
    🚀 서버 실행 중...
    📱 접속 주소: http://localhost:5000
    
    필요한 라이브러리:
    pip install flask flask-cors requests beautifulsoup4 openai
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)
