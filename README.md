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
        <pre>https://medium.com/artificial-corner/exploratory-document-analysis-is-this-a-thing-ed9f4809f364
!image https://miro.medium.com/v2/resize:fit:1400/1*KsR2U0Z3vK1YxVvVXZ7Q9g.jpeg

https://example.com/other-article</pre>
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

### 🔄 Simpler & Clean Approach: **Per-URL Image Override via Comments**

Instead of complex dynamic UI, we’ll use a **simple convention** in the text area:

> Paste links like this:
> ```
> https://medium.com/.../my-article
> !image https://miro.medium.com/v2/.../123.jpg
> 
> https://other-site.com/blog
> ```

- Any line starting with `!image ` **immediately after a URL** will be treated as its **custom image**
- Only applies if the **previous line was a URL**
- Works only for Medium? We can **auto-detect** and **only enable this logic for Medium links**

This keeps the UI minimal (no JS, no dynamic rows) and works great in your current Flask form.

> 🔍 **How to get the Medium image URL**:
> 1. Open the Medium article in your browser
> 2. Right-click the **header image** → *Copy image address*
> 3. Paste it after `!image `

The app will:
- Skip fetching for that Medium link (faster!)
- Use your image
- Show a clean card

For non-Medium links, `!image` is ignored (but you can extend it later if needed).

---


---

# How to turn Link Preview Generator into a standalone desktop app

To turn your **Link Preview Generator** (with support for custom Medium images) into a **standalone desktop app** that users can run **without installing Python or dependencies**...

Here’s a practical, step-by-step plan using **PyInstaller** + **Flask** (which you already have), resulting in a **double-clickable `.exe` (Windows) or `.app` (macOS)** that starts a local server and opens the browser automatically.

---

## ✅ Goal
- One executable file
- Launches your Flask app **locally on `127.0.0.1:5000`**
- Automatically opens the browser
- Works **offline after first run** (no internet needed unless previewing links)

---

## 🛠️ Step 1: Finalize Your App Code

Make sure your `app.py` includes:
- The **auto-open browser** logic
- **Host binding to `127.0.0.1`** (not just default)
- **Disable debug mode**


## 📦 Step 2: Freeze with PyInstaller

### Install PyInstaller:
```bash
pip install pyinstaller
```

### Build the standalone app:
```bash
pyinstaller --onefile --windowed --add-data "templates;templates" app.py
```

> 📝 On **macOS/Linux**, use `:` instead of `;`:
> ```bash
> pyinstaller --onefile --windowed --add-data "templates:templates" app.py
> ```

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

