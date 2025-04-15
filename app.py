from flask import Flask, request, jsonify
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
        # yt-dlp options to download the best video and audio, and use the cookies.txt file
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",  # Download best video + audio
            "merge_output_format": "mp4",  # Output format is mp4
            "outtmpl": "/tmp/%(id)s.%(ext)s",  # Save file in the /tmp directory with unique file name
            "cookiefile": "cookies.txt",  # Use the cookies.txt for authentication (make sure the file is in the same folder)
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # Don't download, just get info
            formats = info.get("formats", [])
            video_url = formats[-1]["url"] if formats else None


        return jsonify({"download_url": video_url})  # Return the download URL

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle errors

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Get port from environment or default to 10000
    app.run(host="0.0.0.0", port=port)  # Run the app on the specified host and port
