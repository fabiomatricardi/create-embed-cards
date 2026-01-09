# create-embed-cards
python flask app to create Embedd Cards from urls


<img src='https://github.com/fabiomatricardi/create-embed-cards/raw/main/banner.png' width=500>   <img src='https://github.com/fabiomatricardi/create-embed-cards/raw/main/banner2.png' width=500>

A Python web app that:

1. Lets you input one or more URLs (e.g., Substack, Medium, or any Open Graph–enabled page).
2. Fetches their **Open Graph (OG)** or fallback metadata (title, description, image).
3. Renders beautiful, clickable **embed cards** using clean, professional CSS.
4. Runs locally via a simple web server (using Flask).

---

### ✅ Tech Stack
- **Backend**: Python + Flask (lightweight web framework)
- **Frontend**: HTML + CSS (no JS required, but we’ll keep it clean and responsive)
- **Metadata fetching**: Requests + BeautifulSoup (to parse OG tags)


---

### 🛠️ Step 1: Install Dependencies

Run this in your terminal:

```bash
pip install flask requests beautifulsoup4 pyinstaller
```

---

### 📄 Step 2: Create `app.py`

```python
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
```

---

### 📁 Step 3: Create Templates Folder & HTML

Create a folder called `templates` and inside it, create `index.html`:

```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Link Preview Generator</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f9fafb;
            color: #111;
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 1.5rem;
            color: #2d3748;
        }
        .instructions {
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem 1.25rem;
            border-radius: 0 6px 6px 0;
            margin-bottom: 1.5rem;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .instructions h2 {
            margin-top: 0;
            color: #1e40af;
            font-size: 1.1rem;
        }
        .instructions p {
            margin: 0.75rem 0;
        }
        .instructions code {
            background: #dbeafe;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .instructions pre {
            background: #dbeafe;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 0.75rem 0;
        }
        .instructions ul {
            padding-left: 1.25rem;
            margin: 0.5rem 0;
        }
        .instructions li {
            margin-bottom: 0.25rem;
        }
        textarea {
            width: 100%;
            height: 100px;
            padding: 0.75rem;
            font-size: 1rem;
            border: 1px solid #cbd5e0;
            border-radius: 6px;
            margin-bottom: 1rem;
            resize: vertical;
            font-family: monospace;
        }
        button {
            background-color: #4f46e5;
            color: white;
            border: none;
            padding: 0.5rem 1.25rem;
            font-size: 1rem;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #4338ca;
        }
        .cards {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            margin-top: 2rem;
        }
        .card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.12);
        }
        .card-image {
            width: 100%;
            height: 160px;
            object-fit: cover;
            background-color: #edf2f7;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #a0aec0;
            font-size: 0.875rem;
        }
        .card-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .card-content {
            padding: 1rem;
        }
        .card-site {
            font-size: 0.75rem;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.25rem;
        }
        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            line-height: 1.4;
            color: #2d3748;
        }
        .card-desc {
            font-size: 0.95rem;
            color: #4a5568;
            line-height: 1.5;
            margin: 0;
        }
    </style>
</head>
<body>
    <h1>🔗 Link Preview Generator</h1>
    <div style="text-align: center; margin-top: 2rem; margin-bottom: 1rem;">
        <button onclick="shutdownApp()" style="
            background-color: #ef4444;
            color: white;
            border: none;
            padding: 0.4rem 1rem;
            font-size: 0.9rem;
            border-radius: 6px;
            cursor: pointer;
        ">⏹️ Quit App</button>
    </div>
    <br>
    <script>
    function shutdownApp() {
        if (confirm("Are you sure you want to quit the app?")) {
            fetch('/shutdown', { method: 'POST' })
                .then(() => {
                    document.body.innerHTML = '<div style="text-align:center; margin-top:3rem; font-family:sans-serif; color:#4a5568;"><h2>App is shutting down...</h2><p>You can now close this window.</p></div>';
                    setTimeout(() => window.close(), 1000);
                })
                .catch(err => {
                    alert('Failed to shut down. Please close the terminal or kill the process manually.');
                });
        }
    }
    </script>    
    <form method="POST">
        <textarea name="urls" placeholder="Paste one or more URLs (one per line)">{{ input_text }}</textarea>
        <button type="submit">Generate Previews</button>
    </form>
    <br>
    {% if cards %}
    <div class="cards">
        {% for card in cards %}
        <a href="{{ card.url }}" target="_blank" class="card">
            {% if card.image %}
                <div class="card-image"><img src="{{ card.image }}" alt="Preview image"></div>
            {% else %}
                <div class="card-image">No preview image</div>
            {% endif %}
            <div class="card-content">
                {% if card.site_name %}
                <div class="card-site">{{ card.site_name }}</div>
                {% endif %}
                <h2 class="card-title">{{ card.title }}</h2>
                <p class="card-desc">{{ card.description or 'No description available.' }}</p>
            </div>
        </a><br>
        {% endfor %}
    <br><br>
    </div>
    {% endif %}

        <div class="instructions">
        <h2>📝 How to Use It</h2>
        <p>In the text area below, paste one or more URLs — one per line.</p>
        <p>For <strong>Medium links</strong>, you can add a custom image on the next line using <code>!image &lt;URL&gt;</code>:</p>
        <p>For <strong>Medium articles</strong>, you can add a custom title and description on the next line using <code>!title Your own title</code> and for description <code>!desc your own description</code>:</p>
        <pre>https://medium.com/artificial-corner/exploratory-document-analysis-is-this-a-thing-ed9f4809f364
!image https://miro.medium.com/v2/resize:fit:640/format:webp/1*DB1Jq4zTpOoGulmj9kKfVQ.png
!title Exploratory document analysis is this a thing? 
!desc The only important thing is to take care of your data 

https://thepoorgpuguy.substack.com/p/ai-frankenstein-is-alive-part-2?r=i78xo</pre>
        <p><strong>How to get the Medium image URL:</strong></p>
        <ol>
            <li>Open the Medium article in your browser</li>
            <li>Right-click the <strong>header image</strong> → <em>Copy image address</em></li>
            <li>Paste it after <code>!image </code></li>
        </ol>
        <p>The app will use your image for Medium cards (faster and more reliable!). For non-Medium links, <code>!image</code> is ignored.</p>
    </div>
</body>
</html>
```

---

### ▶️ Step 4: Run the App

In your terminal, run:

```bash
python app.py
```

Then open your browser to:  
👉 **http://127.0.0.1:5000**

---


### 📝 How to Use Manual Overrides

In the text area, paste:

```text
https://example.com/poor-metadata
!title My Custom Title
!desc This is a much better description than the auto-fetched one.
!image https://example.com/great-image.jpg

https://medium.com/pub/member-story
!title Behind the Paywall: Key Insights
!desc Summary of the article even though it's paywalled.
!image https://miro.medium.com/v2/resize:fit:1400/abc123.jpeg
```

> 🔹 Directives must be **on separate lines**, **immediately after the URL**  
> 🔹 Order doesn’t matter (`!image` before `!desc` is fine)  
> 🔹 You can use **any combination** (just title, just image, all three, etc.)

---

### 🔧 Update Your `index.html` Instructions (Optional but Recommended)

Add this to your instructions box in `templates/index.html`:

> You can also customize the **description** using `!desc Your description...`:
> ```text
> https://example.com/article
> !title Custom Title
> !desc A clear, concise summary.
> !image https://example.com/image.jpg
> ```

---

### ▶️ Build Standalone App

```bash
pip install flask requests beautifulsoup4
pyinstaller --onefile --windowed --add-data "templates;templates" app.py
```

The resulting `dist/app.exe` will:
- Launch in browser automatically  
- Let you create perfect cards with full control  
- Shut down cleanly with the **Quit App** button  

### Flags explained:
- `--onefile`: Single executable (slower startup, but cleaner)
- `--windowed`: No console window (optional — you might want to keep console for debugging; if so, remove this flag)
- `--add-data`: Includes your `templates` folder

> 💡 Tip: If you want **faster startup**, use `--onedir` instead of `--onefile`.

---

## 📁 Folder Structure Must Be:
```
your-project/
├── app.py
└── templates/
    └── index.html
```

PyInstaller will bundle everything into `dist/app.exe` (Windows) or `dist/app` (macOS/Linux).

---

## 🧪 Step 3: Test the Executable

Go to `dist/` and run:
- **Windows**: `app.exe`
- **macOS**: `./app`
- **Linux**: `./app`

It should:
1. Start silently (or with a console if you skipped `--windowed`)
2. Open your browser to `http://127.0.0.1:5000`
3. Show your app

---

## 🎁 Bonus: Make It Feel Like a Real App

### Option A: Hide the Console (Windows)
Use `--windowed` → but you lose error logs.  
**Better**: Keep console during dev, remove it for final release.

### Option B: Change App Icon
```bash
pyinstaller --onefile --windowed --icon=app.ico --add-data "templates;templates" app.py
```

### Option C: Bundle as Installer (Advanced)
Use tools like:
- **Windows**: Inno Setup, NSIS
- **macOS**: Create `.app` bundle + `create-dmg`
- **All**: [Nuitka](https://nuitka.net/) (alternative to PyInstaller, often faster)

---

## ⚠️ Limitations to Know
- **Antivirus false positives**: PyInstaller apps are often flagged (common issue, harmless).
- **Large file size**: ~30–70 MB due to Python + Flask + requests + bs4.
- **First run slow**: Unpacking from onefile takes time.

---

## ✅ Final Recommendation

For personal or internal use:
> **PyInstaller + Flask + auto-open browser = perfect standalone tool**

For public distribution:
> Consider **adding a README**, signing the executable (Windows), or using **Docker/Desktop alternatives** like **Tauri** (Rust + web frontend) — but that’s a bigger rewrite.

---

