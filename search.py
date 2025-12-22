import yt_dlp
import os

COOKIES_FILE = 'cookies.txt' # Ensure ye file folder me ho

def download_song(query):
    # Search and Download Options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s', # Downloads folder me save hoga
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'cookiefile': COOKIES_FILE,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Pehle info nikalo
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            # Ab Download karo
            print(f"⬇️ Downloading: {info['title']}")
            ydl.download([info['webpage_url']])
            
            # File Path (MP3 ban jayega)
            file_path = f"downloads/{info['id']}.mp3"
            
            return {
                "title": info['title'],
                "duration": info.get('duration_string', 'Unknown'),
                "thumb": info.get('thumbnail'),
                "path": file_path, # Ye path music_engine ko denge
                "url": info['webpage_url'],
                "channel": info.get('uploader')
            }
    except Exception as e:
        print(f"Download Error: {e}")
        return None
