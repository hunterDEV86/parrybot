import os
import uuid
import subprocess
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from k import keep_alive

keep_alive()
# توکن بات تلگرام
TOKEN = "7735265225:AAFeWVHRcnAmgt8KdqbOdjhEmipRJHYXiW0"
bot = telebot.TeleBot(TOKEN)

REQUIRED_CHANNEL = "@December0_3"
CHANNEL_LINK = "https://t.me/December0_3"
TEMP_DIR = "temp_videos"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# تنظیمات yt-dlp
def download_video(url):
    options = {
        'format': 'best',  # دانلود بهترین کیفیت موجود
        'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',  # مسیر ذخیره فایل دانلود شده
        'quiet': True,  # جلوگیری از نمایش پیام‌های اضافی
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)  # اطلاعات و دانلود
        return ydl.prepare_filename(info)  # بازگرداندن مسیر فایل

def check_membership(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    if not check_membership(message.from_user.id):
        show_join_alert(message)
    else:
        bot.reply_to(message, "👋 خوش آمدید! \n🎥 با ارسال لینک از یوتیوب، اینستاگرام یا تیک‌تاک، ویدیوی خود را دریافت کنید. \n🎬 همچنین می‌توانید ویدیوی خود را ارسال کنید تا به Video Note تبدیل شود. \n✨ لطفاً شروع کنید!")

def show_join_alert(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton("بررسی عضویت", callback_data="check"))
    bot.send_message(message.chat.id, "❗️ برای استفاده از ربات باید در کانال ما عضو شوید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    if check_membership(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ عضویت شما تایید شد! لطفا لینک یا ویدیو را ارسال کنید.")
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو نشدید!", show_alert=True)

def process_video(input_path, output_path):
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-vf', "crop='min(iw,ih)':'min(iw,ih)',scale=640:640,format=yuv420p",
            '-t', '60',
            '-c:v', 'libx264',
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-movflags', '+faststart',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-y',
            output_path
        ]

        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

    except subprocess.CalledProcessError as e:
        error_msg = f"""
        ⚠️ FFmpeg Error Details:
        Command: {e.cmd}
        Exit Code: {e.returncode}
        Output: {e.stdout}
        Error: {e.stderr}
        """
        raise Exception(error_msg)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id

    if not check_membership(user_id):
        show_join_alert(message)
        return

    try:
        processing_msg = bot.reply_to(message, "⏳ در حال پردازش ویدیو...")

        unique_id = str(uuid.uuid4())
        input_path = os.path.join(TEMP_DIR, f"input_{unique_id}.mp4")
        output_path = os.path.join(TEMP_DIR, f"output_{unique_id}.mp4")

        # دانلود ویدیو با بررسی صحت
        file_info = bot.get_file(message.video.file_id)
        if not file_info.file_path.endswith(('.mp4', '.MP4')):
            raise Exception("فرمت ویدیو پشتیبانی نمی‌شود!")

        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_path, 'wb') as f:
            f.write(downloaded_file)

        # بررسی وجود فایل ورودی
        if not os.path.exists(input_path):
            raise Exception("فایل ورودی دانلود نشد!")

        process_video(input_path, output_path)

        # بررسی وجود فایل خروجی
        if not os.path.exists(output_path):
            raise Exception("فایل خروجی ایجاد نشد!")

        with open(output_path, 'rb') as video_note:
            bot.send_video_note(message.chat.id, video_note)

        bot.delete_message(message.chat.id, processing_msg.message_id)
        os.remove(input_path)
        os.remove(output_path)

    except Exception as e:
        error_msg = f"""
        ❌ خطای سیستمی:
        {str(e)}
        """
        bot.reply_to(message, error_msg)
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    user_id = message.from_user.id

    if not check_membership(user_id):
        show_join_alert(message)
        return

    try:
        if any(domain in url for domain in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
            bot.reply_to(message, "در حال دانلود ویدیو، لطفاً صبر کنید...")
            file_path = download_video(url)

            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(file_path)
        else:
            bot.reply_to(message, "لینک ارسال شده معتبر نیست. لطفاً لینک یوتیوب، اینستاگرام یا تیک‌تاک ارسال کنید.")
    except Exception as e:
        bot.reply_to(message, f"متأسفم، مشکلی پیش آمد: {e}")

if __name__ == "__main__":
    bot.polling()
