from __future__ import unicode_literals
from django.shortcuts import redirect
from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, send
from yt_dlp import YoutubeDL
import requests
import sqlite3
import configparser
from pprint import pprint


# Initialize DB
def init_db():
    con = sqlite3.connect("data.db")
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS yt (id INTEGER PRIMARY KEY AUTOINCREMENT, url VARCHAR(256), filename VARCHAR(256), playlist VARCHAR(256), status INTEGER)")
    con.commit()
    con.close()


# Get playlist list from azuracast api
def get_playlists():
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    data = requests.get(
        f"{config['azuracast_host']}/api/station/{config['station_id']}/playlists", headers=headers)

    playlists = [{"id": key["id"], "name": key["name"]} for key in data.json()]
    return playlists


# Playlist ID to name
def get_playlist_name(id):
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    data = requests.get(
        f"{config['azuracast_host']}/api/station/{config['station_id']}/playlist/{id}", headers=headers).json()
    return data["name"]


# Render status tabe
def status():
    songs = get_songs_from_db()
    return str(render_template('status.html.j2', songs=songs))


# Add Song to DB
def add_song_to_db(url, playlist):
    con = sqlite3.connect("data.db")
    c = con.cursor()
    c.execute("INSERT INTO yt (url, playlist, status) VALUES (?, ?, ?)",
              (url, playlist, 2))
    con.commit()
    c.execute("SELECT last_insert_rowid()")
    id = c.fetchone()
    con.close()
    return id[0]


# Update Song in DB
def update_song_in_db(id, status, filename=""):
    con = sqlite3.connect("data.db")
    c = con.cursor()
    c.execute("UPDATE yt SET filename=?, status=? WHERE id=?",
              (filename, status, id))
    con.commit()
    con.close()



# Query Songs from DB
def get_songs_from_db(limit=10):
    try:
        con = sqlite3.connect("data.db")
        c = con.cursor()
        c.execute("SELECT * FROM yt ORDER BY id DESC LIMIT ?", (str(limit), ))
        rows = c.fetchall()
        con.close()
        return rows
    except:
        print("Oh no, it's broken")
        return []


# Create the flask app
app = Flask(__name__, static_url_path='/static')


# Connect the sqlite DB
init_db()

# Parse the config
parser = configparser.ConfigParser()
try:
    parser.read("config.ini")
    config = parser["config"]
except:
    parser.read("app/config.ini")
    config = parser["config"]


@app.route('/')
def index():
    return render_template('index.html.j2', playlists=get_playlists())


@app.route('/download')
def download():
    url = request.args.get('url', default=None, type=str)
    if not url:
        return "Expected 1 parameter for 'url', got 0."

    playlist = request.args.get('playlist', default=None, type=str)
    if not url:
        return "Expected 1 parameter for 'playlist', got 0."

    # Get playlist human readable name
    playlist_name = get_playlist_name(playlist)


    # Add the song to the database
    db_id = add_song_to_db(url, playlist_name)


    # Broadcast status update to websockets
    socketio.send(status())

    ydl_opts = {
        'format': 'bestaudio[ext=mp3]/best',
        'writethumbnail': True,
        'outtmpl': f"{config['music_dir']}/%(title)s.%(ext)s",
        'postprocessors': [
            {'key': 'FFmpegExtractAudio',
             'preferredcodec': 'mp3',
             'preferredquality': '192'},
            {'key': 'MetadataFromField',
             'formats': {"title:%(artist)s - %(meta_title)s"}, },
            {'key': 'FFmpegMetadata'},
            {'key': 'EmbedThumbnail'}]}

    with YoutubeDL(ydl_opts) as ydl:
        try:
            download = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(download)

            update_song_in_db(db_id, 0, filename)
        except:
            update_song_in_db(db_id, 1)
        # Broadcast status update to websockets
        socketio.send(status())
    return redirect("/")


# Create the websocket listener
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=5)


# Send data on connect
@socketio.on('connect')
def connect():
    send(status())


# run the app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
