#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import base64
import subprocess
import tempfile
import threading
import logging
from datetime import datetime
from urllib.parse import urlencode, urlparse, quote_plus
from typing import Dict, Any, Optional

import requests as _http
import urllib3

# Telegram bot
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    os.system("pip install python-telegram-bot==20.7")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================================
#                       KONSTANTALAR
# ==========================================================
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"

title = "TRON"
versi = "1.0.8"
class_require = "1.1.7"
host = "https://tronpick.io/"
turnstile = ""
recaptcha = "6LeBFBclAAAAANoZIrwXU1cPgYDDM7f1ehHpzXWj"
hcaptcha = ""
class_version = "1.1.7"

# Warna teks
n = "\n"
d = "\033[0m"
m = "\033[1;31m"
h = "\033[1;32m"
k = "\033[1;33m"
b = "\033[1;34m"
u = "\033[1;35m"
c = "\033[1;36m"
p = "\033[1;37m"
o = "\033[38;5;214m"

# ==========================================================
#                       YORDAMCHI
# ==========================================================
def safe_json_loads(s, debug_tag="response"):
    if s is None:
        return None
    text = s.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        obj, _end = json.JSONDecoder().raw_decode(text)
        return obj
    except json.JSONDecodeError:
        try:
            with open(f"debug_{debug_tag}.txt", "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
        return None

# ==========================================================
#                       REQUESTS
# ==========================================================
class Requests:
    @staticmethod
    def Curl(url, header=0, post=0, data_post=0, cookie=0, proxy=0, skip=0):
        while True:
            header_file = None
            body_file = None
            try:
                hf = tempfile.NamedTemporaryFile(delete=False, suffix=".hdr")
                header_file = hf.name
                hf.close()
                bf = tempfile.NamedTemporaryFile(delete=False, suffix=".body")
                body_file = bf.name
                bf.close()

                cmd = ["curl", "-s", "-k", "-L", "--connect-timeout", "30", "-D", header_file, "-o", body_file]

                if header:
                    for hline in header:
                        cmd += ["-H", hline]
                if cookie:
                    cmd += ["-b", cookie, "-c", cookie]
                if proxy:
                    cmd += ["--proxytunnel", "-x", proxy]
                if post:
                    cmd += ["-X", "POST"]
                    if data_post:
                        cmd += ["--data-raw", data_post]
                cmd.append(url)

                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=45)
                except FileNotFoundError:
                    print("curl dasturi topilmadi!")
                    time.sleep(3)
                    continue
                except subprocess.TimeoutExpired:
                    print("Check your Connection!")
                    time.sleep(2)
                    continue

                if result.returncode != 0:
                    time.sleep(2)
                    continue

                with open(header_file, "r", errors="ignore") as f:
                    head_raw = f.read()
                with open(body_file, "rb") as f:
                    body_bytes = f.read()

                if skip:
                    return None

                blocks = [blk for blk in head_raw.split("\r\n\r\n") if blk.strip()]
                head_lines = blocks[-1] if blocks else head_raw.strip()
                body = body_bytes.decode("utf-8", errors="replace")

                if not body:
                    print("Check your Connection!")
                    time.sleep(2)
                    continue

                return [head_lines, body]
            finally:
                for fpath in (header_file, body_file):
                    if fpath and os.path.exists(fpath):
                        try:
                            os.unlink(fpath)
                        except Exception:
                            pass

    @staticmethod
    def get(url, head=0):
        return Requests.Curl(url, head)

    @staticmethod
    def post(url, head=0, data_post=0):
        return Requests.Curl(url, head, 1, data_post)

# ==========================================================
#                       DISPLAY
# ==========================================================
class Display:
    @staticmethod
    def Error(except_):
        return f"{m}---[{p}!{m}] {p}{except_}"

    @staticmethod
    def Sukses(msg):
        return f"{h}---[{p}\u2713{h}] {p}{msg}{n}"

# ==========================================================
#                       FUNCTIONS
# ==========================================================
class Functions:
    configFile = "tronpick_config.json"

    @staticmethod
    def _load_config():
        if not os.path.exists(Functions.configFile):
            return {}
        try:
            with open(Functions.configFile, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_config(config):
        with open(Functions.configFile, "w") as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def setConfig(key):
        config = Functions._load_config()
        if key in config:
            return config[key]
        return None

    @staticmethod
    def removeConfig(key):
        config = Functions._load_config()
        if key in config:
            del config[key]
        Functions._save_config(config)

    @staticmethod
    def getConfig(key):
        config = Functions._load_config()
        return config.get(key)

# ==========================================================
#                       HTMLSCRAP
# ==========================================================
class HtmlScrap:
    def __init__(self):
        self.captcha_re = r'class=["\']([^"\']+)["\'][^>]*data-sitekey=["\']([^"\']+)["\']'

    def Result(self, html, form=1):
        data = {}
        data["cloudflare"] = bool(re.search(r"Just a moment\.\.\.", html))
        data["captcha"] = self._getCaptcha(html)
        
        response = {}
        if "icon: 'success'" in html:
            parts = html.split("icon: 'success',")
            if len(parts) > 1:
                inner = parts[1].split("html: '")
                if len(inner) > 1:
                    response["success"] = re.sub(r"<[^>]+>", "", inner[1].split("'")[0])
        else:
            warning_parts = html.split("html: '")
            if len(warning_parts) > 1:
                response["warning"] = warning_parts[1].split("'")[0]
            else:
                response["warning"] = "Not Found"
        
        data["response"] = response
        return data

    def _getCaptcha(self, html):
        matches = re.findall(self.captcha_re, html, flags=re.IGNORECASE)
        data = {}
        for cls, sitekey in matches:
            data[cls] = sitekey
        return data

# ==========================================================
#                       CAPTCHA
# ==========================================================
class Captcha:
    def __init__(self):
        self.url = "http://api.multibot.in/"
        self.key = "test"
        self.provider = "Multibot"

    def getBalance(self):
        try:
            res = json.loads(_http.get(self.url + "res.php?action=userinfo&key=" + self.key, timeout=30).text)
            return res.get("balance")
        except:
            return 0

    def RecaptchaV2(self, sitekey, pageurl):
        data = urlencode({"method": "userrecaptcha", "sitekey": sitekey, "pageurl": pageurl})
        return self._getResult(data, "GET")

    def _getResult(self, data, method, header=0):
        get_res = self._in_api(data, method, header)
        get_in = get_res if isinstance(get_res, dict) else json.loads(get_res or "{}")
        if not get_in.get("status"):
            return 0
        a = 0
        while True:
            get_res = self._res_api(get_in["request"])
            if get_res.get("request") == "CAPCHA_NOT_READY":
                a += 5
                if a > 99:
                    a = 99
                continue
            if get_res.get("status"):
                return get_res["request"]
            return 0

    def _in_api(self, content, method, header=0):
        param = f"key={self.key}&json=1&{content}"
        try:
            return json.loads(_http.get(self.url + "in.php?" + param, timeout=30).text)
        except Exception:
            return None

    def _res_api(self, api_id):
        params = f"?key={self.key}&action=get&id={api_id}&json=1"
        try:
            return json.loads(_http.get(self.url + "res.php" + params, timeout=30).text)
        except Exception:
            return {}

# ==========================================================
#                       TRON BOT
# ==========================================================
class TronBot:
    def __init__(self):
        self.cookie = ""
        self.uagent = ""
        self.captcha = Captcha()
        self.scrap = HtmlScrap()

    def headers(self):
        return [
            "Host: " + urlparse(host).hostname,
            "cookie: " + self.cookie,
            "X-Requested-With: XMLHttpRequest",
            "user-agent: " + self.uagent,
        ]

    def Dashboard(self):
        r = Requests.get(host, self.headers())[1]
        data = {}
        data["cloudflare"] = 1 if re.search(r"Just a moment\.\.\.", r) else 0
        data["Login"] = "" if re.search(r"login_button", r) else 1
        
        try:
            data["Username"] = r.split("&username=")[1].split("&")[0].strip()
        except:
            data["Username"] = None
            
        try:
            data["Balance"] = r.split('class="drop_down_header_text user_balance">')[1].split("<")[0]
        except:
            data["Balance"] = "0"
            
        try:
            data["Level"] = r.split("Your level is  <b>")[1].split("</b>")[0]
        except:
            data["Level"] = "N/A"
            
        return data

    def ClaimBonus(self):
        r = Requests.get(host + "faucet.php", self.headers())
        cookies = {}
        set_cookie_matches = re.findall(r"^Set-Cookie:\s*([^;]*)", r[0], flags=re.MULTILINE | re.IGNORECASE)
        for item in set_cookie_matches:
            if "=" in item:
                key_, val_ = item.split("=", 1)
                cookies[key_] = val_
        
        data = "action=claim_bonus_faucet&csrf_test_name=" + cookies.get("csrf_cookie_name", "")
        r2 = safe_json_loads(Requests.post(host + "process.php", self.headers(), data)[1], "claim_bonus")
        if r2 and r2.get("ret"):
            return True, r2.get("mes", "Bonus yig'ildi!")
        return False, r2.get("mes", "Xatolik") if r2 else "Xatolik"

    def HourlyFaucet(self):
        r = Requests.get(host + "faucet.php", self.headers())
        cek = self.scrap.Result(r[1])
        if cek.get("cloudflare"):
            return False, "Cloudflare"
            
        cookies = {}
        set_cookie_matches = re.findall(r"^Set-Cookie:\s*([^;]*)", r[0], flags=re.MULTILINE | re.IGNORECASE)
        for item in set_cookie_matches:
            if "=" in item:
                key_, val_ = item.split("=", 1)
                cookies[key_] = val_

        cap = self.captcha.RecaptchaV2(recaptcha, host + "faucet.php")
        if not cap:
            return False, "Captcha xatolik"
            
        data = "action=claim_hourly_faucet&g-recaptcha-response=" + cap + "&h-captcha-response=null&captcha=&ft=&csrf_test_name=" + cookies.get("csrf_cookie_name", "")
        r2 = safe_json_loads(Requests.post(host + "process.php", self.headers(), data)[1], "hourly_faucet")
        
        if r2 and r2.get("ret"):
            return True, r2.get("mes", "Hourly bonus yig'ildi!")
        return False, r2.get("mes", "Xatolik") if r2 else "Xatolik"

# ==========================================================
#                       TELEGRAM BOT
# ==========================================================
CONFIG_FILE = "telegram_config.json"

# Papkalar
os.makedirs("config", exist_ok=True)
os.makedirs("sessions", exist_ok=True)

def load_tg_config():
    if not os.path.exists(CONFIG_FILE):
        return {"users": {}, "sessions": {}}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "sessions": {}}

def save_tg_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_session(user_id):
    config = load_tg_config()
    return config.get("sessions", {}).get(str(user_id))

def set_session(user_id, data):
    config = load_tg_config()
    if "sessions" not in config:
        config["sessions"] = {}
    config["sessions"][str(user_id)] = data
    save_tg_config(config)

def remove_session(user_id):
    config = load_tg_config()
    if "sessions" in config and str(user_id) in config["sessions"]:
        del config["sessions"][str(user_id)]
        save_tg_config(config)

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.application = None
        self.bot_instances = {}
        self.running_tasks = {}

    def setup(self):
        self.application = Application.builder().token(self.token).build()
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("login", self.login))
        self.application.add_handler(CommandHandler("logout", self.logout))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("balance", self.balance))
        self.application.add_handler(CommandHandler("claim", self.claim))
        self.application.add_handler(CommandHandler("hourly", self.hourly))
        self.application.add_handler(CommandHandler("stop", self.stop))
        self.application.add_handler(CommandHandler("dashboard", self.dashboard))
        self.application.add_handler(CommandHandler("setapi", self.setapi))
        
        self.application.add_handler(CallbackQueryHandler(self.callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        self.application.add_error_handler(self.error_handler)

    def run(self):
        print("🤖 Bot ishga tushmoqda...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start(self, update, context):
        username = update.effective_user.username or "NoUsername"
        text = f"""
🎰 *TRONPICK BOT v{versi}*

Assalomu alaykum @{username}! 👋

📌 *Komandalar:*
/start - Boshlash
/help - Yordam
/login - Hisobga kirish
/logout - Chiqish
/status - Holat
/balance - Balans
/dashboard - Dashboard
/claim - Bonus yig'ish
/hourly - Hourly bonus
/setapi - API sozlash
/stop - Vazifani to'xtatish

⚙️ *Avval:*
1. /login -> Cookie va User-Agent kiriting
2. /setapi -> Captcha API ni sozlang

🔑 *Bot token:* ✅ Sozlangan
        """
        keyboard = [[
            InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("💰 Balans", callback_data="balance")
        ],[
            InlineKeyboardButton("🎯 Bonus", callback_data="claim"),
            InlineKeyboardButton("⏰ Hourly", callback_data="hourly")
        ]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    async def help(self, update, context):
        text = """
📖 *Yordam*

🔑 /login - Hisobga kirish
  Format: cookie|user_agent

🔧 /setapi - API sozlash
  Format: provider|api_key
  Provider: multibot, xevil

💰 /balance - Balans
📊 /dashboard - Dashboard
🎯 /claim - Kunlik bonus
⏰ /hourly - Hourly bonus (1 soat)
🛑 /stop - Vazifani to'xtatish
🚪 /logout - Chiqish
📊 /status - Holat

📌 *Bot:* @{context.bot.username}
        """
        await update.message.reply_text(text, parse_mode="Markdown")

    async def login(self, update, context):
        await update.message.reply_text(
            "🔑 *Hisobga kirish*\n\n"
            "Cookie va User-Agent ni quyidagi formatda yuboring:\n"
            "`cookie|user_agent`\n\n"
            "Misol:\n"
            "`cf_clearance=...; PHPSESSID=...|Mozilla/5.0...`",
            parse_mode="Markdown"
        )
        context.user_data['state'] = 'login'

    async def logout(self, update, context):
        user_id = update.effective_user.id
        remove_session(user_id)
        if user_id in self.bot_instances:
            del self.bot_instances[user_id]
        await update.message.reply_text("✅ *Hisobdan chiqildi!*", parse_mode="Markdown")

    async def status(self, update, context):
        user_id = update.effective_user.id
        session = get_session(user_id)
        text = f"""
📊 *Holat*

👤 @{update.effective_user.username}
🔑 Kirish: {'✅' if session else '❌'}
🔄 Vazifa: {'Ishlayapti' if user_id in self.running_tasks and self.running_tasks.get(user_id) else 'To\'xtatilgan'}

📌 *Bot token:* ✅ Sozlangan
        """
        await update.message.reply_text(text, parse_mode="Markdown")

    async def balance(self, update, context):
        user_id = update.effective_user.id
        session = get_session(user_id)
        if not session:
            await update.message.reply_text("❌ Avval /login qiling!", parse_mode="Markdown")
            return
        try:
            bot = self._get_bot(user_id, session)
            r = bot.Dashboard()
            if not r.get("Login"):
                await update.message.reply_text("❌ Cookie eskirgan! /login qiling.", parse_mode="Markdown")
                remove_session(user_id)
                return
            text = f"""
💰 *Balans*

👤 {r.get('Username', 'Noma\'lum')}
💵 {r.get('Balance', '0')} TRX
📊 {r.get('Level', 'N/A')}
            """
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}", parse_mode="Markdown")

    async def dashboard(self, update, context):
        user_id = update.effective_user.id
        session = get_session(user_id)
        if not session:
            await update.message.reply_text("❌ Avval /login qiling!", parse_mode="Markdown")
            return
        try:
            bot = self._get_bot(user_id, session)
            r = bot.Dashboard()
            if not r.get("Login"):
                await update.message.reply_text("❌ Cookie eskirgan! /login qiling.", parse_mode="Markdown")
                remove_session(user_id)
                return
            text = f"""
📊 *Dashboard*

👤 {r.get('Username', 'N/A')}
💵 {r.get('Balance', '0')} TRX
📊 {r.get('Level', 'N/A')}
            """
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}", parse_mode="Markdown")

    async def claim(self, update, context):
        user_id = update.effective_user.id
        session = get_session(user_id)
        if not session:
            await update.message.reply_text("❌ Avval /login qiling!", parse_mode="Markdown")
            return
        await update.message.reply_text("🎯 *Bonus yig'ish boshlandi...*", parse_mode="Markdown")
        
        def task():
            try:
                bot = self._get_bot(user_id, session)
                success, msg = bot.ClaimBonus()
                self._send(user_id, f"{'✅' if success else '❌'} {msg}")
            except Exception as e:
                self._send(user_id, f"❌ Xatolik: {str(e)}")
        
        thread = threading.Thread(target=task)
        thread.daemon = True
        thread.start()
        self.running_tasks[user_id] = thread

    async def hourly(self, update, context):
        user_id = update.effective_user.id
        session = get_session(user_id)
        if not session:
            await update.message.reply_text("❌ Avval /login qiling!", parse_mode="Markdown")
            return
        await update.message.reply_text("⏰ *Hourly bonus boshlandi...*", parse_mode="Markdown")
        
        def task():
            try:
                bot = self._get_bot(user_id, session)
                success, msg = bot.HourlyFaucet()
                self._send(user_id, f"{'✅' if success else '❌'} {msg}")
            except Exception as e:
                self._send(user_id, f"❌ Xatolik: {str(e)}")
        
        thread = threading.Thread(target=task)
        thread.daemon = True
        thread.start()
        self.running_tasks[user_id] = thread

    async def stop(self, update, context):
        user_id = update.effective_user.id
        if user_id in self.running_tasks and self.running_tasks.get(user_id):
            self.running_tasks[user_id] = None
            await update.message.reply_text("🛑 *Vazifa to'xtatildi!*", parse_mode="Markdown")
        else:
            await update.message.reply_text("ℹ️ Hech qanday vazifa ishlamayapti.", parse_mode="Markdown")

    async def setapi(self, update, context):
        await update.message.reply_text(
            "🔑 *API sozlash*\n\n"
            "Format: `provider|api_key`\n"
            "Provider: `multibot`, `xevil`\n\n"
            "Misol: `multibot|YOUR_API_KEY`",
            parse_mode="Markdown"
        )
        context.user_data['state'] = 'api'

    async def callback(self, update, context):
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == "dashboard":
            await self.dashboard(update, context)
        elif data == "balance":
            await self.balance(update, context)
        elif data == "claim":
            await self.claim(update, context)
        elif data == "hourly":
            await self.hourly(update, context)

    async def message_handler(self, update, context):
        user_id = update.effective_user.id
        text = update.message.text
        
        # Login
        if context.user_data.get('state') == 'login':
            if '|' in text:
                cookie, ua = text.split('|', 1)
                set_session(user_id, {"cookie": cookie.strip(), "user_agent": ua.strip()})
                context.user_data['state'] = None
                await update.message.reply_text("✅ *Hisobga kirdingiz!*", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Format: `cookie|user_agent`", parse_mode="Markdown")
            return
            
        # API
        if context.user_data.get('state') == 'api':
            if '|' in text:
                provider, key = text.split('|', 1)
                config = load_tg_config()
                if "apis" not in config:
                    config["apis"] = {}
                config["apis"][str(user_id)] = {"provider": provider.strip(), "api_key": key.strip()}
                save_tg_config(config)
                context.user_data['state'] = None
                await update.message.reply_text(f"✅ *API sozlandi!* Provider: {provider}", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Format: `provider|api_key`", parse_mode="Markdown")
            return

    def _get_bot(self, user_id, session):
        if user_id not in self.bot_instances:
            bot = TronBot()
            bot.cookie = session.get("cookie")
            bot.uagent = session.get("user_agent")
            self.bot_instances[user_id] = bot
        return self.bot_instances[user_id]

    def _send(self, user_id, text):
        try:
            self.application.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        except Exception:
            pass

    async def error_handler(self, update, context):
        print(f"Xatolik: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(f"❌ Xatolik: {str(context.error)[:100]}", parse_mode="Markdown")

# ==========================================================
#                       MAIN
# ==========================================================
def main():
    # curl tekshirish
    try:
        subprocess.run(["curl", "--version"], capture_output=True, check=True)
    except:
        print("❌ curl o'rnatilmagan!")
        print("📌 apt install curl (Linux) yoki pkg install curl (Termux)")
        sys.exit(1)
    
    bot = TelegramBot(BOT_TOKEN)
    bot.setup()
    
    print(f"""
╔════════════════════════════════════════╗
║     🤖 TRONPICK TELEGRAM BOT v{versi}     ║
║     Bot ishga tushdi!                  ║
║     Token: {BOT_TOKEN[:15]}...        ║
╚════════════════════════════════════════╝
    """)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi.")
    except Exception as e:
        print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    main()
