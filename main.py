import os
import tempfile
import subprocess
import telebot
from k import keep_alive
from telebot import types

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
    except Exception as e:
        print(f"خطا در بررسی عضویت: {str(e)}")
        return False

@bot.message_handler(commands=['start'])
def start(message):
    if not check_membership(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("بررسی عضویت", callback_data="check"))
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "❗️ برای استفاده از ربات باید در کانال ما عضو شوید:", reply_markup=markup)
    else:
        bot.reply_to(message, "سلام! ویدیو مورد نظر خود را ارسال کنید تا به ویدیو مسیج تبدیل شود.")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "check":
        if check_membership(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ عضویت شما تایید شد! لطفا ویدیو را ارسال کنید.")
        else:
            bot.answer_callback_query(call.id, "❌ هنوز در کانال عضو نشدید!", show_alert=True)

def process_video(input_path, output_path):
    # همان تابع پردازش ویدیو قبلی
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=min(iw\,ih):min(iw\,ih),scale=640:640",
            "-t", "60",
            "-fs", "1M",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "28",
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
    if not check_membership(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("بررسی عضویت", callback_data="check"))
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "❗️ برای استفاده از ربات باید در کانال ما عضو شوید:", reply_markup=markup)
        return

    try:
        # کد اصلی پردازش ویدیو
        bot.delete_message(message.chat.id, message.message_id)
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.mp4")
            output_path = os.path.join(tmp_dir, "output.mp4")
            
            with open(input_path, 'wb') as f:
                f.write(downloaded_file)
            
            process_video(input_path, output_path)
            
            if not os.path.exists(output_path):
                raise Exception("فایل خروجی ایجاد نشد.")
            
            with open(output_path, 'rb') as video_note:
                bot.send_video_note(message.chat.id, video_note)
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

if __name__ == "__main__":
    bot.polling()
