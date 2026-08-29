import os
import sys
import json
import logging
import subprocess
import threading
import time
import queue
import shlex
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Bot tokeni
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"

# Papkalar
SCRIPTS_DIR = "scripts"
LOGS_DIR = "logs"
VENV_DIR = "venvs"  # Har bir foydalanuvchi uchun virtual environment

for dir_name in [SCRIPTS_DIR, LOGS_DIR, VENV_DIR]:
    Path(dir_name).mkdir(exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

running_scripts = {}
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

def get_python_path(user_id):
    """Foydalanuvchi uchun python path"""
    venv_path = Path(VENV_DIR) / user_id
    if venv_path.exists():
        if os.name == 'nt':  # Windows
            python_path = venv_path / "Scripts" / "python.exe"
        else:  # Linux/Mac
            python_path = venv_path / "bin" / "python"
        if python_path.exists():
            return str(python_path)
    return sys.executable

def install_requirements(user_id, script_path):
    """Requirements.txt ni o'rnatish"""
    try:
        req_file = script_path.parent / "requirements.txt"
        if req_file.exists():
            python_path = get_python_path(user_id)
            result = subprocess.run(
                [python_path, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)
    return True, "No requirements", ""

def run_script_universal(script_path, user_id, script_name, context):
    """Har qanday skriptni ishga tushirish"""
    try:
        # Python path
        python_path = get_python_path(user_id)
        
        # Skriptni ishga tushirish
        process = subprocess.Popen(
            [python_path, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(script_path.parent)  # Skript papkasida ishlash
        )
        
        script_key = f"{user_id}_{script_name}"
        script_input_queues[script_key] = queue.Queue()
        
        running_scripts[script_key] = {
            "process": process,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "input_count": 0
        }
        
        log_file = Path(LOGS_DIR) / f"{user_id}_{script_name}.log"
        
        # Input handler
        def input_handler():
            while process.poll() is None:
                try:
                    input_data = script_input_queues[script_key].get(timeout=0.5)
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
                    logger.error(f"Input error: {e}")
                    break
        
        # Output handler
        def output_handler():
            while process.poll() is None:
                try:
                    # Stdout
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[STDOUT] {stdout_line}")
                            f.flush()
                        
                        # Telegramga yuborish
                        try:
                            context.bot.send_message(
                                chat_id=int(user_id),
                                text=f"📤 *{script_name}*:\n```\n{stdout_line.strip()[:1000]}\n```",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}")
                    
                    # Stderr
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[STDERR] {stderr_line}")
                            f.flush()
                        
                        try:
                            context.bot.send_message(
                                chat_id=int(user_id),
                                text=f"⚠️ *{script_name}* xatolik:\n```\n{stderr_line.strip()[:1000]}\n```",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}")
                            
                except Exception as e:
                    logger.error(f"Output error: {e}")
                    break
        
        # Threadlarni ishga tushirish
        input_thread = threading.Thread(target=input_handler, daemon=True)
        output_thread = threading.Thread(target=output_handler, daemon=True)
        input_thread.start()
        output_thread.start()
        
        # Process tugashini kutish
        process.wait()
        
        # Statusni yangilash
        if script_key in running_scripts:
            running_scripts[script_key]["status"] = "stopped"
            running_scripts[script_key]["end_time"] = datetime.now().isoformat()
            
            try:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"⏹ *{script_name}* to'xtadi!\nExit code: {process.returncode}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Telegram send error: {e}")
        
        if script_key in script_input_queues:
            del script_input_queues[script_key]
            
    except Exception as e:
        logger.error(f"Script error {script_name}: {e}")
        script_key = f"{user_id}_{script_name}"
        if script_key in running_scripts:
            running_scripts[script_key]["status"] = "error"
            running_scripts[script_key]["error"] = str(e)
        
        try:
            context.bot.send_message(
                chat_id=int(user_id),
                text=f"❌ *{script_name}* xatolik:\n```\n{str(e)}\n```",
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
            "registered_at": datetime.now().isoformat(),
            "scripts": []
        }
        save_user_data(user_data)
    
    keyboard = [
        [InlineKeyboardButton("📤 Skript yuborish", callback_data="upload_script")],
        [InlineKeyboardButton("📦 Requirements.txt", callback_data="upload_requirements")],
        [InlineKeyboardButton("📋 Skriptlarim", callback_data="my_scripts")],
        [InlineKeyboardButton("▶️ Ishga tushirish", callback_data="run_script")],
        [InlineKeyboardButton("📤 Ma'lumot yuborish", callback_data="send_input")],
        [InlineKeyboardButton("⏹ To'xtatish", callback_data="stop_script")],
        [InlineKeyboardButton("📊 Holat", callback_data="check_status")],
        [InlineKeyboardButton("📄 Log", callback_data="view_log")],
        [InlineKeyboardButton("🔧 Venv yaratish", callback_data="create_venv")],
        [InlineKeyboardButton("❌ O'chirish", callback_data="delete_script")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        f"🤖 **Universal Script Bot**\n"
        f"✅ Har qanday skriptni ishga tushiraman\n"
        f"✅ Termux, server, hamma joyda ishlaydi\n"
        f"✅ Requirements.txt ni o'rnataman\n\n"
        f"📌 Tugmalardan foydalaning:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if query.data == "upload_script":
        await query.edit_message_text(
            "📤 Python skript faylingizni (.py) yuboring.\n\n"
            "✅ Har qanday skript ishlaydi\n"
            "✅ Termux, server, hamma joyda\n"
            "⚠️ Fayl nomi ingliz tilida bo'lsin"
        )
        context.user_data['waiting_for_script'] = True
    
    elif query.data == "upload_requirements":
        await query.edit_message_text(
            "📦 `requirements.txt` faylini yuboring.\n\n"
            "✅ Avtomatik o'rnatiladi\n"
            "✅ Skript bilan birga ishlaydi"
        )
        context.user_data['waiting_for_requirements'] = True
    
    elif query.data == "create_venv":
        await query.edit_message_text("🔧 Virtual environment yaratilmoqda...")
        
        venv_path = Path(VENV_DIR) / user_id
        if not venv_path.exists():
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                await query.edit_message_text("✅ Virtual environment yaratildi!")
            except Exception as e:
                await query.edit_message_text(f"❌ Xatolik: {str(e)}")
        else:
            await query.edit_message_text("ℹ️ Virtual environment allaqachon mavjud")
    
    elif query.data == "my_scripts":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            scripts = user_data[user_id]["scripts"]
            text = "📋 Skriptlaringiz:\n\n"
            for i, script in enumerate(scripts, 1):
                key = f"{user_id}_{script}"
                status = "🟢" if key in running_scripts and running_scripts[key]["status"] == "running" else "🔴"
                text += f"{i}. {status} {script}\n"
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data == "run_script":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                key = f"{user_id}_{script}"
                if key not in running_scripts or running_scripts[key]["status"] != "running":
                    keyboard.append([InlineKeyboardButton(f"▶️ {script}", callback_data=f"run_{script}")])
            
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Hammasi ishlayapti", callback_data="none")])
            
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("▶️ Tanlang:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data.startswith("run_"):
        script_name = query.data.replace("run_", "")
        script_path = Path(SCRIPTS_DIR) / user_id / script_name
        
        if not script_path.exists():
            await query.edit_message_text("❌ Skript topilmadi!")
            return
        
        key = f"{user_id}_{script_name}"
        if key in running_scripts and running_scripts[key]["status"] == "running":
            await query.edit_message_text("⚠️ Skript ishlayapti!")
            return
        
        await query.edit_message_text(f"⏳ {script_name} ishga tushirilmoqda...")
        
        # Requirements ni o'rnatish
        req_installed, req_out, req_err = install_requirements(user_id, script_path)
        if not req_installed:
            await query.message.reply_text(
                f"⚠️ Requirements o'rnatishda xatolik:\n```\n{req_err}\n```",
                parse_mode="Markdown"
            )
        
        # Skriptni ishga tushirish
        thread = threading.Thread(
            target=run_script_universal,
            args=(script_path, user_id, script_name, context),
            daemon=True
        )
        thread.start()
        
        await query.message.reply_text(
            f"✅ *{script_name}* ishga tushdi!\n\n"
            f"📤 Ma'lumot yuborish uchun 'Ma'lumot yuborish' tugmasini bosing.",
            parse_mode="Markdown"
        )
    
    elif query.data == "send_input":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                key = f"{user_id}_{script}"
                if key in running_scripts and running_scripts[key]["status"] == "running":
                    keyboard.append([InlineKeyboardButton(f"📤 {script}", callback_data=f"input_{script}")])
            
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Ishlamayotgan skriptlar", callback_data="none")])
            
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📤 Qaysi skriptga ma'lumot yuboramiz?", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data.startswith("input_"):
        script_name = query.data.replace("input_", "")
        context.user_data['input_script'] = script_name
        context.user_data['waiting_for_input'] = True
        await query.edit_message_text(
            f"📤 *{script_name}* ga ma'lumot yozing:\n\n"
            f"💬 Matn yozib yuboring.\n"
            f"⏹ Bekor: /cancel",
            parse_mode="Markdown"
        )
    
    elif query.data == "stop_script":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                key = f"{user_id}_{script}"
                if key in running_scripts and running_scripts[key]["status"] == "running":
                    keyboard.append([InlineKeyboardButton(f"⏹ {script}", callback_data=f"stop_{script}")])
            
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Ishlamayotgan skriptlar", callback_data="none")])
            
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⏹ Qaysi skriptni to'xtatamiz?", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data.startswith("stop_"):
        script_name = query.data.replace("stop_", "")
        key = f"{user_id}_{script_name}"
        
        if key not in running_scripts:
            await query.edit_message_text("❌ Skript ishlamayapti!")
            return
        
        try:
            process = running_scripts[key]["process"]
            process.terminate()
            process.wait(timeout=5)
            running_scripts[key]["status"] = "stopped"
            running_scripts[key]["end_time"] = datetime.now().isoformat()
            
            if key in script_input_queues:
                script_input_queues[key].put("EXIT")
            
            await query.edit_message_text(f"⏹ *{script_name}* to'xtatildi!", parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Xatolik: {str(e)}")
    
    elif query.data == "check_status":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            text = "📊 **Holat:**\n\n"
            for script in user_data[user_id]["scripts"]:
                key = f"{user_id}_{script}"
                if key in running_scripts:
                    status = running_scripts[key]
                    emoji = "🟢" if status["status"] == "running" else "🔴"
                    text += f"{emoji} *{script}*\n"
                    text += f"   📤 Input: {status.get('input_count', 0)}\n"
                    text += f"   ⏱ Boshlangan: {status['start_time'][:19]}\n"
                    if status["status"] != "running":
                        text += f"   ⏹ Tugagan: {status.get('end_time', 'N/A')[:19]}\n"
                else:
                    text += f"⚪ *{script}* - ishlamayapti\n"
                text += "\n"
            await query.edit_message_text(text, parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data == "view_log":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                log_file = Path(LOGS_DIR) / f"{user_id}_{script}.log"
                if log_file.exists():
                    keyboard.append([InlineKeyboardButton(f"📄 {script}", callback_data=f"log_{script}")])
            
            if not keyboard:
                keyboard.append([InlineKeyboardButton("ℹ️ Loglar mavjud emas", callback_data="none")])
            
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📄 Qaysi skript logini ko'ramiz?", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data.startswith("log_"):
        script_name = query.data.replace("log_", "")
        log_file = Path(LOGS_DIR) / f"{user_id}_{script_name}.log"
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) > 4000:
                content = content[-4000:] + "\n\n... (oxirgi 4000 belgi)"
            await query.edit_message_text(
                f"📄 *{script_name}* log:\n\n```\n{content}\n```",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Log topilmadi!")
    
    elif query.data == "delete_script":
        user_data = load_user_data()
        if user_id in user_data and user_data[user_id]["scripts"]:
            keyboard = []
            for script in user_data[user_id]["scripts"]:
                keyboard.append([InlineKeyboardButton(f"❌ {script}", callback_data=f"del_{script}")])
            keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🗑 Qaysi skriptni o'chiramiz?", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Skriptlar mavjud emas.")
    
    elif query.data.startswith("del_"):
        script_name = query.data.replace("del_", "")
        key = f"{user_id}_{script_name}"
        
        if key in running_scripts and running_scripts[key]["status"] == "running":
            try:
                process = running_scripts[key]["process"]
                process.terminate()
                process.wait(timeout=5)
                if key in script_input_queues:
                    script_input_queues[key].put("EXIT")
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
            
            if key in running_scripts:
                del running_scripts[key]
            if key in script_input_queues:
                del script_input_queues[key]
            
            await query.edit_message_text(f"✅ *{script_name}* o'chirildi!", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Skript topilmadi!")
    
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ **Yordam**\n\n"
            "📤 **Skript yuborish** - .py faylni yuklash\n"
            "📦 **Requirements.txt** - Kutubxonalarni o'rnatish\n"
            "📋 **Skriptlarim** - Ro'yxat\n"
            "▶️ **Ishga tushirish** - 24/7 ishlatish\n"
            "📤 **Ma'lumot yuborish** - Jonli ma'lumot\n"
            "⏹ **To'xtatish** - Skriptni o'chirish\n"
            "📊 **Holat** - Qaysi skript ishlayapti\n"
            "📄 **Log** - Chiqishlarni ko'rish\n"
            "🔧 **Venv** - Virtual environment yaratish\n"
            "❌ **O'chirish** - Skriptni o'chirish\n\n"
            "✅ Har qanday skript ishlaydi!\n"
            "✅ Termux, server, hamma joyda!",
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
        await update.message.reply_text("⏹ Bekor qilindi.")
        return
    
    if context.user_data.get('waiting_for_input'):
        script_name = context.user_data.get('input_script')
        if not script_name:
            await update.message.reply_text("❌ Xatolik!")
            return
        
        key = f"{user_id}_{script_name}"
        if key not in script_input_queues:
            await update.message.reply_text("❌ Skript ishlamayapti!")
            context.user_data['waiting_for_input'] = False
            return
        
        try:
            script_input_queues[key].put(message_text)
            await update.message.reply_text(
                f"✅ *{script_name}* ga yuborildi:\n```\n{message_text}\n```",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    else:
        await update.message.reply_text(
            "ℹ️ Tugmalardan foydalaning yoki /start bosing."
        )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    document = update.message.document
    file_name = document.file_name
    
    # Requirements.txt
    if context.user_data.get('waiting_for_requirements') or file_name == "requirements.txt":
        try:
            user_dir = Path(SCRIPTS_DIR) / user_id
            user_dir.mkdir(exist_ok=True)
            file_path = user_dir / "requirements.txt"
            
            file = await document.get_file()
            await file.download_to_drive(file_path)
            
            context.user_data['waiting_for_requirements'] = False
            await update.message.reply_text(
                f"✅ `requirements.txt` yuklandi!\n"
                f"▶️ Skriptni ishga tushirganda avtomatik o'rnatiladi.",
                parse_mode="Markdown"
            )
            return
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}")
            return
    
    # Python skript
    if not context.user_data.get('waiting_for_script'):
        await update.message.reply_text("❌ Avval 'Skript yuborish' tugmasini bosing.")
        return
    
    if not document or not document.file_name.endswith('.py'):
        await update.message.reply_text("❌ Faqat .py fayl yuboring!")
        return
    
    # Skriptni saqlash
    user_dir = Path(SCRIPTS_DIR) / user_id
    user_dir.mkdir(exist_ok=True)
    file_path = user_dir / file_name
    
    try:
        file = await document.get_file()
        await file.download_to_drive(file_path)
        
        # Ma'lumotlarni yangilash
        user_data = load_user_data()
        if user_id not in user_data:
            user_data[user_id] = {"scripts": []}
        if file_name not in user_data[user_id]["scripts"]:
            user_data[user_id]["scripts"].append(file_name)
            save_user_data(user_data)
        
        context.user_data['waiting_for_script'] = False
        await update.message.reply_text(
            f"✅ *{file_name}* yuklandi!\n\n"
            f"📊 Hajm: {document.file_size} bayt\n"
            f"▶️ Ishga tushirish uchun tugmani bosing.\n"
            f"📦 Agar kerak bo'lsa `requirements.txt` yuboring.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Universal Script Bot**\n\n"
        "Har qanday skriptni ishga tushiradi!\n"
        "Termux, server, hamma joyda!\n\n"
        "/start - Boshlash\n"
        "/help - Yordam\n"
        "/cancel - Bekor qilish",
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
    
    print("="*60)
    print("🤖 Universal Script Bot ishga tushdi!")
    print("✅ Har qanday skript ishlaydi")
    print("✅ Termux, server, hamma joyda")
    print(f"📁 Skriptlar: {SCRIPTS_DIR}")
    print(f"📁 Loglar: {LOGS_DIR}")
    print(f"📁 Virtual env: {VENV_DIR}")
    print("="*60)
    
    application.run_polling()

if __name__ == "__main__":
    main()
