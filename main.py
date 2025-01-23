import os
import tempfile
import subprocess
import telebot
from telebot import types
from k import keep_alive

keep_alive()

TOKEN = "7735265225:AAFeWVHRcnAmgt8KdqbOdjhEmipRJHYXiW0"
bot = telebot.TeleBot(TOKEN)
bot.delete_my_commands()

# تنظیمات جوین اجباری
REQUIRED_CHANNEL = "@December0_3"
CHANNEL_LINK = "https://t.me/December0_3"

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

def process_video(input_path, output_path, message):
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=min(iw\,ih):min(iw\,ih),scale=640:640",
            "-t", "60",  # محدودیت مدت زمان
            "-fs", "1M",  # محدودیت حجم فایل
            "-c:v", "libx264",
            "-preset", "superfast",  # استفاده از preset سریع‌تر
            "-crf", "30",  # افزایش CRF برای کاهش کیفیت و سرعت بیشتر
            "-an",  # حذف صدا
            "-y",
            output_path
        ]
        process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

        # ارسال پیام اولیه برای Progress Bar
        progress_message = bot.send_message(message.chat.id, "🔄 در حال پردازش ویدیو...\n[░░░░░░░░░░] 0%")
        last_percentage = 0  # ذخیره آخرین درصد پیشرفت

        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if "time=" in output:
                # استخراج زمان پیشرفت از خروجی FFmpeg
                time_str = output.split("time=")[1].split(" ")[0]
                h, m, s = map(float, time_str.split(':'))
                total_seconds = h * 3600 + m * 60 + s
                progress = min(total_seconds / 60, 1.0)  # محدودیت مدت زمان 60 ثانیه
                percentage = int(progress * 100)

                # فقط اگر درصد تغییر کرده باشد، پیام را به‌روزرسانی کنید
                if percentage != last_percentage:
                    bar_length = 10
                    filled_length = int(bar_length * progress)
                    bar = "[" + "█" * filled_length + "░" * (bar_length - filled_length) + "]"
                    try:
                        bot.edit_message_text(
                            f"🔄 در حال پردازش ویدیو...\n{bar} {percentage}%",
                            chat_id=progress_message.chat.id,
                            message_id=progress_message.message_id
                        )
                        last_percentage = percentage  # به‌روزرسانی آخرین درصد
                    except telebot.apihelper.ApiTelegramException as e:
                        if "message is not modified" not in str(e):
                            raise  # اگر خطا مربوط به تغییر نکردن پیام نباشد، آن را پرتاب کنید

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

        # پس از اتمام پردازش، Progress Bar را به 100% برسانید
        bot.edit_message_text(
            "✅ پردازش ویدیو کامل شد! در حال ارسال ویدیو...",
            chat_id=progress_message.chat.id,
            message_id=progress_message.message_id
        )

    except subprocess.CalledProcessError as e:
        print(f"خطا در پردازش: {e.stderr}")
        raise

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id

    if not check_membership(user_id):
        show_join_alert(message)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            input_path = os.path.join(tmp_dir, "input.mp4")
            output_path = os.path.join(tmp_dir, "output.mp4")

            with open(input_path, 'wb') as f:
                f.write(downloaded_file)

            process_video(input_path, output_path, message)

            with open(output_path, 'rb') as video_note:
                bot.send_video_note(message.chat.id, video_note)

            # ارسال پیام تأیید نهایی
            bot.send_message(message.chat.id, "🎉 ویدیو با موفقیت ارسال شد!")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا: {str(e)}")

if __name__ == "__main__":
    bot.polling()