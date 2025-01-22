import os
import tempfile
import subprocess
import telebot
from k import keep_alive

keep_alive()

TOKEN = "7735265225:AAFeWVHRcnAmgt8KdqbOdjhEmipRJHYXiW0"
bot = telebot.TeleBot(TOKEN)
bot.delete_my_commands()

def process_video(input_path, output_path):
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=min(iw\,ih):min(iw\,ih),scale=640:640",  # تبدیل به مربع 640x640
            "-t", "60",  # محدودیت مدت زمان به 60 ثانیه
            "-fs", "1M",  # محدودیت حجم فایل به 1 مگابایت (حداکثر مجاز برای Video Note)
            "-c:v", "libx264",
            "-preset", "fast",  # افزایش سرعت پردازش
            "-crf", "28",  # کاهش کیفیت برای کوچک کردن حجم
            "-c:a", "aac",
            "-y",
            output_path
        ]
        subprocess.run(command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"خطا در پردازش ویدیو: {e.stderr.decode()}")
        raise

@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        # حذف پیام ویدیو از چت
        bot.delete_message(message.chat.id, message.message_id)

        # دریافت ویدیو
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.mp4")
            output_path = os.path.join(tmp_dir, "output.mp4")
            
            # ذخیره موقت ویدیو
            with open(input_path, 'wb') as f:
                f.write(downloaded_file)
            
            # پردازش ویدیو
            process_video(input_path, output_path)
            
            # بررسی وجود فایل خروجی
            if not os.path.exists(output_path):
                raise Exception("فایل خروجی ایجاد نشد.")
            
            # ارسال به عنوان Video Note
            with open(output_path, 'rb') as video_note:
                bot.send_video_note(message.chat.id, video_note)
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

if __name__ == "__main__":
    bot.polling()
