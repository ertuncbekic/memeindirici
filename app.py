from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import urllib.request
import json

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Lütfen geçerli bir URL girin.'}), 400

    # KESİN ÇÖZÜM: 'b' parametresi (Best). Sadece ses ve görüntüsü hazır birleşik olan videoyu çeker, ffmpeg aramaz.
    ydl_opts = {
        'format': 'b', 
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    # Çerezler hala güvende ve çalışıyor
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Doğrudan tek parça MP4 linkini arayüze gönder
            if info and info.get('url'):
                return jsonify({
                    'title': info.get('title', 'Video'),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': info.get('url')
                })
    except Exception as e:
        print("YT-DLP Hatası:", str(e))

    # YEDEK PLAN (Sorunsuz Cobalt Sunucusu - Eski patlayan API değiştirildi)
    print("Yedek (Fallback) API Devrede...")
    try:
        req = urllib.request.Request(
            'https://co.wuk.sh/api/json',
            data=json.dumps({
                "url": url,
                "vQuality": "720",
                "filenamePattern": "classic"
            }).encode('utf-8'),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            c_data = json.loads(response.read().decode())
            if 'url' in c_data:
                return jsonify({
                    'title': 'Video Hazır (Yedek Sistem)',
                    'thumbnail': 'https://placehold.co/300x200/334155/fff?text=Medya',
                    'url': c_data['url']
                })
    except Exception as e:
        print("Fallback Hatası:", str(e))

    return jsonify({'error': 'Sistem videoyu işleyemedi. Lütfen farklı bir bağlantı deneyin.'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
