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

# Bot tokeni
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"

# Papkalar
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"

for dir_name in [SCRIPTS_DIR, LOGS_DIR]:
    dir_name.mkdir(exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ishga tushirilgan skriptlar
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

def get_user_script_dir(user_id):
    user_dir = SCRIPTS_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)
    return user_dir

def get_script_path(user_id, script_name):
    return get_user_script_dir(user_id) / script_name

def get_log_path(user_id, script_name):
    return LOGS_DIR / f"{user_id}_{script_name}.log"

def run_script(script_path, user_id, script_name, context):
    """Skriptni ishga tushirish va loglarni jonli yuborish"""
    try:
        # Skriptni ishga tushirish
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(script_path.parent)
        )
        
        script_key = f"{user_id}_{script_name}"
        script_input_queues[script_key] = queue.Queue()
        
        running_scripts[script_key] = {
            "process": process,
            "start_time": datetime.now().isoformat(),
            "status": "running"
        }
        
        log_file = get_log_path(user_id, script_name)
        
        # Log yozish va Telegramga yuborish
        def send_log(message, is_error=False):
            """Logni faylga yozish va Telegramga yuborish"""
            try:
                # Faylga yozish
                with open(log_file, 'a', encoding='utf-8') as f:
                    prefix = "[STDERR]" if is_error else "[STDOUT]"
                    f.write(f"{prefix} {message}")
                    f.flush()
                
                # Telegramga yuborish (faqat stdout)
                if not is_error:
                    context.bot.send_message(
                        chat_id=int(user_id),
                        text=f"📤 {message.strip()}"
                    )
            except Exception as e:
                logger.error(f"Send log error: {e}")
        
        # Input handler
        def input_handler():
            while process.poll() is None:
                try:
                    input_data = script_input_queues[script_key].get(timeout=0.5)
                    if input_data == "EXIT":
                        break
                    process.stdin.write(input_data + "\n")
                    process.stdin.flush()
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
                    # Stdout - asosiy chiqish
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        send_log(stdout_line, is_error=False)
                    
                    # Stderr - xatoliklar
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        send_log(stderr_line, is_error=True)
                        
                except Exception as e:
                    logger.error(f"Output error: {e}")
                    break
            
            # Process tugagandan keyin
            stdout, stderr = process.communicate()
            if stdout:
                send_log(stdout, is_error=False)
            if stderr:
                send_log(stderr, is_error=True)
        
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
            
            context.bot.send_message(
                chat_id=int(user_id),
                text=f"⏹ *{script_name}* to'xtadi! (Exit: {process.returncode})",
                parse_mode="Markdown"
            )
        
        if script_key in script_input_queues:
            del script_input_queues[script_key]
            
    except Exception as e:
        logger.error(f"Script error {script_name}: {e}")
        script_key = f"{user_id}_{script_name}"
        if script_key in running_scripts:
            running_scripts[script_key]["status"] = "error"
        
        context.bot.send_message(
            chat_id=int(user_id),
            text=f"❌ *{script_name}* xatolik:\n```\n{str(e)}\n```",
            parse_mode="Markdown"
        )

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
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        f"🤖 **Termux uslubidagi bot**\n"
        f"✅ Skript yuboring - avtomatik ishga tushadi\n"
        f"✅ Barcha chiqishlar jonli yuboriladi\n"
        f"✅ Xuddi Termuxdagi kabi!\n\n"
        f"📌 **Qanday ishlaydi:**\n"
        f"1. `.py` faylni yuboring\n"
        f"2. Skript avtomatik ishga tushadi\n"
        f"3. Barcha `print()` chiqishlari keladi\n"
        f"4. `input()` so'rasa, matn yozib yuboring\n\n"
        f"📌 **Buyruqlar:**\n"
        f"/start - Boshlash\n"
        f"/stop - Skriptni to'xtatish\n"
        f"/logs - Loglarni ko'rish\n"
        f"/scripts - Skriptlar ro'yxati\n"
        f"/delete - Skriptni o'chirish",
        parse_mode="Markdown"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fayl yuborilganda - avtomatik ishga tushadi"""
    user_id = str(update.effective_user.id)
    document = update.message.document
    
    if not document or not document.file_name.endswith('.py'):
        await update.message.reply_text("❌ Faqat .py fayl yuboring!")
        return
    
    file_name = document.file_name
    
    # Skriptni saqlash
    user_dir = get_user_script_dir(user_id)
    file_path = user_dir / file_name
    
    # Agar skript allaqachon mavjud bo'lsa
    if file_path.exists():
        # Avval to'xtatish
        key = f"{user_id}_{file_name}"
        if key in running_scripts and running_scripts[key]["status"] == "running":
            try:
                process = running_scripts[key]["process"]
                process.terminate()
                process.wait(timeout=3)
                if key in script_input_queues:
                    script_input_queues[key].put("EXIT")
            except:
                pass
    
    try:
        # Faylni yuklash
        file = await document.get_file()
        await file.download_to_drive(file_path)
        
        # Ma'lumotlarni yangilash
        user_data = load_user_data()
        if user_id not in user_data:
            user_data[user_id] = {"scripts": []}
        if file_name not in user_data[user_id]["scripts"]:
            user_data[user_id]["scripts"].append(file_name)
            save_user_data(user_data)
        
        await update.message.reply_text(
            f"✅ *{file_name}* yuklandi!\n"
            f"🚀 Avtomatik ishga tushirilmoqda...\n"
            f"📁 Yo'l: `{file_path}`",
            parse_mode="Markdown"
        )
        
        # Avtomatik ishga tushirish
        thread = threading.Thread(
            target=run_script,
            args=(file_path, user_id, file_name, context),
            daemon=True
        )
        thread.start()
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn yuborilganda - input sifatida yuborish"""
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    # Buyruqlar
    if message_text.startswith('/'):
        return
    
    # Input yuborish
    user_data = load_user_data()
    if user_id not in user_data:
        await update.message.reply_text("❌ Avval skript yuboring!")
        return
    
    # Qaysi skript ishlayapti?
    running_script = None
    for script in user_data[user_id]["scripts"]:
        key = f"{user_id}_{script}"
        if key in running_scripts and running_scripts[key]["status"] == "running":
            running_script = script
            break
    
    if not running_script:
        await update.message.reply_text("❌ Hech qanday skript ishlamayapti!")
        return
    
    # Input yuborish
    key = f"{user_id}_{running_script}"
    if key not in script_input_queues:
        await update.message.reply_text("❌ Xatolik!")
        return
    
    try:
        script_input_queues[key].put(message_text)
        await update.message.reply_text(f"✅ Yuborildi: `{message_text}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def stop_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skriptni to'xtatish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    # Qaysi skript ishlayapti?
    stopped = False
    for script in user_data[user_id]["scripts"]:
        key = f"{user_id}_{script}"
        if key in running_scripts and running_scripts[key]["status"] == "running":
            try:
                process = running_scripts[key]["process"]
                process.terminate()
                process.wait(timeout=3)
                running_scripts[key]["status"] = "stopped"
                if key in script_input_queues:
                    script_input_queues[key].put("EXIT")
                await update.message.reply_text(f"⏹ *{script}* to'xtatildi!", parse_mode="Markdown")
                stopped = True
            except Exception as e:
                await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    
    if not stopped:
        await update.message.reply_text("❌ Hech qanday skript ishlamayapti!")

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Loglarni ko'rish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    # Oxirgi skriptning logini ko'rsatish
    last_script = user_data[user_id]["scripts"][-1]
    log_file = get_log_path(user_id, last_script)
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > 4000:
            content = content[-4000:] + "\n\n... (oxirgi 4000 belgi)"
        
        await update.message.reply_text(
            f"📄 *{last_script}* log:\n\n```\n{content}\n```",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Log topilmadi!")

async def list_scripts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skriptlar ro'yxati"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    text = "📋 Skriptlaringiz:\n\n"
    for script in user_data[user_id]["scripts"]:
        key = f"{user_id}_{script}"
        status = "🟢" if key in running_scripts and running_scripts[key]["status"] == "running" else "🔴"
        text += f"{status} {script}\n"
    
    await update.message.reply_text(text)

async def delete_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skriptni o'chirish"""
    user_id = str(update.effective_user.id)
    
    user_data = load_user_data()
    if user_id not in user_data or not user_data[user_id]["scripts"]:
        await update.message.reply_text("❌ Skriptlar mavjud emas!")
        return
    
    # Eng so'nggi skriptni o'chirish
    script_name = user_data[user_id]["scripts"][-1]
    key = f"{user_id}_{script_name}"
    
    # Avval to'xtatish
    if key in running_scripts and running_scripts[key]["status"] == "running":
        try:
            process = running_scripts[key]["process"]
            process.terminate()
            process.wait(timeout=3)
            if key in script_input_queues:
                script_input_queues[key].put("EXIT")
        except:
            pass
    
    # Faylni o'chirish
    script_path = get_script_path(user_id, script_name)
    if script_path.exists():
        script_path.unlink()
        
        log_file = get_log_path(user_id, script_name)
        if log_file.exists():
            log_file.unlink()
        
        user_data[user_id]["scripts"].remove(script_name)
        save_user_data(user_data)
        
        if key in running_scripts:
            del running_scripts[key]
        if key in script_input_queues:
            del script_input_queues[key]
        
        await update.message.reply_text(f"✅ *{script_name}* o'chirildi!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Skript topilmadi!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_script))
    application.add_handler(CommandHandler("logs", view_logs))
    application.add_handler(CommandHandler("scripts", list_scripts))
    application.add_handler(CommandHandler("delete", delete_script))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*60)
    print("🤖 Termux uslubidagi bot ishga tushdi!")
    print("✅ Skript yuboring - avtomatik ishga tushadi")
    print("✅ Barcha chiqishlar jonli yuboriladi")
    print(f"📁 Skriptlar: {SCRIPTS_DIR}")
    print(f"📁 Loglar: {LOGS_DIR}")
    print("="*60)
    
    application.run_polling()

if __name__ == "__main__":
    main()
