import os
import sys
import json
import logging
import subprocess
import threading
import time
import signal
import queue
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Bot tokenini o'zgartiring
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"
ADMIN_ID = 8758410535

# Papkalar
UPLOAD_DIR = "uploads"
SCRIPTS_DIR = "scripts"
RESULTS_DIR = "results"
LOGS_DIR = "logs"

for dir_name in [UPLOAD_DIR, SCRIPTS_DIR, RESULTS_DIR, LOGS_DIR]:
    Path(dir_name).mkdir(exist_ok=True)

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ishga tushirilgan skriptlar
running_scripts = {}
script_processes = {}
script_input_queues = {}

user_data_file = "user_data.json"

def load_user_data():
    if os.path.exists(user_data_file):
        with open(user_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(user_data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_script_with_input(script_path, user_id, script_name, context):
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        script_key = f"{user_id}_{script_name}"
        script_processes[script_key] = process
        script_input_queues[script_key] = queue.Queue()
        
        running_scripts[script_key] = {
            "process": process,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "input_count": 0
        }
        
        log_file = Path(LOGS_DIR) / f"{user_id}_{script_name}.log"
        
        def input_handler():
            while True:
                try:
                    if process.poll() is not None:
                        break
                    try:
                        input_data = script_input_queues[script_key].get(timeout=0.1)
                        if input_data == "EXIT":
                            break
                        process.stdin.write(input_data + "\n")
                        process.stdin.flush()
                        running_scripts[script_key]["input_count"] += 1
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[INPUT] {input_data}\n")
                    except queue.Empty:
                        continue
                except Exception as e:
                    logger.error(f"Input handler error: {e}")
                    break
        
        def output_handler():
            while True:
                try:
                    if process.poll() is not None:
                        break
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[STDOUT] {stdout_line}")
                            f.flush()
                        try:
                            context.bot.send_message(
                                chat_id=int(user_id),
                                text=f"📤 *{script_name}* dan javob:\n```\n{stdout_line.strip()}\n```",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}")
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[STDERR] {stderr_line}")
                            f.flush()
                        try:
                            context.bot.send_message(
                                chat_id=int(user_id),
                                text=f"⚠️ *{script_name}* xatolik:\n```\n{stderr_line.strip()}\n```",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}")
                except Exception as e:
                    logger.error(f"Output handler error: {e}")
                    break
        
        input_thread = threading.Thread(target=input_handler, daemon=True)
        output_thread = threading.Thread(target=output_handler, daemon=True)
        input_thread.start()
        output_thread.start()
        
        process.wait()
        
        if script_key in running_scripts:
            running_scripts[script_key]["status"] = "stopped"
            running_scripts[script_key]["end_time"] = datetime.now().isoformat()
            try:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"⏹ *{script_name}* skripti to'xtadi!\nExit code: {process.returncode}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Telegram send error: {e}")
        
    except Exception as e:
        logger.error(f"Error running script {script_name}: {e}")
        script_key = f"{user_id}_{script_name}"
        if script_key in running_scripts:
            running_scripts[script_key]["status"] = "error"
            running_scripts[script_key]["error"] = str(e)
        try:
            context.bot.send_message(
                chat_id=int(user_id),
                text=f"❌ *{script_name}* skriptida xatolik:\n```\n{str(e)}\n```",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Telegram send error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "registered_at": datetime.now().isoformat(),
            "scripts": []
        }
        save_user_data(user_data)
    
    keyboard = [
        [InlineKeyboardButton("📤 Skript yuborish", callback_data="upload_script")],
        [InlineKeyboardButton("📋 Skriptlarim", callback_data="my_scripts")],
        [InlineKeyboardButton("▶️ Skriptni ishga tushirish", callback_data="run_script")],
        [InlineKeyboardButton("📤 Ma'lumot yuborish", callback_data="send_input")],
        [InlineKeyboardButton("⏹ Skriptni to'xtatish", callback_data="stop_script")],
        [InlineKeyboardButton("📊 Holatni tekshirish", callback_data="check_status")],
        [InlineKeyboardButton("📄 Log faylni ko'rish", callback_data="view_log")],
        [InlineKeyboardButton("❌ Skriptni o'chirish", callback_data="delete_script")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        f"Men sizga Python skriptlarni **24/7** ishga tushirish va\n"
        f"ularga **jonli ma'lumot** yuborishda yordam beraman.\n\n"
        f"📌 Quyidagi tugmalar orqali ishlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if query.data == "upload_script":
        await query.edit_message_text(
            "📤 Iltimos, Python skript faylingizni (.py) yuboring.\n\n"
            "⚠️ Fayl nomi ingliz tilida va probelsiz bo'lishi kerak.\n"
            "💡 Skript `input()` yoki `sys.stdin.read()` orqali ma'lumot qabul qilishi kerak."
        )
        context.user_data['waiting_for_script'] = True
        
    elif query.data == "my_scripts":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            scripts = user_data[user_id]["scripts"]
            text = "📋 Sizning skriptlaringiz:\n\n"
            for i, script in enumerate(scripts, 1):
                status = "🟢" if f"{user_id}_{script}" in running_scripts and running_scripts[f"{user_id}_{script}"]["status"] == "running" else "🔴"
                text += f"{i}. {status} {script}\n"
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("❌ Sizda hali skriptlar mavjud emas.")
            
    elif query.data == "run_script":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                if f"{user_id}_{script}" not in running_scripts or running_scripts[f"{user_id}_{script}"]["status"] != "running":
                    keyboard.append([InlineKeyboardButton(f"▶️ {script}", callback_data=f"run_{script}")])
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Barcha skriptlar ishlayapti", callback_data="none")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("▶️ Ishga tushirmoqchi bo'lgan skriptni tanlang:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Sizda skriptlar mavjud emas.")
            
    elif query.data.startswith("run_"):
        script_name = query.data.replace("run_", "")
        script_path = Path(SCRIPTS_DIR) / user_id / script_name
        if script_path.exists():
            if f"{user_id}_{script_name}" in running_scripts and running_scripts[f"{user_id}_{script_name}"]["status"] == "running":
                await query.edit_message_text("⚠️ Bu skript allaqachon ishlayapti!")
                return
            await query.edit_message_text(f"⏳ {script_name} ishga tushirilmoqda...")
            thread = threading.Thread(
                target=run_script_with_input,
                args=(script_path, user_id, script_name, context),
                daemon=True
            )
            thread.start()
            await query.message.reply_text(
                f"✅ {script_name} muvaffaqiyatli ishga tushdi!\n\n"
                f"🔄 Skript 24/7 ishlaydi va ma'lumot qabul qiladi\n"
                f"📤 Ma'lumot yuborish uchun 'Ma'lumot yuborish' tugmasini bosing\n"
                f"📊 Log fayl: {LOGS_DIR}/{user_id}_{script_name}.log"
            )
        else:
            await query.edit_message_text("❌ Skript topilmadi!")
            
    elif query.data == "send_input":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                if f"{user_id}_{script}" in running_scripts and running_scripts[f"{user_id}_{script}"]["status"] == "running":
                    keyboard.append([InlineKeyboardButton(f"📤 {script}", callback_data=f"input_{script}")])
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Ishlamayotgan skriptlar", callback_data="none")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📤 Qaysi skriptga ma'lumot yubormoqchisiz?", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Sizda skriptlar mavjud emas.")
            
    elif query.data.startswith("input_"):
        script_name = query.data.replace("input_", "")
        context.user_data['input_script'] = script_name
        context.user_data['waiting_for_input'] = True
        await query.edit_message_text(
            f"📤 *{script_name}* skriptiga ma'lumot yuborish.\n\n"
            f"💬 Iltimos, yubormoqchi bo'lgan ma'lumotni matn sifatida yozing.\n"
            f"⏹ Bekor qilish uchun /cancel buyrug'ini yozing.",
            parse_mode="Markdown"
        )
        
    elif query.data == "stop_script":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                if f"{user_id}_{script}" in running_scripts and running_scripts[f"{user_id}_{script}"]["status"] == "running":
                    keyboard.append([InlineKeyboardButton(f"⏹ {script}", callback_data=f"stop_{script}")])
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Ishlamayotgan skriptlar", callback_data="none")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⏹ To'xtatmoqchi bo'lgan skriptni tanlang:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Sizda skriptlar mavjud emas.")
            
    elif query.data.startswith("stop_"):
        script_name = query.data.replace("stop_", "")
        script_key = f"{user_id}_{script_name}"
        if script_key in running_scripts:
            process = running_scripts[script_key]["process"]
            try:
                process.terminate()
                running_scripts[script_key]["status"] = "stopped"
                running_scripts[script_key]["end_time"] = datetime.now().isoformat()
                if script_key in script_input_queues:
                    script_input_queues[script_key].put("EXIT")
                await query.edit_message_text(f"⏹ {script_name} to'xtatildi!")
            except Exception as e:
                await query.edit_message_text(f"❌ Xatolik: {str(e)}")
        else:
            await query.edit_message_text("❌ Skript ishlamayapti!")
            
    elif query.data == "check_status":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            text = "📊 **Skriptlar holati:**\n\n"
            for script in user_data[user_id]["scripts"]:
                key = f"{user_id}_{script}"
                if key in running_scripts:
                    status = running_scripts[key]
                    emoji = "🟢" if status["status"] == "running" else "🔴"
                    text += f"{emoji} **{script}**\n"
                    text += f"   ⏱ Boshlangan: {status['start_time']}\n"
                    text += f"   📤 Qabul qilingan ma'lumotlar: {status.get('input_count', 0)}\n"
                    if status["status"] != "running":
                        text += f"   ⏹ Tugagan: {status.get('end_time', 'N/A')}\n"
                    if status["status"] == "error":
                        text += f"   ❌ Xatolik: {status.get('error', 'N/A')}\n"
                else:
                    text += f"⚪ **{script}** - ishlamayapti\n"
                text += "\n"
            await query.edit_message_text(text, parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Sizda skriptlar mavjud emas.")
            
    elif query.data == "view_log":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                log_file = Path(LOGS_DIR) / f"{user_id}_{script}.log"
                if log_file.exists():
                    keyboard.append([InlineKeyboardButton(f"📄 {script}", callback_data=f"log_{script}")])
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Log fayllar mavjud emas", callback_data="none")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📄 Log faylini ko'rmoqchi bo'lgan skriptni tanlang:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Sizda skriptlar mavjud emas.")
            
    elif query.data.startswith("log_"):
        script_name = query.data.replace("log_", "")
        log_file = Path(LOGS_DIR) / f"{user_id}_{script_name}.log"
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) > 4000:
                content = content[-4000:] + "\n\n... (oxirgi 4000 belgi)"
            await query.edit_message_text(f"📄 **{script_name} log fayli:**\n\n```\n{content}\n```", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Log fayl topilmadi!")
            
    elif query.data == "delete_script":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                keyboard.append([InlineKeyboardButton(f"❌ {script}", callback_data=f"del_{script}")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🗑 O'chirmoqchi bo'lgan skriptni tanlang:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Sizda skriptlar mavjud emas.")
            
    elif query.data.startswith("del_"):
        script_name = query.data.replace("del_", "")
        script_key = f"{user_id}_{script_name}"
        if script_key in running_scripts and running_scripts[script_key]["status"] == "running":
            try:
                process = running_scripts[script_key]["process"]
                process.terminate()
                if script_key in script_input_queues:
                    script_input_queues[script_key].put("EXIT")
            except:
                pass
        script_path = Path(SCRIPTS_DIR) / user_id / script_name
        if script_path.exists():
            script_path.unlink()
            log_file = Path(LOGS_DIR) / f"{user_id}_{script_name}.log"
            if log_file.exists():
                log_file.unlink()
            user_data = load_user_data()
            if user_id in user_data and script_name in user_data[user_id]["scripts"]:
                user_data[user_id]["scripts"].remove(script_name)
                save_user_data(user_data)
            if script_key in running_scripts:
                del running_scripts[script_key]
            if script_key in script_input_queues:
                del script_input_queues[script_key]
            await query.edit_message_text(f"✅ {script_name} o'chirildi!")
        else:
            await query.edit_message_text("❌ Skript topilmadi!")
            
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ **Yordam**\n\n"
            "📤 **Skript yuborish** - Python faylini yuklash\n"
            "📋 **Skriptlarim** - Barcha skriptlar ro'yxati\n"
            "▶️ **Skriptni ishga tushirish** - Skriptni 24/7 ishga tushirish\n"
            "📤 **Ma'lumot yuborish** - Ishlayotgan skriptga ma'lumot yuborish\n"
            "⏹ **Skriptni to'xtatish** - Ishlamoqda bo'lgan skriptni to'xtatish\n"
            "📊 **Holatni tekshirish** - Skriptlar holatini ko'rish\n"
            "📄 **Log faylni ko'rish** - Skript loglarini o'qish\n"
            "❌ **Skriptni o'chirish** - Skriptni o'chirib tashlash\n\n"
            "⚠️ **Muhim:**\n"
            "• Skriptlar `input()` yoki `sys.stdin.read()` orqali ma'lumot qabul qilishi kerak\n"
            "• Ma'lumotlar jonli ravishda skriptga uzatiladi\n"
            "• Skript javoblari Telegramga jonli yuboriladi",
            parse_mode="Markdown"
        )
        
    elif query.data == "back_to_menu":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    if message_text == "/cancel":
        context.user_data['waiting_for_input'] = False
        context.user_data['input_script'] = None
        await update.message.reply_text("⏹ Ma'lumot yuborish bekor qilindi.")
        return
    
    if context.user_data.get('waiting_for_input'):
        script_name = context.user_data.get('input_script')
        if not script_name:
            await update.message.reply_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
            return
        
        script_key = f"{user_id}_{script_name}"
        if script_key not in script_input_queues:
            await update.message.reply_text("❌ Skript ishlamayapti yoki topilmadi!")
            return
        
        try:
            script_input_queues[script_key].put(message_text)
            await update.message.reply_text(
                f"✅ Ma'lumot *{script_name}* skriptiga yuborildi!\n\n"
                f"📤 Yuborilgan: `{message_text}`",
                parse_mode="Markdown"
            )
            if script_key in running_scripts:
                running_scripts[script_key]["input_count"] = running_scripts[script_key].get("input_count", 0) + 1
            context.user_data['waiting_for_input'] = True
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    else:
        await update.message.reply_text(
            "ℹ️ Men faqat skriptlarga ma'lumot yuborish uchun xizmat qilaman.\n"
            "📌 Iltimos, /start buyrug'ini bosing yoki tugmalardan foydalaning."
        )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_script'):
        await update.message.reply_text("❌ Iltimos, avval 'Skript yuborish' tugmasini bosing.")
        return
    
    document = update.message.document
    if not document or not document.file_name.endswith('.py'):
        await update.message.reply_text("❌ Iltimos, faqat .py fayllarni yuboring!")
        return
    
    user_id = str(update.effective_user.id)
    file_name = document.file_name
    
    user_script_dir = Path(SCRIPTS_DIR) / user_id
    user_script_dir.mkdir(exist_ok=True)
    file_path = user_script_dir / file_name
    
    try:
        file = await document.get_file()
        await file.download_to_drive(file_path)
        user_data = load_user_data()
        if user_id in user_data:
            if file_name not in user_data[user_id]["scripts"]:
                user_data[user_id]["scripts"].append(file_name)
                save_user_data(user_data)
        context.user_data['waiting_for_script'] = False
        await update.message.reply_text(
            f"✅ {file_name} muvaffaqiyatli yuklandi!\n\n"
            f"📊 Skript hajmi: {document.file_size} bayt\n"
            f"▶️ Endi skriptni ishga tushirishingiz mumkin."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Bot haqida**\n\n"
        "Bu bot Python skriptlarni 24/7 ishga tushirish va\n"
        "ularga jonli ma'lumot yuborish uchun yaratilgan.\n\n"
        "📌 **Buyruqlar:**\n"
        "/start - Boshlash\n"
        "/help - Yordam\n"
        "/cancel - Ma'lumot yuborishni bekor qilish",
        parse_mode="Markdown"
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    print("🤖 Bot 24/7 ishga tushdi...")
    print(f"📁 Skriptlar papkasi: {SCRIPTS_DIR}")
    print(f"📁 Loglar papkasi: {LOGS_DIR}")
    print("📤 Skriptlarga ma'lumot yuborish tayyor!")
    application.run_polling()

if __name__ == "__main__":
    main()
