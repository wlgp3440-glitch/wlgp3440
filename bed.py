def get_article(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        title = soup.find(['h1', 'h2', 'title'])
        title = title.text.strip()[:100] if title else 'Title'
        
        paragraphs = soup.find_all('p')
        full_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
        
        # 문장을 . 로 분리해서 5줄로 만들기
        sentences = [s.strip() for s in full_text.split('.') if s.strip()]
        summary_lines = sentences[:5]
        summary = '\n'.join(summary_lines)
        
        return title, summary
    except:
        return 'Article', '기사를 불러올 수 없습니다'
