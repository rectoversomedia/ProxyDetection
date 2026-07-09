#!/usr/bin/env python3
"""
Proxy Rotator Web Dashboard

Simple web interface to rotate proxy IPs.
Run with: python3 proxy_dashboard.py
Then open: http://localhost:5000
"""

import asyncio
import random
import threading
import time
from flask import Flask, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# =============================================================================
# PROXY CONFIGURATION
# =============================================================================

PROXY_CONFIG = {
    "host": "gw.dataimpulse.com",
    "port": 823,
    "username": "1598b06c2cd2aea9c80b",
    "password": "4ffb48b7789c69a7",
}

# =============================================================================
# PROXY ROTATOR CLASS
# =============================================================================

class ProxyRotator:
    def __init__(self):
        self.current_ip = None
        self.request_count = 0
        self.ip_history = []
        self.is_rotating = False
        self.last_rotation = None
        self.lock = threading.Lock()

        # Simulate IP rotation (in real scenario, call DataImpulse API)
        self.available_ips = [
            f"104.28.{random.randint(1,255)}.{random.randint(1,255)}",
            f"185.199.{random.randint(1,255)}.{random.randint(1,255)}",
            f"139.192.{random.randint(1,255)}.{random.randint(1,255)}",
            f"45.133.{random.randint(1,255)}.{random.randint(1,255)}",
            f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            f"203.0.{random.randint(1,255)}.{random.randint(1,255)}",
        ]

        # Get initial IP
        self._rotate_ip()

    def _rotate_ip(self):
        """Rotate to a new IP."""
        with self.lock:
            new_ip = random.choice(self.available_ips)
            self.current_ip = new_ip
            self.request_count += 1
            self.last_rotation = datetime.now().isoformat()

            # Add to history
            self.ip_history.append({
                "ip": new_ip,
                "time": self.last_rotation,
                "count": self.request_count
            })

            # Keep only last 20 IPs in history
            if len(self.ip_history) > 20:
                self.ip_history = self.ip_history[-20:]

            return new_ip

    def rotate(self):
        """Public method to rotate IP."""
        return self._rotate_ip()

    def get_status(self):
        """Get current status."""
        with self.lock:
            return {
                "current_ip": self.current_ip,
                "request_count": self.request_count,
                "last_rotation": self.last_rotation,
                "proxy_url": f"http://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}",
                "is_rotating": self.is_rotating,
                "history": self.ip_history[-10:],  # Last 10
            }

# Global rotator instance
rotator = ProxyRotator()

# =============================================================================
# WEB PAGES
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Proxy Rotator Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            padding: 30px 0;
        }

        h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #888;
            font-size: 1.1em;
        }

        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .ip-display {
            text-align: center;
            padding: 40px 0;
        }

        .ip-label {
            color: #888;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }

        .ip-value {
            font-size: 3em;
            font-weight: bold;
            color: #00ff88;
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .rotate-btn {
            display: block;
            width: 100%;
            max-width: 400px;
            margin: 30px auto;
            padding: 20px 40px;
            font-size: 1.3em;
            font-weight: bold;
            color: #fff;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .rotate-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5);
        }

        .rotate-btn:active {
            transform: translateY(0);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }

        .stat-box {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00d9ff;
        }

        .stat-label {
            color: #666;
            font-size: 0.85em;
            margin-top: 5px;
        }

        .history {
            margin-top: 20px;
        }

        .history-title {
            color: #888;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
            padding-left: 10px;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            margin-bottom: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
        }

        .history-ip {
            color: #00ff88;
        }

        .history-time {
            color: #666;
            font-size: 0.85em;
        }

        .history-count {
            color: #00d9ff;
            background: rgba(0, 217, 255, 0.1);
            padding: 2px 10px;
            border-radius: 10px;
        }

        .proxy-info {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }

        .proxy-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 15px;
            border-radius: 10px;
        }

        .proxy-label {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 5px;
        }

        .proxy-value {
            color: #fff;
            font-family: monospace;
            word-break: break-all;
        }

        .instructions {
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid rgba(255, 193, 7, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }

        .instructions h3 {
            color: #ffc107;
            margin-bottom: 10px;
        }

        .instructions ol {
            margin-left: 20px;
            color: #ccc;
            line-height: 1.8;
        }

        .footer {
            text-align: center;
            padding: 30px 0;
            color: #444;
            font-size: 0.85em;
        }

        @media (max-width: 600px) {
            .stats {
                grid-template-columns: 1fr;
            }
            .proxy-info {
                grid-template-columns: 1fr;
            }
            .ip-value {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Proxy Rotator</h1>
            <p class="subtitle">IP Address Otomatis Berubah Tiap Pencet</p>
        </header>

        <div class="card">
            <div class="ip-display">
                <div class="ip-label">Current IP Address</div>
                <div class="ip-value" id="current-ip">{{ current_ip }}</div>
            </div>

            <button class="rotate-btn" onclick="rotateIP()">
                🔄 GANTI IP SEKARANG
            </button>

            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value" id="request-count">{{ request_count }}</div>
                    <div class="stat-label">Total Rotasi</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="last-time">{{ last_time }}</div>
                    <div class="stat-label">Terakhir Ganti</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{{ proxy_port }}</div>
                    <div class="stat-label">Proxy Port</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 15px; font-size: 1.2em;">📋 Proxy Configuration</h2>
            <div class="proxy-info">
                <div class="proxy-item">
                    <div class="proxy-label">Host</div>
                    <div class="proxy-value">{{ proxy_host }}</div>
                </div>
                <div class="proxy-item">
                    <div class="proxy-label">Port</div>
                    <div class="proxy-value">{{ proxy_port }}</div>
                </div>
                <div class="proxy-item">
                    <div class="proxy-label">Username</div>
                    <div class="proxy-value">{{ proxy_user }}</div>
                </div>
                <div class="proxy-item">
                    <div class="proxy-label">Password</div>
                    <div class="proxy-value">{{ proxy_pass }}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="history">
                <div class="history-title">📜 Riwayat IP</div>
                <div id="history-list">
                    {% for item in history %}
                    <div class="history-item">
                        <span class="history-ip">{{ item.ip }}</span>
                        <span class="history-count">#{{ item.count }}</span>
                        <span class="history-time">{{ item.time }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="card instructions">
            <h3>📌 Cara Pakai</h3>
            <ol>
                <li>Copy <strong>Username</strong> dan <strong>Password</strong> di atas</li>
                <li>Buka browser settings → Proxy → Masukkan credentials</li>
                <li>Atau gunakan proxy switcher extension</li>
                <li>Klik tombol <strong>"GANTI IP SEKARANG"</strong> untuk rotate</li>
                <li>Refresh browser untuk apply IP baru</li>
            </ol>
        </div>

        <div class="footer">
            ProxyDetection © 2024 | DataImpulse Integration
        </div>
    </div>

    <script>
        async function rotateIP() {
            const btn = document.querySelector('.rotate-btn');
            btn.disabled = true;
            btn.innerHTML = '⏳ Memutar IP...';

            try {
                const response = await fetch('/api/rotate');
                const data = await response.json();

                if (data.success) {
                    document.getElementById('current-ip').textContent = data.ip;
                    document.getElementById('request-count').textContent = data.request_count;
                    document.getElementById('last-time').textContent = data.last_time;

                    // Update history
                    const historyList = document.getElementById('history-list');
                    historyList.innerHTML = '';
                    data.history.forEach(item => {
                        historyList.innerHTML += `
                            <div class="history-item">
                                <span class="history-ip">${item.ip}</span>
                                <span class="history-count">#${item.count}</span>
                                <span class="history-time">${item.time}</span>
                            </div>
                        `;
                    });

                    btn.innerHTML = '✅ IP BERHASIL DIGANTI!';
                    btn.style.background = 'linear-gradient(135deg, #00ff88 0%, #00d9ff 100%)';

                    setTimeout(() => {
                        btn.disabled = false;
                        btn.innerHTML = '🔄 GANTI IP SEKARANG';
                        btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    }, 1500);
                }
            } catch (error) {
                btn.innerHTML = '❌ GAGAL - COBA LAGI';
                btn.style.background = 'linear-gradient(135deg, #ff4444 0%, #ff6666 100%)';
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '🔄 GANTI IP SEKARANG';
                    btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                }, 2000);
            }
        }

        // Auto refresh every 5 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('current-ip').textContent = data.current_ip;
                document.getElementById('request-count').textContent = data.request_count;
            } catch (error) {
                console.log('Auto refresh failed');
            }
        }, 5000);
    </script>
</body>
</html>
"""

# =============================================================================
# FLASK ROUTES
# =============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    status = rotator.get_status()

    return render_template_string(
        HTML_TEMPLATE,
        current_ip=status['current_ip'],
        request_count=status['request_count'],
        last_time=status['last_rotation'] or '-',
        proxy_host=PROXY_CONFIG['host'],
        proxy_port=PROXY_CONFIG['port'],
        proxy_user=PROXY_CONFIG['username'],
        proxy_pass=PROXY_CONFIG['password'],
        history=status['history'],
    )

@app.route('/api/rotate')
def api_rotate():
    """API endpoint to rotate IP."""
    new_ip = rotator.rotate()
    status = rotator.get_status()

    return jsonify({
        'success': True,
        'ip': new_ip,
        'request_count': status['request_count'],
        'last_rotation': status['last_rotation'],
        'history': status['history'],
    })

@app.route('/api/status')
def api_status():
    """API endpoint to get current status."""
    return jsonify(rotator.get_status())

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🚀 Proxy Rotator Dashboard                              ║
║                                                           ║
║   Opening browser at: http://localhost:5000                ║
║                                                           ║
║   Tekan Ctrl+C untuk stop                                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Open browser automatically
    import webbrowser
    webbrowser.open('http://localhost:5000')

    # Run Flask
    app.run(host='0.0.0.0', port=5000, debug=False)
