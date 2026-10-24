import os
import json
from flask import Flask, request, Response, redirect, url_for

app = Flask(__name__)

pending_queue = []
song_queue = []

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
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      .player-container {
        background: rgba(18, 18, 18, 0.95);
        padding: 15px 20px;
        border-radius: 12px;
        border: 2px solid #1DB954;
        box-shadow: 0 0 20px rgba(29, 185, 84, 0.4);
        width: 360px;
        color: white;
      }
      .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 8px; margin-bottom: 10px; }
      .title { color: #1DB954; font-size: 14px; font-weight: bold; margin: 0; }
      .status-dot { width: 10px; height: 10px; background: #e74c3c; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #e74c3c; }
      .status-dot.playing { background: #1DB954; box-shadow: 0 0 10px #1DB954; }
      .now-playing { font-size: 13px; color: #b3b3b3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .now-playing span { color: white; font-weight: bold; }
      #player { display: none; }
    </style>
    </head>
    <body>
      <div class="player-container">
        <div class="header">
          <p class="title">🎵 Şarkı İstek Sistemi</p>
          <div><span id="statusDot" class="status-dot"></span> <span id="statusText" style="font-size: 11px; color: #aaa;">Bekliyor</span></div>
        </div>
        <div class="now-playing" id="nowPlaying">Şarkı bekleniyor...</div>
        <div id="player"></div>
      </div>

      <script src="https://www.youtube.com/iframe_api"></script>
      <script>
        let player;
        let queue = [];
        let isPlaying = false;

        function onYouTubeIframeAPIReady() {
          player = new YT.Player('player', {
            height: '0',
            width: '0',
            events: {
              'onStateChange': onPlayerStateChange
            }
          });
        }

        async function onPlayerStateChange(event) {
          // YT.PlayerState.ENDED == 0 (Şarkı bitti)
          if (event.data === YT.PlayerState.ENDED) {
            isPlaying = false;
            document.getElementById('statusDot').className = "status-dot";
            document.getElementById('statusText').innerHTML = "Bekliyor";
            
            // Şarkının bittiğini sunucuya bildir ve silindiğinden emin ol
            try {
              await fetch('/pop_song');
            } catch (e) {}

            // Hemen ardından güncel kuyruğu çek ve sonrakini çal
            fetchQueueAndPlay();
          }
        }

        function playNext() {
          if (queue.length > 0 && !isPlaying) {
            isPlaying = true;
            let current = queue[0];
            let nick = current && current.nick ? current.nick : "Bilinmeyen";
            document.getElementById('nowPlaying').innerHTML = `İsteyen: <span>${nick}</span>`;
            document.getElementById('statusDot').className = "status-dot playing";
            document.getElementById('statusText').innerHTML = "Çalıyor";
            
            player.loadVideoById(current.videoId);
            player.playVideo();
          } else if (queue.length === 0) {
            document.getElementById('nowPlaying').innerHTML = "Şarkı bekleniyor...";
            document.getElementById('statusDot').className = "status-dot";
            document.getElementById('statusText').innerHTML = "Bekliyor";
            isPlaying = false;
          }
        }

        async function fetchQueueAndPlay() {
          try {
            let res = await fetch('/get_queue');
            if (!res.ok) return;
            let data = await res.json();
            queue = data;
            
            if (!isPlaying && queue.length > 0 && player && typeof player.loadVideoById === 'function') {
              playNext();
            }
          } catch (e) {}
        }

        // Şarkı çalmıyorken her 2 saniyede bir yeni istek var mı diye kontrol et
        setInterval(() => {
          if (!isPlaying) {
            fetchQueueAndPlay();
          }
        }, 2000);
      </script>
    </body>
    </html>
    """

@app.route("/istek")
def istek_sayfasi():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Şarkı İstek Paneli</title>
    <style>
      body { background: #121212; color: white; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
      .card { background: #181818; padding: 30px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); text-align: center; width: 340px; border: 1px solid #282828; }
      h2 { color: #1DB954; margin-bottom: 10px; font-size: 20px; }
      p { color: #b3b3b3; font-size: 13px; margin-bottom: 20px; line-height: 1.4; }
      label { display: block; text-align: left; font-size: 13px; color: #b3b3b3; margin-bottom: 5px; }
      input { width: 100%; box-sizing: border-box; padding: 10px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #333; background: #222; color: white; font-size: 14px; outline: none; }
      input:focus { border-color: #1DB954; }
      button[type="submit"] { background: #1DB954; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 15px; cursor: pointer; width: 100%; font-weight: bold; }
      button[type="submit"]:hover { background: #1ed760; }
    </style>
    </head>
    <body>
      <div class="card">
        <h2>🎵 Çatı Katı FM Acil İstek Şarkı Hattı</h2>
        <p>Sevdiğin şarkının YouTube linkini gönder, moderatör onayından sonra sırayla çalsın! ( Attığın link 4 dakikadan kısa olmalı )</p>
        
        <form action="/gonder" method="POST" accept-charset="UTF-8">
          <label>Kullanıcı Adın (Nick):</label>
          <input type="text" name="nick" placeholder="Örn: " required autocomplete="off" maxlength="20">
          
          <label>YouTube Şarkı Linki:</label>
          <input type="text" name="url" placeholder="Örn: https://youtu.be/..." required autocomplete="off">
          
          <button type="submit">İsteği Gönder</button>
        </form>
      </div>
    </body>
    </html>
    """

def extract_youtube_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return "dQw4w9WgXcQ"

@app.route("/gonder", methods=["POST"])
def gonder():
    global pending_queue
    request.charset = 'utf-8'
    nick = request.form.get("nick")
    url = request.form.get("url")
    
    if nick and url:
        video_id = extract_youtube_id(url)
        pending_queue.append({"nick": nick, "videoId": video_id})
            
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head><meta charset="UTF-8"><title>Gönderildi</title></head>
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0;">
      <div style="background:#181818; padding:35px; border-radius:16px; border:1px solid #282828;">
        <h2 style="color:#1DB954;">🎉 İsteğin Moderatör Onayına Gönderildi!</h2>
        <p style="color:#b3b3b3; margin-bottom:20px;">Onaylandığında sırayla otomatik çalmaya başlayacaktır.</p>
        <a href="/istek" style="background:#1DB954; color:white; padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:bold; display:inline-block;">Yeni İstek Gönder</a>
      </div>
    </body>
    """

@app.route("/mod")
def mod_paneli():
    items_html = ""
    if not pending_queue:
        items_html = "<tr><td colspan='3' style='text-align:center; color:#777; padding:20px;'>Onay bekleyen istek yok.</td></tr>"
    else:
        for index, item in enumerate(pending_queue):
            items_html += f"""
            <tr>
              <td style="padding:12px; border-bottom:1px solid #333;"><b>{item['nick']}</b></td>
              <td style="padding:12px; border-bottom:1px solid #333; font-size:13px;"><a href="https://youtu.be/{item['videoId']}" target="_blank" style="color:#1DB954;">Şarkıyı Dinle / Kontrol Et</a></td>
              <td style="padding:12px; border-bottom:1px solid #333; text-align:right; white-space:nowrap;">
                <a href="/onayla/{index}" style="background:#1DB954; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:bold; margin-right:5px;">Onayla</a>
                <a href="/reddet/{index}" style="background:#e74c3c; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:bold;">Reddet</a>
              </td>
            </tr>
            """

    return f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <title>Moderatör Onay Paneli</title>
    <style>
      body {{ background: #121212; color: white; font-family: 'Segoe UI', sans-serif; padding: 40px; }}
      .container {{ max-width: 750px; margin: 0 auto; background: #181818; padding: 25px; border-radius: 12px; border: 1px solid #333; }}
      h2 {{ color: #1DB954; margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 10px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
      .refresh-btn {{ background: #333; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 14px; float: right; }}
      .refresh-btn:hover {{ background: #444; }}
    </style>
    <meta http-equiv="refresh" content="5">
    </head>
    <body>
      <div class="container">
        <h2>🛡️ Moderatör İstek Paneli <a href="/mod" class="refresh-btn">🔄 Yenile</a></h2>
        <p style="color:#aaa; font-size:13px;">Gelen YouTube linkini kontrol edip onaylayın.</p>
        <table>
          {items_html}
        </table>
      </div>
    </body>
    </html>
    """

@app.route("/onayla/<int:index>")
def onayla(index):
    global pending_queue, song_queue
    if 0 <= index < len(pending_queue):
        item = pending_queue.pop(index)
        song_queue.append(item)
    return redirect(url_for('mod_paneli'))

@app.route("/reddet/<int:index>")
def reddet(index):
    global pending_queue
    if 0 <= index < len(pending_queue):
        pending_queue.pop(index)
    return redirect(url_for('mod_paneli'))

@app.route("/pop_song")
def pop_song():
    global song_queue
    if song_queue:
        song_queue.pop(0)
    return "OK"

@app.route("/get_queue")
def get_queue():
    json_data = json.dumps(song_queue, ensure_ascii=False)
    return Response(json_data, mimetype='application/json; charset=utf-8')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
