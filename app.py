from flask import Flask, request, jsonify, send_file
import yt_dlp
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Instagram Reel Downloader API is running!"

@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": "/tmp/%(id)s.%(ext)s",
            "cookiefile": "cookies.txt",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)  # Download + merge

        video_id = info.get("id")
        ext = info.get("ext", "mp4")
        local_file_path = f"/tmp/{video_id}.{ext}"

        # ✅ Serve the downloaded file directly
        return send_file(local_file_path, mimetype="video/mp4", as_attachment=False)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
