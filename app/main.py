import random
import string
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from pydantic import BaseModel
import redis
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

from config import REDIS_HOST, REDIS_PORT, BASE_URL

app = FastAPI()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #8b5cf6;
            --primary-hover: #7c3aed;
            --primary-glow: rgba(139, 92, 246, 0.5);
            --bg: #0f172a;
            --surface: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body {
            background-color: var(--bg); color: var(--text);
            display: flex; justify-content: center; align-items: center; min-height: 100vh;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(139, 92, 246, 0.15), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(56, 189, 248, 0.15), transparent 25%);
            overflow: hidden;
        }
        
        /* Floating background elements */
        .blob {
            position: absolute; filter: blur(80px); z-index: -1; opacity: 0.6;
            animation: float 10s infinite ease-in-out alternate;
        }
        .blob-1 { top: -10%; left: -10%; width: 400px; height: 400px; background: #8b5cf6; }
        .blob-2 { bottom: -10%; right: -10%; width: 500px; height: 500px; background: #3b82f6; animation-delay: -5s; }
        @keyframes float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(30px, 50px) scale(1.1); } }

        .container {
            background: var(--surface); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            padding: 3rem; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            width: 100%; max-width: 480px; text-align: center;
            transform: translateY(0); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 10;
        }
        .container:hover { box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.1); }
        
        h1 { 
            margin-bottom: 0.5rem; font-weight: 700; font-size: 2.2rem; letter-spacing: -0.02em;
            background: linear-gradient(135deg, #c4b5fd 0%, #8b5cf6 50%, #3b82f6 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: gradient-shift 3s infinite linear alternate;
        }
        @keyframes gradient-shift { 0% { filter: hue-rotate(0deg); } 100% { filter: hue-rotate(15deg); } }
        
        p.subtitle { color: var(--text-muted); margin-bottom: 2.5rem; font-size: 0.95rem; line-height: 1.5; }
        
        .input-group { position: relative; display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1rem; }
        
        input {
            width: 100%; padding: 1.2rem; border-radius: 16px;
            background: rgba(15, 23, 42, 0.5); border: 2px solid rgba(255, 255, 255, 0.05);
            color: var(--text); font-size: 1.05rem; outline: none; 
            transition: all 0.3s ease; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }
        input:focus { border-color: var(--primary); background: rgba(15, 23, 42, 0.8); box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.15), inset 0 2px 4px rgba(0,0,0,0.2); }
        input::placeholder { color: #475569; }
        
        button {
            width: 100%; padding: 1.2rem; border-radius: 16px; font-weight: 600; font-size: 1.05rem; letter-spacing: 0.02em;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white; border: none; cursor: pointer; position: relative; overflow: hidden;
            transition: all 0.3s ease; box-shadow: 0 4px 15px var(--primary-glow);
        }
        button::after {
            content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
            background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent);
            transform: rotate(45deg) translateX(-100%); transition: transform 0.6s ease;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px var(--primary-glow); filter: brightness(1.1); }
        button:hover::after { transform: rotate(45deg) translateX(100%); }
        button:active { transform: translateY(1px); box-shadow: 0 2px 10px var(--primary-glow); }
        
        button.loading { background: #475569; box-shadow: none; cursor: not-allowed; animation: pulse 1.5s infinite; filter: none; transform: none; }
        button.loading::after { display: none; }
        @keyframes pulse { 0% { opacity: 0.7; } 50% { opacity: 1; } 100% { opacity: 0.7; } }

        .result-box {
            margin-top: 1.5rem; padding: 1.5rem; border-radius: 16px;
            background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2);
            display: none; word-break: break-all; position: relative;
            transform-origin: top; animation: scaleDown 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }
        @keyframes scaleDown { from { opacity: 0; transform: scaleY(0.8) translateY(-20px); } to { opacity: 1; transform: scaleY(1) translateY(0); } }
        
        .result-box.show { display: block; }
        
        .result-label { display: flex; align-items: center; justify-content: center; gap: 8px; color: var(--success); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.8rem; }
        .result-label svg { width: 16px; height: 16px; }
        
        .link-container { display: flex; align-items: center; background: rgba(0,0,0,0.2); border-radius: 12px; padding: 0.8rem; border: 1px solid rgba(255,255,255,0.05); }
        .link-container a { flex-grow: 1; color: var(--text); text-decoration: none; font-weight: 500; font-size: 1.1rem; transition: color 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left; }
        .link-container a:hover { color: var(--primary); }
        
        .copy-btn {
            background: rgba(255,255,255,0.1); border: none; width: 36px; height: 36px; border-radius: 8px;
            display: flex; justify-content: center; align-items: center; cursor: pointer; color: white;
            transition: all 0.2s; margin-left: 10px; flex-shrink: 0;
        }
        .copy-btn:hover { background: var(--primary); transform: scale(1.05); }
        .copy-btn:active { transform: scale(0.95); }
        
        .error { color: #f43f5e; font-size: 0.9rem; margin-top: 1rem; padding: 0.8rem; background: rgba(244, 63, 94, 0.1); border-radius: 12px; display: none; animation: shake 0.5s ease-in-out; }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
        
        .toast {
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(100px);
            background: var(--success); color: white; padding: 12px 24px; border-radius: 30px;
            font-weight: 600; font-size: 0.9rem; box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
            opacity: 0; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); pointer-events: none;
        }
        .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
    </style>
</head>
<body>
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    
    <div class="container" id="mainCard">
        <h1>URL Shortener</h1>
        <p class="subtitle">Transform your long, messy links into short, memorable ones in a single click.</p>
        
        <div class="input-group">
            <input type="url" id="urlInput" placeholder="https://example.com/very/long/path" required autocomplete="off">
            <button id="shortenBtn" onclick="shortenUrl()">
                <span>Shorten URL</span>
            </button>
        </div>
        
        <div class="result-box" id="resultBox">
            <div class="result-label">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                Success!
            </div>
            <div class="link-container">
                <a href="#" id="shortLink" target="_blank"></a>
                <button class="copy-btn" onclick="copyToClipboard()" title="Copy to clipboard">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" width="18" height="18"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                </button>
            </div>
        </div>
        
        <p class="error" id="errorText"></p>
    </div>
    
    <div class="toast" id="toast">Copied to clipboard!</div>

    <script>
        let currentShortUrl = "";
        
        async function shortenUrl() {
            const input = document.getElementById('urlInput');
            const btn = document.getElementById('shortenBtn');
            const resultBox = document.getElementById('resultBox');
            const shortLink = document.getElementById('shortLink');
            const errorText = document.getElementById('errorText');
            
            const url = input.value.trim();
            if (!url) {
                showError("Please enter a valid URL to shorten.");
                input.focus();
                return;
            }

            try {
                btn.classList.add('loading');
                btn.innerHTML = 'Shortening...';
                btn.disabled = true;
                errorText.style.display = "none";
                resultBox.classList.remove('show');

                const response = await fetch('/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || "Failed to shorten URL. Please try again.");
                }

                currentShortUrl = window.location.origin + "/" + data.short_code;
                shortLink.href = currentShortUrl;
                shortLink.innerText = window.location.origin.replace(/^https?:\\/\\//, '') + "/" + data.short_code;
                
                setTimeout(() => {
                    resultBox.classList.add('show');
                }, 100);
                
            } catch (err) {
                showError(err.message);
            } finally {
                btn.classList.remove('loading');
                btn.innerHTML = 'Shorten URL';
                btn.disabled = false;
            }
        }
        
        function showError(msg) {
            const errorText = document.getElementById('errorText');
            errorText.innerText = msg;
            errorText.style.display = "block";
            
            errorText.style.animation = 'none';
            errorText.offsetHeight; 
            errorText.style.animation = null;
        }

        async function copyToClipboard() {
            if (!currentShortUrl) return;
            try {
                await navigator.clipboard.writeText(currentShortUrl);
                showToast();
            } catch (err) {
                console.error('Failed to copy', err);
            }
        }
        
        function showToast() {
            const toast = document.getElementById('toast');
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2500);
        }

        document.getElementById('urlInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') shortenUrl();
        });
        
        document.addEventListener('mousemove', (e) => {
            const container = document.getElementById('mainCard');
            if(!container) return;
            const xAxis = (window.innerWidth / 2 - e.pageX) / 80;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 80;
            container.style.transform = `perspective(1000px) rotateY(${xAxis}deg) rotateX(${yAxis}deg) translateY(-5px)`;
        });
        
        document.addEventListener('mouseleave', () => {
            const container = document.getElementById('mainCard');
            if(!container) return;
            container.style.transform = `perspective(1000px) rotateY(0deg) rotateX(0deg) translateY(0)`;
        });
    </script>
</body>
</html>
"""

@app.get("/")
def read_root():
    return HTMLResponse(content=HTML_CONTENT)

# Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Prometheus metrics
total_urls_created = Counter("total_urls_created", "Total number of shortened URLs created")
total_redirects = Counter("total_redirects", "Total number of redirects")
active_urls = Gauge("active_urls", "Number of currently active shortened URLs")

class URLRequest(BaseModel):
    url: str

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

@app.post("/shorten")
def shorten_url(request: URLRequest):
    short_code = generate_short_code()
    
    # Ensure uniqueness
    while redis_client.exists(short_code):
        short_code = generate_short_code()
        
    # Store in Redis with TTL of 7 days (7 * 24 * 60 * 60 = 604800 seconds)
    redis_client.setex(short_code, 604800, request.url)
    
    # Update Prometheus metrics
    total_urls_created.inc()
    active_urls.inc()
    
    return {
        "short_code": short_code,
        "short_url": f"{BASE_URL}/{short_code}"
    }

@app.get("/metrics")
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/{short_code}")
def redirect_to_original(short_code: str):
    original_url = redis_client.get(short_code)
    
    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found")
        
    # Increment hit counter in Redis
    redis_client.incr(f"hits:{short_code}")
    
    # Update Prometheus metric
    total_redirects.inc()
    
    return RedirectResponse(url=original_url, status_code=302)
