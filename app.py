from flask import Flask, request, jsonify
import os
import uuid
import requests
from moviepy import TextClip, VideoFileClip, CompositeVideoClip
from datetime import datetime, timedelta
import threading

app = Flask(__name__)
TEMP_DIR = "temp"
FONT_PATH = "fonts/Shabnam.ttf"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs("fonts", exist_ok=True)

def delete_file_after(file_path, delay_minutes=1):
    def delete_file():
        now = datetime.now()
        delete_time = now + timedelta(minutes=delay_minutes)
        while datetime.now() < delete_time:
            continue
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    thread = threading.Thread(target=delete_file)
    thread.start()

@app.route('/')
def index():
    return "Video Text Adder Service"

@app.route('/process', methods=['GET'])
def process_video():
    video_url = request.args.get('videourl')
    text = request.args.get('text')
    
    if not video_url or not text:
        return jsonify({"status": 400, "error": "Missing videourl or text parameter"}), 400
    
    try:
        # دانلود ویدیو
        video_id = str(uuid.uuid4())
        input_path = os.path.join(TEMP_DIR, f"input_{video_id}.mp4")
        output_path = os.path.join(TEMP_DIR, f"output_{video_id}.mp4")
        
        # دانلود ویدیو از URL
        response = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        # پردازش ویدیو و افزودن متن با فونت Shabnam
        video = VideoFileClip(input_path)
        
        txt_clip = (TextClip(text, fontsize=30, font=FONT_PATH, color='white',
                    stroke_color='black', stroke_width=1.5)
                   .set_position(('center', 'bottom'))
                   .set_duration(video.duration))
        
        final = CompositeVideoClip([video, txt_clip])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac', threads=4)
        
        # حذف فایل موقت ورودی
        os.remove(input_path)
        
        # تنظیم حذف خودکار پس از 1 دقیقه
        delete_file_after(output_path, 1)
        
        # تولید لینک نتیجه
        result_url = f"https://{request.host}/temp/output_{video_id}.mp4"
        
        return jsonify({
            "status": 200,
            "result": result_url
        })
    
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": str(e)
        }), 500

@app.route('/temp/<filename>')
def serve_temp_file(filename):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        return app.send_file(file_path, as_attachment=True)
    else:
        return "File not found or expired", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
