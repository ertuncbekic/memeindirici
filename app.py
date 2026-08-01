from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Lütfen geçerli bir URL girin.'}), 400

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Doğrudan url yoksa formatlar içinden en uygun olanı seç
            download_url = info.get('url')
            if not download_url and 'formats' in info:
                # Hem ses hem görüntü içeren formatı bul
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
        print("Hata:", str(e))
        return jsonify({'error': 'Video çekilemedi. Link gizli bir hesaba ait olabilir veya geçersizdir.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
