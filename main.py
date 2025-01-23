import os
import tempfile
import subprocess
import telebot
from telebot import types
from threading import Thread
from k import keep_alive

keep_alive()

TOKEN = "7735265225:AAFeWVHRcnAmgt8KdqbOdjhEmipRJHYXiW0"
bot = telebot.TeleBot(TOKEN)
bot.delete_my_commands()

# تنظیمات جوین اجباری
REQUIRED_CHANNEL = "@December0_3"  # یوزرنیم کانال خود را اینجا قرار دهید
CHANNEL_LINK = "https://t.me/December0_3"  # لینک کانال خود را اینجا قرار دهید

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
        bot.reply_to(message, "🎬 ویدیوی خود را ارسال کنید تا به Video Note تبدیل شود!")

def show_join_alert(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton("بررسی عضویت", callback_data="check"))
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, "❗️ برای استفاده از ربات باید در کانال ما عضو شوید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    if check_membership(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ عضویت شما تایید شد! لطفا ویدیو را ارسال کنید.")
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو نشدید!", show_alert=True)

def process_video(input_path, output_path):
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=min(iw\,ih):min(iw\,ih),scale=640:640",
            "-t", "60",
            "-fs", "1M",
            "-c:v", "libx264",
            "-preset", "superfast",  # استفاده از preset سریع‌تر
            "-crf", "30",  # افزایش CRF برای کاهش کیفیت و سرعت بیشتر
            "-c:a", "aac",
            "-y",
            output_path
        ]
        subprocess.run(command, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"خطا در پردازش: {e.stderr.decode()}")
        raise

def process_and_send_video(message):
    try:
        # حذف پیام کاربر
        bot.delete_message(message.chat.id, message.message_id)

        # ایجاد پوشه موقت
        with tempfile.TemporaryDirectory() as tmp_dir:
            # دانلود ویدیو
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # ذخیره موقت
            input_path = os.path.join(tmp_dir, "input.mp4")
            output_path = os.path.join(tmp_dir, "output.mp4")

            with open(input_path, 'wb') as f:
                f.write(downloaded_file)

            # پردازش ویدیو
            process_video(input_path, output_path)

            # ارسال نتیجه
            with open(output_path, 'rb') as video_note:
                bot.send_video_note(message.chat.id, video_note)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id

    if not check_membership(user_id):
        show_join_alert(message)
        return

    # ایجاد یک Thread جدید برای پردازش ویدیو
    Thread(target=process_and_send_video, args=(message,)).start()

if __name__ == "__main__":
    bot.polling()