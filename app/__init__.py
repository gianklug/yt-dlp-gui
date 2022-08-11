from django.shortcuts import redirect
from flask import Flask, render_template, request, redirect
from yt_dlp import YoutubeDL
import os
import requests
import sqlite3
import configparser 
from pprint import pprint
# Create the flask app
app = Flask(__name__)

# Connect the sqlite DB
con = sqlite3.connect("data.db")

# Parse the config
parser = configparser.ConfigParser()
parser.read("config.ini")
config = parser["config"]

# Get playlist list from azuracast api
def get_playlists():
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    data = requests.get(f"{config['azuracast_host']}/api/station/{config['station_id']}/playlists", headers=headers)
    
    playlists = [{"id": key["id"], "name": key["name"]}  for key in data.json()]
    #playlists = ["Rickrolling", "Rick Astley", "Give UP!"]
    return playlists


@app.route('/')
def index():
    return render_template('index.html.j2', playlists=get_playlists())


@app.route('/download')
def download():
    url = request.args.get('url', default=None, type=str)
    if not url:
        return "Expected 1 parameter for 'url', got 0."

    ydl_opts = {
        'format': 'bestaudio[ext=mp3]/best',
        'writethumbnail': True,
        'outtmpl': '%(uploader)s - %(title)s.%(ext)s',
        'postprocessors': [
            {'key': 'FFmpegExtractAudio',
             'preferredcodec': 'mp3',
             'preferredquality': '192'},
            {'key': 'FFmpegMetadata', 'add_metadata': 'True'},
            {'key': 'EmbedThumbnail', }, ]}

    with YoutubeDL(ydl_opts) as ydl:
        path = ydl.download(url)
        print(path)

    return redirect("/")
