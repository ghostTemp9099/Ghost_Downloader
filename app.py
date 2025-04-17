from flask import Flask, request, jsonify, send_file, Response
import yt_dlp
import os

app = Flask(__name__)

# In-memory storage (used for viewing)
session_ids = []

@app.route("/")
def home():
    return "👻 Instagram Reel Downloader API is running!"

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
            info = ydl.extract_info(url, download=True)

        video_id = info.get("id")
        ext = info.get("ext", "mp4")
        local_file_path = f"/tmp/{video_id}.{ext}"

        return send_file(local_file_path, mimetype="video/mp4", as_attachment=False)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sessionid", methods=["POST"])
def receive_sessionid():
    data = request.get_json()
    session_id = data.get("sessionid")
    if not session_id:
        return jsonify({"error": "Missing sessionid"}), 400

    # Save in memory
    session_ids.append(session_id)

    # Save to file
    try:
        with open("session_ids_storage.txt", "a") as file:
            file.write(session_id + "\n")
    except Exception as e:
        print(f"Failed to write session ID to file: {e}")

    print(f"[✔️ RECEIVED] Session ID: {session_id}")
    return jsonify({"message": "Session ID received"}), 200

@app.route("/view-sessionids", methods=["GET"])
def view_sessionids():
    try:
        with open("session_ids_storage.txt", "r") as file:
            content = file.read()
        return Response(content, mimetype="text/plain")
    except FileNotFoundError:
        return Response("No session IDs saved yet.", mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
