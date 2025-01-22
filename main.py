import os
import tempfile
import subprocess
import telebot
import k
keep_alive()
# تنظیم توکن ربات
TOKEN = "7735265225:AAFeWVHRcnAmgt8KdqbOdjhEmipRJHYXiW0"
bot = telebot.TeleBot(TOKEN)
bot.delete_my_commands()

def process_video(input_path, output_path):
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=min(iw\,ih):min(iw\,ih)",
            "-t", "60",
            "-fs", "49M",
            "-c:v", "libx264",
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
        # حذف پیام ویدیو از چت (بلافاصله پس از دریافت)
        bot.delete_message(message.chat.id, message.message_id)
        print("پیام ویدیو از چت حذف شد.")

        # دریافت اطلاعات ویدیو
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # ایجاد پوشه موقت
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.mp4")
            output_path = os.path.join(tmp_dir, "output.mp4")
            
            # ذخیره موقت ویدیو دانلود شده
            with open(input_path, 'wb') as f:
                f.write(downloaded_file)
            
            # پردازش ویدیو
            process_video(input_path, output_path)
            
            # ارسال به عنوان Video Note
            with open(output_path, 'rb') as video_note:
                bot.send_video_note(message.chat.id, video_note)
            
            # حذف فایلهای موقت
            os.remove(input_path)
            os.remove(output_path)
            print("فایلهای موقت با موفقیت حذف شدند.")
    
    except Exception as e:
        # ارسال پیام خطا بدون استفاده از reply_to
        bot.send_message(message.chat.id, f"خطا: {str(e)}")

# شروع ربات
if __name__ == "__main__":
    bot.polling()
