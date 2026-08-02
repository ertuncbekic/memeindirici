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

    # Hazır birleşik video+ses formatını zorluyoruz
    ydl_opts = {
        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    # Cookies dosyası varsa ekle
    if os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            download_url = info.get('url')
            
            # Doğrudan URL çıkmazsa format listesinden hazır MP4 bağlantısını çek
            if not download_url and 'formats' in info:
                # Önce hem video hem ses barındıran formatları süz
                for fmt in reversed(info['formats']):
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none' and fmt.get('url'):
                        download_url = fmt['url']
                        break
                
                # Yine bulamazsa olan ilk geçerli URL'i al
                if not download_url:
                    for fmt in reversed(info['formats']):
                        if fmt.get('url'):
                            download_url = fmt['url']
                            break

            if not download_url:
                return jsonify({'error': 'İndirilebilir uygun medya formatı bulunamadı.'}), 400

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
