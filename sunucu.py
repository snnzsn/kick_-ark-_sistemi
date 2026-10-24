import os
import json
from flask import Flask, request, Response

app = Flask(__name__)

# Son istekleri tutacak olan liste (Maksimum 5 tane)
song_queue = []
MAX_QUEUE = 5

# 1. YAYIN EKRANI WIDGET'I (Streamlabs'e eklenecek ana adres)
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <style>
      body {
        margin: 0;
        background: transparent;
        overflow: hidden;
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        height: 100vh;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      .queue-box {
        background: rgba(0, 0, 0, 0.85);
        padding: 15px 20px;
        border-radius: 12px;
        border: 2px solid #1DB954;
        box-shadow: 0 0 20px rgba(29, 185, 84, 0.5);
        max-width: 400px;
      }
      h3 { color: #1DB954; margin: 0 0 10px 0; font-size: 16px; border-bottom: 1px solid #333; padding-bottom: 5px; }
      ul { list-style: none; padding: 0; margin: 0; }
      li { color: #ffffff; font-size: 14px; padding: 6px 0; border-bottom: 1px dashed #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      li:last-child { border-bottom: none; }
      li span { color: #1DB954; font-weight: bold; }
    </style>
    </head>
    <body>
      <div class="queue-box">
        <h3>🎵 Şarkı İstek Kuyruğu</h3>
        <ul id="songList">
          <li>Şarkı bekleniyor...</li>
        </ul>
      </div>
      <script>
        setInterval(async () => {
          try {
            let res = await fetch('/get_queue');
            if (!res.ok) return;
            let data = await res.json();
            let ul = document.getElementById('songList');
            ul.innerHTML = "";
            
            if(!data || data.length === 0) {
              ul.innerHTML = "<li>Şarkı bekleniyor...</li>";
            } else {
              data.forEach(item => {
                let li = document.createElement('li');
                li.innerHTML = `<span>${item.nick}</span> ➔ ${item.song}`;
                ul.appendChild(li);
              });
            }
          } catch (e) {}
        }, 1000);
      </script>
    </body>
    </html>
    """

# 2. İZLEYİCİ İSTEK PANELİ
@app.route("/istek")
def istek_sayfasi():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kick Şarkı İstek Paneli</title>
    <style>
      body { background: #121212; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
      .card { background: #181818; padding: 35px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); text-align: center; width: 320px; border: 1px solid #282828; }
      h2 { color: #1DB954; margin-bottom: 20px; font-size: 22px; }
      label { display: block; text-align: left; font-size: 14px; color: #b3b3b3; margin-bottom: 5px; }
      input { width: 100%; box-sizing: border-box; padding: 12px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #333; background: #222; color: white; font-size: 15px; outline: none; }
      input:focus { border-color: #1DB954; }
      button { background: #1DB954; color: white; border: none; padding: 14px; border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; font-weight: bold; }
      button:hover { background: #1ed760; }
    </style>
    </head>
    <body>
      <div class="card">
        <h2>🎵 Şarkı İsteği</h2>
        <form action="/gonder" method="POST" accept-charset="UTF-8">
          <label>Kullanıcı Adın (Nick):</label>
          <input type="text" name="nick" placeholder="Örn: Sinan" required autocomplete="off">
          
          <label>Şarkı ve Sanatçı:</label>
          <input type="text" name="song" placeholder="Örn: Teoman - Paramparça" required autocomplete="off">
          
          <button type="submit">İsteği Gönder</button>
        </form>
      </div>
    </body>
    </html>
    """

# 3. İSTEĞİ KUYRUĞA EKLEME
@app.route("/gonder", methods=["POST"])
def gonder():
    global song_queue
    # Türkçe karakterlerin bozulmaması için form verisini utf-8 olarak alıyoruz
    request.charset = 'utf-8'
    nick = request.form.get("nick")
    song = request.form.get("song")
    
    if nick and song:
        song_queue.insert(0, {"nick": nick, "song": song})
        if len(song_queue) > MAX_QUEUE:
            song_queue.pop()
            
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head><meta charset="UTF-8"><title>Gönderildi</title></head>
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0;">
      <div style="background:#181818; padding:35px; border-radius:16px; border:1px solid #282828;">
        <h2 style="color:#1DB954;">🎉 İsteğin Kuyruğa Eklendi!</h2>
        <p style="color:#b3b3b3; margin-bottom:20px;">Yayın ekranındaki yerini aldı.</p>
        <a href="/istek" style="background:#1DB954; color:white; padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:bold; display:inline-block;">Yeni İstek Gönder</a>
      </div>
    </body>
    </html>
    """

# 4. WIDGET İÇİN KUYRUĞU JSON OLARAK VERME (Türkçe Karakter Desteği ile)
@app.route("/get_queue")
def get_queue():
    json_data = json.dumps(song_queue, ensure_ascii=False)
    return Response(json_data, mimetype='application/json; charset=utf-8')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)