import os
import sys
import json
import logging
import subprocess
import threading
import time
import queue
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================
# KONFIGURATSIYA
# ============================================

BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"

# Papkalar
BASE_DIR = Path(__file__).parent.absolute()
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"
RUN_DIR = BASE_DIR / "running"

for dir_name in [SCRIPTS_DIR, LOGS_DIR, RUN_DIR]:
    dir_name.mkdir(exist_ok=True, parents=True)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global o'zgaruvchilar
running_processes = {}
process_outputs = {}
user_data_file = "user_data.json"

# ============================================
# YORDAMCHI FUNKSIYALAR
# ============================================

def load_user_data():
    if os.path.exists(user_data_file):
        try:
            with open(user_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_data(data):
    try:
        with open(user_data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Save user data error: {e}")

def get_user_script_dir(user_id):
    user_dir = SCRIPTS_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True, parents=True)
    return user_dir

def get_script_path(user_id, script_name):
    return get_user_script_dir(user_id) / script_name

def get_log_path(user_id, script_name):
    return LOGS_DIR / f"{user_id}_{script_name}.log"

# ============================================
# REQUIREMENTS O'RNATISH
# ============================================

def install_requirements(script_path):
    """Skript uchun requirements.txt ni o'rnatish"""
    req_file = script_path.parent / "requirements.txt"
    if req_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--no-cache-dir"],
                capture_output=True,
                text=True,
                timeout=180
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    return True, "No requirements", ""

# ============================================
# SKRIPTNI ISHGA TUSHIRISH
# ============================================

def run_tron_script(script_path, user_id, script_name, context, config_data):
    """TRON skriptini ishga tushirish"""
    try:
        # Requirements o'rnatish
        success, stdout, stderr = install_requirements(script_path)
        if not success:
            context.bot.send_message(
                chat_id=int(user_id),
                text=f"⚠️ Requirements o'rnatishda xatolik:\n```\n{stderr[:500]}\n```",
                parse_mode="Markdown"
            )
        
        # Environment variables
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['TERM'] = 'xterm-256color'
        
        # TRON uchun maxsus environment
        if config_data:
            for key, value in config_data.items():
                env[f'TRON_{key.upper()}'] = str(value)
        
        # Skriptni ishga tushirish
        process = subprocess.Popen(
            [sys.executable, "-u", str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(script_path.parent),
            env=env
        )
        
        script_key = f"{user_id}_{script_name}"
        running_processes[script_key] = {
            "process": process,
            "start_time": datetime.now().isoformat(),
            "status": "running"
        }
        
        log_file = get_log_path(user_id, script_name)
        
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
                        
                        # Telegramga yuborish (faqat muhim qismi)
                        if any(keyword in stdout_line.lower() for keyword in ['balance', 'claim', 'success', 'error', 'bonus', 'login']):
                            context.bot.send_message(
                                chat_id=int(user_id),
                                text=f"📤 {stdout_line.strip()}"
                            )
                        else:
                            # Logga yozamiz lekin yubormaymiz (keraksiz chiqishlar)
                            pass
                    
                    # Stderr - xatoliklar
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[STDERR] {stderr_line}")
                            f.flush()
                        
                        # Xatoliklarni yuborish
                        context.bot.send_message(
                            chat_id=int(user_id),
                            text=f"⚠️ {stderr_line.strip()}"
                        )
                        
                except Exception as e:
                    logger.error(f"Output error: {e}")
                    break
            
            # Process tugadi
            stdout, stderr = process.communicate()
            if stdout:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"📤 {stdout.strip()}"
                )
            if stderr:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"⚠️ {stderr.strip()}"
                )
        
        # Thread ishga tushirish
        output_thread = threading.Thread(target=output_handler, daemon=True)
        output_thread.start()
        
        # Process tugashini kutish
        process.wait()
        
        # Status yangilash
        if script_key in running_processes:
            running_processes[script_key]["status"] = "stopped"
            running_processes[script_key]["end_time"] = datetime.now().isoformat()
        
        context.bot.send_message(
            chat_id=int(user_id),
            text=f"⏹ *{script_name}* to'xtadi! (Exit: {process.returncode})",
            parse_mode="Markdown"
        )
            
    except Exception as e:
        logger.error(f"Script error {script_name}: {e}")
        script_key = f"{user_id}_{script_name}"
        if script_key in running_processes:
            running_processes[script_key]["status"] = "error"
        
        context.bot.send_message(
            chat_id=int(user_id),
            text=f"❌ *{script_name}* xatolik:\n```\n{str(e)}\n```",
            parse_mode="Markdown"
        )

# ============================================
# BOT HANDLERLAR
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "registered_at": datetime.now().isoformat(),
            "scripts": [],
            "config": {}
        }
        save_user_data(user_data)
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        f"🔮 **TRON BOT SERVER**\n"
        f"✅ `tron.py` skriptini yuboring\n"
        f"✅ Avtomatik ishga tushadi\n"
        f"✅ Kerakli ma'lumotlarni bot orqali yuboring\n"
        f"✅ 24/7 ishlaydi\n\n"
        f"📌 **Qanday ishlaydi:**\n"
        f"1. `tron.py` faylni yuboring\n"
        f"2. Bot avtomatik ishga tushiradi\n"
        f"3. Kerakli ma'lumotlarni so'raydi\n"
        f"4. Siz ma'lumotlarni yozib yuborasiz\n\n"
        f"📌 **Buyruqlar:**\n"
        f"/start - Boshlash\n"
        f"/stop - Skriptni to'xtatish\n"
        f"/logs - Loglarni ko'rish\n"
        f"/status - Holatni tekshirish\n"
        f"/config - Konfiguratsiyani ko'rish\n"
        f"/set - Ma'lumot kiritish",
        parse_mode="Markdown"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fayl yuborilganda"""
    user_id = str(update.effective_user.id)
    document = update.message.document
    
    if not document or not document.file_name.endswith('.py'):
        await update.message.reply_text("❌ Faqat .py fayl yuboring!")
        return
    
    file_name = document.file_name
    
    # Faqat tron.py qabul qilinadi
    if file_name.lower() != "tron.py":
        await update.message.reply_text(
            f"❌ Faqat `tron.py` fayli qabul qilinadi!\n"
            f"Siz yuborgan: `{file_name}`",
            parse_mode="Markdown"
        )
        return
    
    # Skriptni saqlash
    user_dir = get_user_script_dir(user_id)
    file_path = user_dir / file_name
    
    # Avvalgi skriptni to'xtatish
    key = f"{user_id}_{file_name}"
    if key in running_processes and running_processes[key]["status"] == "running":
        try:
            process = running_processes[key]["process"]
            process.terminate()
            process.wait(timeout=3)
        except:
            pass
    
    try:
        file = await document.get_file()
        await file.download_to_drive(file_path)
        
        # Ma'lumotlarni yangilash
        user_data = load_user_data()
        if user_id not in user_data:
            user_data[user_id] = {"scripts": [], "config": {}}
        if file_name not in user_data[user_id]["scripts"]:
            user_data[user_id]["scripts"].append(file_name)
        save_user_data(user_data)
        
        await update.message.reply_text(
            f"✅ *{file_name}* yuklandi!\n"
            f"📁 Yo'l: `{file_path}`\n\n"
            f"🔧 **Kerakli ma'lumotlarni sozlang:**\n"
            f"1. `/set cookie` - Cookie kiriting\n"
            f"2. `/set user_agent` - User Agent kiriting\n"
            f"3. `/set apikey` - API kalitini kiriting\n\n"
            f"🚀 Sozlamalardan keyin `/run` buyrug'ini bering!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn yuborilganda"""
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    if message_text.startswith('/'):
        return
    
    # Agar ma'lumot kiritish holatida bo'lsa
    if context.user_data.get('waiting_for_config'):
        config_key = context.user_data.get('config_key')
        if config_key:
            # Ma'lumotni saqlash
            user_data = load_user_data()
            if user_id not in user_data:
                user_data[user_id] = {"scripts": [], "config": {}}
            user_data[user_id]["config"][config_key] = message_text
            save_user_data(user_data)
            
            context.user_data['waiting_for_config'] = False
            context.user_data['config_key'] = None
            
            await update.message.reply_text(
                f"✅ `{config_key}` sozlandi!\n"
                f"📝 Qiymat: `{message_text}`",
                parse_mode="Markdown"
            )
            return
    
    # Oddiy xabar
    await update.message.reply_text(
        "ℹ️ Ma'lumot kiritish uchun:\n"
        "1. `/set cookie` - Cookie\n"
        "2. `/set user_agent` - User Agent\n"
        "3. `/set apikey` - API kalit\n"
        "4. `/set` dan keyin ma'lumotni yozing"
    )

async def set_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Konfiguratsiya kiritish"""
    user_id = str(update.effective_user.id)
    
    # Agar argument berilgan bo'lsa
    if context.args:
        config_key = context.args[0].lower()
        valid_keys = ['cookie', 'user_agent', 'apikey', 'multibot_apikey', 'xevil_apikey', 'type']
        
        if config_key not in valid_keys:
            await update.message.reply_text(
                f"❌ Noto'g'ri kalit!\n"
                f"✅ Mavjud kalitlar: {', '.join(valid_keys)}",
                parse_mode="Markdown"
            )
            return
        
        context.user_data['waiting_for_config'] = True
        context.user_data['config_key'] = config_key
        
        await update.message.reply_text(
            f"📝 *{config_key}* qiymatini kiriting:\n\n"
            f"💬 Matn yozib yuboring.",
            parse_mode="Markdown"
        )
        return
    
    # Joriy konfiguratsiyani ko'rsatish
    user_data = load_user_data()
    if user_id in user_data and user_data[user_id].get("config"):
        config = user_data[user_id]["config"]
        text = "📋 **Joriy konfiguratsiya:**\n\n"
        for key, value in config.items():
            # Xavfsizlik uchun cookie ni qisman ko'rsatish
            if key == 'cookie' and len(value) > 20:
                value = value[:20] + "..."
            text += f"📌 *{key}*: `{value}`\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "❌ Konfiguratsiya mavjud emas!\n\n"
            "Sozlash uchun:\n"
            "`/set cookie` - Cookie\n"
            "`/set user_agent` - User Agent",
            parse_mode="Markdown"
        )

async def run_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skriptni ishga tushirish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Avval `tron.py` faylini yuboring!")
        return
    
    # Konfiguratsiyani tekshirish
    config = user_data[user_id].get("config", {})
    required = ['cookie', 'user_agent']
    missing = [r for r in required if r not in config]
    
    if missing:
        await update.message.reply_text(
            f"❌ Quyidagi ma'lumotlar kiritilmagan:\n"
            f"{', '.join(missing)}\n\n"
            f"Sozlash uchun: `/set {missing[0]}`",
            parse_mode="Markdown"
        )
        return
    
    script_name = user_data[user_id]["scripts"][-1]
    script_path = get_script_path(user_id, script_name)
    
    if not script_path.exists():
        await update.message.reply_text("❌ Skript topilmadi!")
        return
    
    # Skriptni ishga tushirish
    key = f"{user_id}_{script_name}"
    if key in running_processes and running_processes[key]["status"] == "running":
        await update.message.reply_text("⚠️ Skript allaqachon ishlayapti!")
        return
    
    await update.message.reply_text(
        f"🚀 *{script_name}* ishga tushirilmoqda...\n"
        f"📁 Yo'l: `{script_path}`\n"
        f"📋 Konfiguratsiya yuklandi!",
        parse_mode="Markdown"
    )
    
    # Skriptni ishga tushirish
    thread = threading.Thread(
        target=run_tron_script,
        args=(script_path, user_id, script_name, context, config),
        daemon=True
    )
    thread.start()

async def stop_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skriptni to'xtatish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    script_name = user_data[user_id]["scripts"][-1]
    key = f"{user_id}_{script_name}"
    
    if key not in running_processes or running_processes[key]["status"] != "running":
        await update.message.reply_text("❌ Skript ishlamayapti!")
        return
    
    try:
        process = running_processes[key]["process"]
        process.terminate()
        process.wait(timeout=5)
        running_processes[key]["status"] = "stopped"
        await update.message.reply_text(f"⏹ *{script_name}* to'xtatildi!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Loglarni ko'rish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    script_name = user_data[user_id]["scripts"][-1]
    log_file = get_log_path(user_id, script_name)
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > 4000:
            content = content[-4000:] + "\n\n... (oxirgi 4000 belgi)"
        
        await update.message.reply_text(
            f"📄 *{script_name}* log:\n\n```\n{content}\n```",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Log topilmadi!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Holatni ko'rish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    script_name = user_data[user_id]["scripts"][-1]
    key = f"{user_id}_{script_name}"
    
    text = f"📊 *{script_name}* holati:\n\n"
    if key in running_processes:
        status_data = running_processes[key]
        status_emoji = "🟢" if status_data["status"] == "running" else "🔴"
        text += f"Holat: {status_emoji} {status_data['status']}\n"
        text += f"Boshlangan: {status_data['start_time']}\n"
        if "end_time" in status_data:
            text += f"Tugagan: {status_data['end_time']}\n"
    else:
        text += "Holat: ⚪ ishlamayapti\n"
    
    # Konfiguratsiya
    config = user_data[user_id].get("config", {})
    if config:
        text += "\n📋 Konfiguratsiya:\n"
        for key, value in config.items():
            if key == 'cookie' and len(value) > 20:
                value = value[:20] + "..."
            text += f"• {key}: `{value}`\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ============================================
# MAIN
# ============================================

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("run", run_script))
    application.add_handler(CommandHandler("stop", stop_script))
    application.add_handler(CommandHandler("logs", view_logs))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("config", set_config))
    application.add_handler(CommandHandler("set", set_config))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*60)
    print("🔮 TRON BOT SERVER ishga tushdi!")
    print(f"📁 Skriptlar: {SCRIPTS_DIR}")
    print(f"📁 Loglar: {LOGS_DIR}")
    print("="*60)
    print("\n📌 Bot buyruqlari:")
    print("  /start - Boshlash")
    print("  /set cookie - Cookie kiritish")
    print("  /set user_agent - User Agent kiritish")
    print("  /set apikey - API kalit kiritish")
    print("  /config - Konfiguratsiyani ko'rish")
    print("  /run - Skriptni ishga tushirish")
    print("  /stop - Skriptni to'xtatish")
    print("  /logs - Loglarni ko'rish")
    print("  /status - Holatni tekshirish")
    print("="*60)
    
    application.run_polling()

if __name__ == "__main__":
    main()
