from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import urllib.request
import json
import re

app = Flask(__name__)
CORS(app)

# YouTube ID ayıklayıcı (Yedek API için)
def extract_youtube_id(url):
    reg = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/\s]{11})'
    match = re.search(reg, url)
    return match.group(1) if match else None

# YT-DLP çökerse devreye girecek olan Yedek B-Planı API'si
def fallback_api(url):
    try:
        req = urllib.request.Request(
            'https://api.cobalt.tools/',
            data=json.dumps({"url": url}).encode('utf-8'),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if 'url' in data:
                return data['url']
            elif data.get('picker'):
                return data['picker'][0]['url']
    except:
        pass
    return None

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Lütfen geçerli bir URL girin.'}), 400

    # YT-DLP'nin çökmesini tamamen engellemek için kısıtlamaları kaldırdık
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,  # Herhangi bir hatada çökmesini engeller
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info:
                download_url = None
                formats = info.get('formats', [])

                # 1. Öncelik: Hem video hem ses olan hazır birleşik MP4'ü bul
                valid_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url')]
                if valid_formats:
                    # Çözünürlüğe göre yukarıdan aşağıya sırala, en yükseğini al
                    valid_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
                    download_url = valid_formats[0]['url']

                # 2. Öncelik: Birleşik video yoksa sadece video linkini al (sessiz de olsa indirmesi için)
                if not download_url and formats:
                    video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('url')]
                    if video_formats:
                        video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
                        download_url = video_formats[0]['url']
                        
                # 3. Öncelik: Eğer formats listesinde sadece genel bir URL varsa (Örn: TikTok, Instagram)
                if not download_url and formats:
                    for fmt in reversed(formats):
                        if fmt.get('url'):
                            download_url = fmt['url']
                            break

                # info['url'] varsa doğrudan al
                if not download_url:
                    download_url = info.get('url')

                # Her şey yolundaysa linki ön yüze gönder
                if download_url:
                    return jsonify({
                        'title': info.get('title', 'Video'),
                        'thumbnail': info.get('thumbnail', ''),
                        'url': download_url
                    })

    except Exception as e:
        print("YT-DLP başarısız oldu:", str(e))

    # YUKARIDAKI HİÇBİR ŞEY ÇALIŞMAZSA (CRASH / ENGEL): DEVREYE YEDEK API GİRER
    print("Yedek (Fallback) API Devrede...")
    fallback_url = fallback_api(url)
    
    if fallback_url:
        yt_id = extract_youtube_id(url)
        return jsonify({
            'title': 'Medya Hazır',
            'thumbnail': f'https://img.youtube.com/vi/{yt_id}/hqdefault.jpg' if yt_id else 'https://placehold.co/300x200/334155/fff?text=Medya',
            'url': fallback_url
        })

    # Yedek API bile patlarsa (ki bu linkin bozuk veya tamamen gizli olduğu anlamına gelir)
    return jsonify({'error': 'Video indirilemiyor. Bağlantı özel bir hesaba ait olabilir veya YouTube tarafından tamamen engellenmiş.'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
