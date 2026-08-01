from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Lütfen geçerli bir URL girin.'}), 400

    cookie_path = 'cookies.txt'

    # yt-dlp Gelişmiş İndirme Konfigürasyonu
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    # Eğer cookies.txt dosyası varsa YouTube isteğine ekle
    if os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            download_url = info.get('url')
            if not download_url and 'formats' in info:
                for fmt in reversed(info['formats']):
                    if fmt.get('url'):
                        download_url = fmt['url']
                        break

            if not download_url:
                return jsonify({'error': 'İndirilebilir medya bağlantısı bulunamadı.'}), 400

            return jsonify({
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', ''),
                'url': download_url
            })
    except Exception as e:
        print("Hata Detayı:", str(e))
        return jsonify({'error': f'Sunucu Hatası: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
