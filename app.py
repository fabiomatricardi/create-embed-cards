# app.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import signal
from flask import Flask, render_template, request, jsonify
import re
# for pyinstaller
import webbrowser
import threading
import time

app = Flask(__name__)

# for pyinstaller
def open_browser():
    time.sleep(1)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:5000")

def is_medium_url(url):
    return urlparse(url).netloc.endswith('medium.com')

def extract_meta(url, custom_image=None):
    """Fetch metadata; use custom_image if provided and URL is Medium."""
    fallback = {
        'url': url,
        'title': url,
        'description': '',
        'image': custom_image or '',
        'site_name': urlparse(url).netloc
    }

    # If it's Medium and we have a custom image, skip fetching
    if is_medium_url(url) and custom_image:
        return {**fallback, 'description': 'Manually added preview.'}

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        def get_meta(*names):
            for name in names:
                tag = soup.find('meta', property=name) or soup.find('meta', attrs={'name': name})
                if tag and tag.get('content'):
                    return tag['content']
            return ''

        title = get_meta('og:title', 'twitter:title', 'title') or (soup.title.string if soup.title else '')
        description = get_meta('og:description', 'twitter:description', 'description')
        image = get_meta('og:image', 'twitter:image')
        site_name = get_meta('og:site_name', 'twitter:site')

        if image and not image.startswith(('http://', 'https://')):
            image = urljoin(url, image)

        result = {
            'url': url,
            'title': title.strip() if title else url,
            'description': description.strip() if description else '',
            'image': image or custom_image or '',
            'site_name': site_name.strip() if site_name else urlparse(url).netloc
        }
        return result

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        fallback['description'] = 'Preview unavailable.'
        if is_medium_url(url) and custom_image:
            fallback['description'] = 'Manually added preview.'
        return fallback

@app.route('/', methods=['GET', 'POST'])
def index():
    cards = []
    input_text = ""
    if request.method == 'POST':
        raw_input = request.form.get('urls', '').strip()
        input_text = raw_input
        lines = [line.strip() for line in raw_input.splitlines() if line.strip()]
        
        urls_with_images = []
        i = 0
        while i < len(lines):
            url_line = lines[i]
            if re.match(r'https?://', url_line):
                url = url_line
                custom_image = None
                # Check next line for !image
                if i + 1 < len(lines) and lines[i + 1].startswith('!image '):
                    custom_image = lines[i + 1].replace('!image ', '').strip()
                    i += 2  # skip image line
                else:
                    i += 1
                urls_with_images.append((url, custom_image))
            else:
                i += 1  # skip non-URL lines

        cards = [extract_meta(url, img) for url, img in urls_with_images]
    return render_template('index.html', input_text=input_text, cards=cards)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Force-kill the current process (works in PyInstaller)."""
    os._exit(0)  # Immediate exit, no cleanup needed for local apps

if __name__ == '__main__':
    # Only open browser if not in reloader (avoid double launch in debug)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)