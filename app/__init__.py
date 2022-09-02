from django.shortcuts import redirect
from flask import Flask, render_template, request, redirect
from yt_dlp import YoutubeDL
import os
import requests
import sqlite3
import configparser
from pprint import pprint


# Initialize DB
def init_db(con):
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS yt (id INTEGER PRIMARY KEY AUTOINCREMENT, url VARCHAR(256), filename VARCHAR(256), playlist VARCHAR(256), status INTEGER)")
    con.commit()


# Get playlist list from azuracast api
def get_playlists():
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    data = requests.get(
        f"{config['azuracast_host']}/api/station/{config['station_id']}/playlists", headers=headers)

    playlists = [{"id": key["id"], "name": key["name"]} for key in data.json()]
    #playlists = ["Rickrolling", "Rick Astley", "Give UP!"]
    return playlists


# Create the flask app
app = Flask(__name__, static_url_path='/static')

# Connect the sqlite DB
con = sqlite3.connect("data.db")
init_db(con)


# Parse the config
parser = configparser.ConfigParser()
parser.read("config.ini")
config = parser["config"]


@app.route('/')
def index():
    return render_template('index.html.j2', playlists=get_playlists())

@app.route('/status')
def status():
    return render_template('status.html.j2')

@app.route('/download')
def download():
    url = request.args.get('url', default=None, type=str)
    if not url:
        return "Expected 1 parameter for 'url', got 0."

    ydl_opts = {
        'format': 'bestaudio[ext=mp3]/best',
        'writethumbnail': True,
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [
            {'key': 'FFmpegExtractAudio',
             'preferredcodec': 'mp3',
             'preferredquality': '192'},
            {'key': 'MetadataFromTitle',
             'titleformat': '(?P<title>.+)\ \-\ (?P<artist>.+)'},
            {'key': 'FFmpegMetadata'},
            {'key': 'EmbedThumbnail'}]}

    with YoutubeDL(ydl_opts) as ydl:
        path = ydl.download(url)
        print(path)

    return redirect("/")
