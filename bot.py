import os
import pty
import signal
import subprocess
import threading

import telebot

# === SOZLAMALAR ===
# Shu ikki qatorni o'zingnikiga almashtir:
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"        # masalan: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
ADMIN_IDS = [7907570895]                                  # masalan: [123456789] — o'z Telegram ID'ing

BOTS_DIR = "bots"
LOGS_DIR = "logs"
os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Qaysi kengaytma qaysi interpretator bilan ishga tushishini shu yerda
# belgilaymiz. Yangi til qo'shmoqchi bo'lsang, shu ro'yxatga qo'shasan.
RUNTIMES = {
    ".py": ["python3"],
    ".php": ["php"],
    ".js": ["node"],
}

processes = {}   # bot_nomi -> subprocess.Popen
master_fds = {}  # bot_nomi -> PTY master fayl deskriptori (matn yuborish uchun)

bot = telebot.TeleBot(BOT_TOKEN)


def is_admin(message) -> bool:
    return message.from_user.id in ADMIN_IDS


def stream_output_to_log(master_fd: int, log_path: str):
    """PTY'dan chiqadigan hamma narsani (chin terminaldagidek) log fayliga yozadi."""
    def reader():
        with open(log_path, "ab") as log_file:
            while True:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                log_file.write(data)
                log_file.flush()
    t = threading.Thread(target=reader, daemon=True)
    t.start()


def find_bot_file(name: str):
    """bots/<name>.<ext> ko'rinishidagi faylni qidiradi, topsa (path, ext) qaytaradi."""
    for ext in RUNTIMES:
        path = os.path.join(BOTS_DIR, f"{name}{ext}")
        if os.path.isfile(path):
            return path, ext
    return None, None


def list_available_bots():
    names = []
    for f in os.listdir(BOTS_DIR):
        base, ext = os.path.splitext(f)
        if ext in RUNTIMES:
            names.append(base)
    return sorted(set(names))


def is_running(name: str) -> bool:
    proc = processes.get(name)
    return proc is not None and proc.poll() is None


def install_requirements(name: str, ext: str, log_file):
    """Bot yoniga qo'yilgan requirements/package.json/composer.json bo'lsa o'rnatadi."""
    if ext == ".py":
        req = os.path.join(BOTS_DIR, f"{name}.requirements.txt")
        if os.path.isfile(req):
            log_file.write(f"--- pip install -r {req} ---\n")
            log_file.flush()
            subprocess.run(["pip", "install", "-r", req], stdout=log_file, stderr=subprocess.STDOUT)
    elif ext == ".js":
        pkg = os.path.join(BOTS_DIR, f"{name}.package.json")
        if os.path.isfile(pkg):
            log_file.write("--- npm install ---\n")
            log_file.flush()
            subprocess.run(["npm", "install", "--prefix", BOTS_DIR], stdout=log_file, stderr=subprocess.STDOUT)
    elif ext == ".php":
        comp = os.path.join(BOTS_DIR, f"{name}.composer.json")
        if os.path.isfile(comp):
            log_file.write("--- composer install ---\n")
            log_file.flush()
            subprocess.run(["composer", "install", "-d", BOTS_DIR], stdout=log_file, stderr=subprocess.STDOUT)


# ===================== BUYRUQLAR =====================

@bot.message_handler(commands=["start", "help"])
def start(message):
    if not is_admin(message):
        bot.reply_to(message, "Kechirasiz, sizda ruxsat yo'q.")
        return
    text = (
        "Salom! Men sening bot-menejeringman.\n\n"
        "📂 Fayl yubor (document) — .py / .php / .js — avtomatik bots/ ga saqlanadi\n\n"
        "/list — barcha botlar va holati\n"
        "/run <nomi> — botni ishga tushirish (kerak bo'lsa avval kutubxonalarni o'rnatadi)\n"
        "/stop <nomi> — botni to'xtatish\n"
        "/restart <nomi> — qayta ishga tushirish\n"
        "/status — hozir nechta bot ishlayotgani\n"
        "/log <nomi> — botning oxirgi loglari\n"
        "/send <nomi> <matn> — ishlab turgan botga terminal orqali matn yuborish\n"
        "   (masalan bot 'Loginni kiriting:' deb so'rasa shu bilan javob berasan)"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["list"])
def list_bots(message):
    if not is_admin(message):
        return
    names = list_available_bots()
    if not names:
        bot.reply_to(message, "bots/ papkasida hech qanday bot yo'q. Menga .py/.php/.js fayl yuborib qo'sh.")
        return
    lines = []
    for n in names:
        state = "🟢 ishlayapti" if is_running(n) else "⚪ to'xtagan"
        lines.append(f"{n} — {state}")
    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(commands=["run"])
def run_bot(message):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Foydalanish: /run <bot_nomi>")
        return
    name = parts[1].strip()
    path, ext = find_bot_file(name)

    if not path:
        bot.reply_to(
            message,
            f"'{name}' topilmadi. /list bilan mavjud botlarni ko'r.\n"
            f"Qo'llab-quvvatlanadigan turlar: {', '.join(RUNTIMES)}",
        )
        return
    if is_running(name):
        bot.reply_to(message, f"'{name}' allaqachon ishlayapti.")
        return

    interpreter = RUNTIMES[ext]
    log_path = os.path.join(LOGS_DIR, f"{name}.log")

    bot.reply_to(message, f"⏳ '{name}' tayyorlanmoqda (kerak bo'lsa kutubxonalar o'rnatilmoqda)...")
    with open(log_path, "a") as setup_log:
        install_requirements(name, ext, setup_log)

    # Haqiqiy pseudo-terminal (PTY) ochamiz — shu orqali skript xuddi chinakam
    # terminalda ishlayotgandek his qiladi (TERM o'rnatilgan, getpass/parol
    # kiritish, rich progress-bar kabi narsalar ham to'g'ri ishlaydi).
    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"

    try:
        proc = subprocess.Popen(
            interpreter + [path],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            preexec_fn=os.setsid,
            close_fds=True,
        )
    except FileNotFoundError:
        os.close(master_fd)
        os.close(slave_fd)
        bot.reply_to(
            message,
            f"'{interpreter[0]}' interpretatori serverda o'rnatilmagan. "
            f"README'dagi 'Ko'p tilni qo'llab-quvvatlash' bo'limiga qara.",
        )
        return

    os.close(slave_fd)  # bola jarayon o'z nusxasini oldi, ota-jarayonga kerak emas
    processes[name] = proc
    master_fds[name] = master_fd
    stream_output_to_log(master_fd, log_path)
    bot.reply_to(message, f"✅ '{name}' ({ext}) ishga tushdi (PID {proc.pid}).")


@bot.message_handler(commands=["stop"])
def stop_bot(message):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Foydalanish: /stop <bot_nomi>")
        return
    name = parts[1].strip()
    proc = processes.get(name)
    if not proc or proc.poll() is not None:
        bot.reply_to(message, f"'{name}' hozir ishlamayapti.")
        return
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    fd = master_fds.pop(name, None)
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass
    bot.reply_to(message, f"🛑 '{name}' to'xtatildi.")


@bot.message_handler(commands=["restart"])
def restart_bot(message):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Foydalanish: /restart <bot_nomi>")
        return
    name = parts[1].strip()
    proc = processes.get(name)
    if proc and proc.poll() is None:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    message.text = f"/run {name}"
    run_bot(message)


@bot.message_handler(commands=["status"])
def status(message):
    if not is_admin(message):
        return
    running = [n for n in processes if is_running(n)]
    bot.reply_to(message, f"Ishlab turgan botlar: {', '.join(running) if running else 'yoq'}")


@bot.message_handler(commands=["log"])
def show_log(message):
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Foydalanish: /log <bot_nomi>")
        return
    name = parts[1].strip()
    log_path = os.path.join(LOGS_DIR, f"{name}.log")
    if not os.path.isfile(log_path):
        bot.reply_to(message, "Bu bot uchun log topilmadi.")
        return
    with open(log_path, "rb") as f:
        data = f.read()[-3000:]
    text = data.decode(errors="ignore") or "(log bo'sh)"
    bot.reply_to(message, f"```\n{text}\n```", parse_mode="Markdown")


@bot.message_handler(commands=["send"])
def send_input(message):
    """Ishlab turgan botning stdin'iga matn yuboradi (masalan input() kutayotganda)."""
    if not is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Foydalanish: /send <bot_nomi> <matn>")
        return
    rest = parts[1]  # "<bot_nomi> <matn>" — nomda ham bo'sh joy bo'lishi mumkin

    # Ishlab turgan botlar orasidan REST matnga mos keladigan eng uzun nomni
    # qidiramiz — shu orqali nomida bo'sh joy bo'lgan fayllar ham to'g'ri ishlaydi
    # (masalan "bot (2)").
    running_names = sorted(processes.keys(), key=len, reverse=True)
    name = None
    text = None
    for n in running_names:
        if rest == n or rest.startswith(n + " "):
            name = n
            text = rest[len(n):].strip()
            break

    if name is None:
        bot.reply_to(
            message,
            "Bunday nomli ishlab turgan bot topilmadi. /status bilan aniq nomini tekshir.\n"
            "Eslatma: bot fayl nomida bo'sh joy bo'lsa (masalan 'bot (2).py'), "
            "nomni bo'sh joysiz qilib qayta nomlashni tavsiya qilaman.",
        )
        return
    if not text:
        bot.reply_to(message, "Foydalanish: /send <bot_nomi> <matn>")
        return

    proc = processes.get(name)
    if not proc or proc.poll() is not None:
        bot.reply_to(message, f"'{name}' hozir ishlamayapti.")
        return
    fd = master_fds.get(name)
    if fd is None:
        bot.reply_to(message, f"'{name}' matn qabul qila olmaydi.")
        return
    try:
        os.write(fd, (text + "\n").encode())
        bot.reply_to(message, f"📨 '{name}' ga yuborildi: {text}")
    except OSError as e:
        bot.reply_to(message, f"Yuborib bo'lmadi: {e}")


@bot.message_handler(content_types=["document"])
def receive_file(message):
    """Telegramga yuborilgan .py/.php/.js faylni bots/ ga o'zgartirmasdan saqlaydi."""
    if not is_admin(message):
        return
    file_name = message.document.file_name or ""
    _, ext = os.path.splitext(file_name)
    if ext not in RUNTIMES:
        bot.reply_to(
            message,
            f"Bu fayl turi qo'llab-quvvatlanmaydi ({ext or 'nomаʼlum'}). "
            f"Faqat: {', '.join(RUNTIMES)}",
        )
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    dest_path = os.path.join(BOTS_DIR, file_name)
    with open(dest_path, "wb") as f:
        f.write(downloaded)

    name = os.path.splitext(file_name)[0]
    bot.reply_to(
        message,
        f"📥 '{file_name}' saqlandi.\nIshga tushirish uchun: /run {name}",
    )


if __name__ == "__main__":
    print("Bot-menejer ishga tushdi...")
    bot.infinity_polling()
