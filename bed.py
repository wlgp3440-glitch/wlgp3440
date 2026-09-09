def get_article(url):
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizer import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        title = soup.find(['h1', 'h2', 'title'])
        title = title.text.strip()[:100] if title else 'Title'
        
        paragraphs = soup.find_all('p')
        full_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
        
        if len(full_text) < 100:
            return title, full_text
        
        try:
            parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
            summarizer = LsaSummarizer()
            summary_sentences = summarizer(parser.document, sentences_count=5)
            summary = '\n'.join([str(s) for s in summary_sentences])
            return title, summary
        except:
            sentences = full_text.split('.')
            lines = [s.strip() for s in sentences if s.strip()][:5]
            return title, '\n'.join(lines)
    except:
        return 'Article', '기사를 불러올 수 없습니다'
