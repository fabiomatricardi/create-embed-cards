# app.py
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from flask import Flask, render_template, request
import threading
import time
import webbrowser

app = Flask(__name__)

def extract_meta(url, custom_title=None, custom_desc=None, custom_image=None):
    """Fetch metadata only if needed; always respect manual overrides."""
    # Always use manual values if provided
    final_title = custom_title or url
    final_desc = custom_desc or ''
    final_image = custom_image
    final_site_name = urlparse(url).netloc

    # Should we fetch the page? Only if at least one field is missing.
    should_fetch = not (custom_title and custom_desc and custom_image)

    if should_fetch:
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

            # Title: use custom or fetch
            if not custom_title:
                og_title = get_meta('og:title', 'twitter:title', 'title')
                final_title = og_title or (soup.title.string if soup.title else url)

            # Description: use custom or fetch
            if not custom_desc:
                final_desc = get_meta('og:description', 'twitter:description', 'description') or ''

            # Image: use custom or fetch
            if not custom_image:
                image = get_meta('og:image', 'twitter:image')
                if image and not image.startswith(('http://', 'https://')):
                    image = urljoin(url, image)
                final_image = image

            # Site name (only from fetch)
            site_name = get_meta('og:site_name', 'twitter:site')
            final_site_name = site_name.strip() if site_name else urlparse(url).netloc

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            if not custom_desc:
                final_desc = 'Preview unavailable.'
            if custom_title or custom_desc or custom_image:
                final_desc = 'Partially manually added preview.'

    else:
        # Fully manual — no network call
        final_desc = final_desc or 'Manually added preview.'

    return {
        'url': url,
        'title': str(final_title).strip(),
        'description': str(final_desc).strip(),
        'image': final_image or '',
        'site_name': final_site_name
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    cards = []
    input_text = ""
    if request.method == 'POST':
        raw_input = request.form.get('urls', '').strip()
        input_text = raw_input
        lines = [line.strip() for line in raw_input.splitlines()]
        
        urls_with_meta = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.match(r'https?://', line):
                url = line
                custom_title = None
                custom_desc = None
                custom_image = None

                # Parse subsequent directive lines (!title, !desc, !image)
                j = i + 1
                while j < len(lines) and lines[j].startswith('!'):
                    directive = lines[j]
                    if directive.startswith('!title '):
                        custom_title = directive[len('!title '):].strip()
                    elif directive.startswith('!desc '):
                        custom_desc = directive[len('!desc '):].strip()
                    elif directive.startswith('!image '):
                        custom_image = directive[len('!image '):].strip()
                    else:
                        break  # unknown directive — stop parsing
                    j += 1

                urls_with_meta.append((url, custom_title, custom_desc, custom_image))
                i = j  # skip processed lines
            else:
                i += 1  # skip non-URL lines

        cards = [
            extract_meta(url, title, desc, img)
            for url, title, desc, img in urls_with_meta
        ]
    return render_template('index.html', input_text=input_text, cards=cards)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Terminate the application process immediately."""
    os._exit(0)

# Auto-open browser on startup
def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)