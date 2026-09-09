#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

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
        .header h1 { font-size: 32px; color: #fff; }
        .input-section { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-size: 13px; color: #aaa; margin-bottom: 8px; }
        .input-group input { width: 100%; padding: 12px; background: #0f0f0f; border: 1px solid #333; border-radius: 4px; color: #e0e0e0; }
        .btn { width: 100%; padding: 14px; background: #4a9eff; color: #0f0f0f; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-bottom: 8px; }
        .btn:disabled { opacity: 0.5; }
        .error { background: #4a1a1a; color: #ff9999; padding: 12px; margin-bottom: 12px; border-radius: 4px; }
        .success { background: #1a4a2a; color: #99ff99; padding: 12px; margin-bottom: 12px; border-radius: 4px; }
        .slides { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }
        .slide { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; cursor: pointer; }
        .slide img { width: 100%; height: 150px; object-fit: cover; }
        .slide-num { padding: 8px; text-align: center; font-size: 12px; }
        .preview { background: #1a1a1a; padding: 20px; border-radius: 8px; display: none; margin-bottom: 20px; }
        .preview.show { display: block; }
        .preview-img { width: 100%; max-width: 400px; margin: 12px 0; border-radius: 6px; }
        .download-btn { width: 100%; padding: 14px; background: #51cf66; color: #000; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-bottom: 8px; }
        .results { display: none; }
        .results.show { display: block; }
        @media (max-width: 900px) { .slides { grid-template-columns: repeat(2, 1fr); } }
    </style>
</head>
<body>
<div class="container">
    <div class="header"><h1>🎨 카드뉴스 자동 생성기</h1></div>
    <div class="input-section">
        <div id="msg"></div>
        <div class="input-group">
            <label>🔑 OpenAI API 키</label>
            <input type="password" id="apiKey" placeholder="sk-...">
        </div>
        <div class="input-group">
            <label>🔗 링크 (YouTube, 뉴스, 블로그 등)</label>
            <input type="text" id="link" placeholder="https://...">
        </div>
        <button class="btn" onclick="generate()">✨ 생성하기</button>
    </div>
    <div id="results" class="results">
        <div class="slides" id="slides"></div>
        <div class="preview" id="preview">
            <h2 id="previewTitle"></h2>
            <img class="preview-img" id="previewImage">
            <p id="previewText"></p>
        </div>
        <button class="download-btn" onclick="downloadAll()">⬇️ 모두 다운로드</button>
    </div>
</div>
<script>
let cards = [];
let selected = 0;

function msg(text, type = 'error') {
    document.getElementById('msg').innerHTML = `<div class="${type}">${text}</div>`;
}

async function generate() {
    const link = document.getElementById('link').value;
    const key = document.getElementById('apiKey').value;
    if (!link || !key) { msg('입력해주세요'); return; }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '⏳ 생성 중...';
    
    try {
        const res = await fetch('/api/gen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link, key })
        });
        const data = await res.json();
        if (!res.ok) { msg(data.error); btn.disabled = false; btn.innerHTML = '✨ 생성하기'; return; }
        
        cards = data.cards;
        document.getElementById('slides').innerHTML = cards.map((c, i) => 
            `<div class="slide" onclick="select(${i})"><img src="${c.image}"><div class="slide-num">${i+1}/5</div></div>`
        ).join('');
        document.getElementById('results').classList.add('show');
        select(0);
        msg('✅ 완료!', 'success');
    } catch(e) { msg(e.message); }
    finally { btn.disabled = false; btn.innerHTML = '✨ 생성하기'; }
}

function select(i) {
    selected = i;
    const c = cards[i];
    document.getElementById('previewTitle').textContent = c.title;
    document.getElementById('previewImage').src = c.image;
    document.getElementById('previewText').textContent = c.text;
    document.getElementById('preview').classList.add('show');
}

async function downloadAll() {
    for (let i = 0; i < cards.length; i++) {
        const a = document.createElement('a');
        a.href = cards[i].image;
        a.download = `card-${i+1}.png`;
        a.click();
        await new Promise(r => setTimeout(r, 300));
    }
}
</script>
</body>
</html>
'''

def get_content(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.find('h1')
        title = title.text if title else 'Title'
        text = ' '.join([p.text for p in soup.find_all('p')[:5]])
        return title[:100], text[:500]
    except:
        return 'Content', 'Unable to fetch'

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/gen', methods=['POST'])
def gen():
    try:
        data = request.json
        link = data.get('link')
        key = data.get('key')
        
        title, content = get_content(link)
        
        # GPT 제목 생성
        headers = {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4o-mini',
            'messages': [{'role': 'user', 'content': f'제목을 20자 이내로: {content[:200]}'}],
            'max_tokens': 50
        }
        
        res = requests.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers, timeout=30)
        if res.status_code != 200:
            return jsonify({'error': res.json().get('error', {}).get('message', 'API 오류')}), 400
        
        main_title = res.json()['choices'][0]['message']['content'].strip()
        
        # 슬라이드 생성
        payload['messages'] = [{'role': 'user', 'content': f'5개 슬라이드 [슬라이드 1] IMAGE: ... TEXT: ... 형식:\n{content[:1000]}'}]
        payload['max_tokens'] = 1000
        
        res = requests.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers, timeout=30)
        slides_text = res.json()['choices'][0]['message']['content']
        
        slides = []
        pattern = r'\[슬라이드 \d+\].*?IMAGE:\s*(.+?)\s*TEXT:\s*(.+?)(?=\[슬라이드|$)'
        matches = re.findall(pattern, slides_text, re.DOTALL)
        
        for img_prompt, txt in matches[:5]:
            slides.append({'image_prompt': img_prompt.strip()[:100], 'text': txt.strip()[:100]})
        
        while len(slides) < 5:
            slides.append({'image_prompt': 'professional image', 'text': f'슬라이드 {len(slides)+1}'})
        
        # DALL-E 이미지
        cards = []
        for slide in slides[:5]:
            try:
                img_payload = {
                    'model': 'dall-e-3',
                    'prompt': slide['image_prompt'],
                    'n': 1,
                    'size': '1024x1024'
                }
                img_res = requests.post('https://api.openai.com/v1/images/generations', json=img_payload, headers=headers, timeout=30)
                img_url = img_res.json()['data'][0]['url']
            except:
                img_url = 'data:image/svg+xml,%3Csvg%3E%3Crect fill="%23333"%3E%3C/svg%3E'
            
            cards.append({'title': main_title, 'image': img_url, 'text': slide['text']})
        
        return jsonify({'cards': cards})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
