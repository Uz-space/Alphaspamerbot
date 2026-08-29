#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRON Telegram Bot - Hamma ma'lumot Telegram orqali so'raladi
Terminalda hech narsa so'ramaydi!
"""

import os
import re
import sys
import time
import json
import base64
import subprocess
import tempfile
import threading
from urllib.parse import urlencode, urlparse, quote_plus

import requests as _http
import urllib3

# Telegram bot
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("Iltimos, telegram kutubxonasini o'rnating: pip install python-telegram-bot --upgrade")
    sys.exit(1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================================
#                    TELEGRAM KONFIGURATSIYA
# ==========================================================

# O'ZGARTIRING! @BotFather dan olingan token
BOT_TOKEN = "8856631856:AAE3fSYI4zfF3KP0EpugrzvYv9u7NXbsfgI"

# O'ZGARTIRING! @userinfobot dan olingan ID
ADMIN_ID = 8758410535

# ==========================================================
#                       KONSTANTALAR
# ==========================================================
title = "TRON"
versi = "1.0.8"
class_require = "1.1.7"
host = "https://tronpick.io/"
youtube = ""

turnstile = ""
recaptcha = "6LeBFBclAAAAANoZIrwXU1cPgYDDM7f1ehHpzXWj"
hcaptcha = ""

MAXWIN_DICE = 1000
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
o2 = "\033[01;38;5;208m"

# ==========================================================
#                    Yordamchi funksiya
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
        return None

# ==========================================================
#                        Requests
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

                cmd = [
                    "curl", "-s", "-k", "-L",
                    "--connect-timeout", "30",
                    "-D", header_file,
                    "-o", body_file,
                ]

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
                    time.sleep(3)
                    continue
                except subprocess.TimeoutExpired:
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
#                        Functions
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
    def setConfig(key, value=None):
        config = Functions._load_config()
        if value is not None:
            config[key] = value
            Functions._save_config(config)
            return value
        if key in config:
            return config[key]
        return None

    @staticmethod
    def getConfig(key):
        config = Functions._load_config()
        return config.get(key)

    @staticmethod
    def removeConfig(key):
        config = Functions._load_config()
        if key in config:
            del config[key]
            Functions._save_config(config)

# ==========================================================
#                        HtmlScrap
# ==========================================================
class HtmlScrap:
    def __init__(self):
        self.captcha_re = r'class=["\']([^"\']+)["\'][^>]*data-sitekey=["\']([^"\']+)["\']'
        self.input_re = r'<input[^>]*name=["\'](.*?)["\'][^>]*value=["\'](.*?)["\']'
        self.limit_re = r'(\d{1,})/(\d{1,})'

    def _scrap(self, pattern, html):
        return re.findall(pattern, html, flags=re.IGNORECASE)

    def _getCaptcha(self, html):
        matches = self._scrap(self.captcha_re, html)
        data = {}
        for cls, sitekey in matches:
            data[cls] = sitekey
        return data

    def _getInput(self, html, form=1):
        parts = html.split("<form")
        if form >= len(parts):
            return {}
        form_html = parts[form]
        matches = self._scrap(self.input_re, form_html)
        data = {}
        for name, value in matches:
            data[name] = value
        return data

    def Result(self, html, form=1):
        data = {}
        try:
            data["title"] = html.split("<title>")[1].split("</title>")[0]
        except IndexError:
            data["title"] = None

        data["cloudflare"] = bool(re.search(r"Just a moment\.\.\.", html))
        data["firewall"] = bool(re.search(r"Firewall", html))
        data["locked"] = bool(re.search(r"Locked", html))
        data["captcha"] = self._getCaptcha(html)

        input_ = self._getInput(html, form)
        data["input"] = input_ if input_ else self._getInput(html, 2)
        data["faucet"] = self._scrap(self.limit_re, html)

        response = {}
        parts = html.split("icon: 'success',")
        sukses = parts[1] if len(parts) > 1 else None

        if sukses:
            inner = sukses.split("html: '")
            if len(inner) > 1:
                response["success"] = re.sub(r"<[^>]+>", "", inner[1].split("'")[0])
        else:
            warning_parts = html.split("html: '")
            warning = warning_parts[1].split("'")[0] if len(warning_parts) > 1 else None

            ban_parts = html.split(
                '<div class="alert text-center alert-danger"><i class="fas fa-exclamation-circle"></i> Your account'
            )
            ban = ban_parts[1].split("</div>")[0] if len(ban_parts) > 1 else None

            invalid = "You are sending an invalid amount" if re.search(r"invalid amount", html) else False
            shortlink = warning if re.search(r"Shortlink in order to claim from the faucet!", html) else False
            sufficient = "Sufficient funds" if re.search(r"sufficient funds", html) else False
            daily = "Daily claim limit" if re.search(r"Daily claim limit", html) else False

            response["unset"] = False
            response["exit"] = False

            if ban:
                response["warning"] = ban
                response["exit"] = True
            elif invalid:
                response["warning"] = invalid
                response["unset"] = True
            elif shortlink:
                response["warning"] = shortlink
                response["exit"] = True
            elif sufficient:
                response["warning"] = sufficient
                response["unset"] = True
            elif warning:
                response["warning"] = warning
            else:
                response["warning"] = "Not Found"

        data["response"] = response
        return data

# ==========================================================
#                         Captcha
# ==========================================================
class Captcha:
    def __init__(self):
        config = Functions._load_config()
        captcha_type = config.get("type", "1")
        
        if captcha_type == "1":
            self.url = "http://api.multibot.in/"
            self.key = config.get("multibot_apikey", "")
            self.provider = "Multibot"
        else:
            self.url = "https://sctg.xyz/"
            self.key = config.get("xevil_apikey", "") + "|SOFTID1204538927"
            self.provider = "Xevil"

    def _in_api(self, content, method, header=0):
        param = f"key={self.key}&json=1&{content}"
        if method == "GET":
            try:
                return json.loads(_http.get(self.url + "in.php?" + param, timeout=30).text)
            except Exception:
                return None
        headers = {}
        if header:
            headers["Content-Type"] = header if isinstance(header, str) else "application/x-www-form-urlencoded"
        return _http.post(self.url + "in.php", data=param, headers=headers, timeout=30).text

    def _res_api(self, api_id):
        params = f"?key={self.key}&action=get&id={api_id}&json=1"
        try:
            return json.loads(_http.get(self.url + "res.php" + params, timeout=30).text)
        except Exception:
            return {}

    def _getResult(self, data, method, header=0):
        try:
            cap = data.split("method=")[1].split("&")[0]
        except:
            cap = "captcha"
            
        get_res = self._in_api(data, method, header)
        try:
            get_in = json.loads(get_res) if isinstance(get_res, str) else get_res
        except:
            return 0

        if not get_in or not get_in.get("status"):
            return 0

        a = 0
        while True:
            get_res = self._res_api(get_in.get("request", 0))
            if not get_res:
                return 0
            if get_res.get("request") == "CAPCHA_NOT_READY":
                a += 10
                time.sleep(1)
                if a > 99:
                    return 0
                continue
            if get_res.get("status"):
                return get_res.get("request", 0)
            return 0

    def getBalance(self):
        try:
            res = json.loads(
                _http.get(self.url + "res.php?action=userinfo&key=" + self.key, timeout=30).text
            )
            return res.get("balance", 0)
        except Exception:
            return 0

    def RecaptchaV2(self, sitekey, pageurl):
        data = urlencode({"method": "userrecaptcha", "sitekey": sitekey, "pageurl": pageurl})
        return self._getResult(data, "GET")

# ==========================================================
#                            Bot
# ==========================================================
class TronBot:
    def __init__(self):
        config = Functions._load_config()
        self.cookie = config.get("cookie", "")
        self.uagent = config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.captcha = Captcha()
        self.scrap = HtmlScrap()
        self.last_balance = "0"
        self.last_username = "Noma'lum"

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
            self.last_username = data["Username"]
        except IndexError:
            data["Username"] = self.last_username

        try:
            data["Balance"] = r.split('class="drop_down_header_text user_balance">')[1].split("<")[0]
            self.last_balance = data["Balance"]
        except IndexError:
            data["Balance"] = self.last_balance

        return data

    def ClaimBonus(self):
        r = Requests.get(host + "faucet.php", self.headers())
        try:
            bonus = r[1].split('<span id="free_spins">')[1].split("</span>")[0]
        except IndexError:
            bonus = None

        if not bonus:
            return {"success": False, "message": "Bonus mavjud emas!"}

        set_cookie_matches = re.findall(r"^Set-Cookie:\s*([^;]*)", r[0], flags=re.MULTILINE | re.IGNORECASE)
        cookies = {}
        for item in set_cookie_matches:
            if "=" in item:
                key_, val_ = item.split("=", 1)
                cookies[key_] = val_

        if recaptcha and re.search(recaptcha, r[1]):
            cap = self.captcha.RecaptchaV2(recaptcha, host + "faucet.php")
            if not cap:
                return {"success": False, "message": "Captcha yechilmadi!"}
            data = "action=claim_bonus_faucet&g-recaptcha-response=" + cap + "&h-captcha-response=null&captcha=&ft=&csrf_test_name=" + cookies.get("csrf_cookie_name", "")
        else:
            data = "action=claim_bonus_faucet&csrf_test_name=" + cookies.get("csrf_cookie_name", "")

        r2 = safe_json_loads(Requests.post(host + "process.php", self.headers(), data)[1], "claim_bonus")
        if r2 is None:
            return {"success": False, "message": "Server javob bermadi!"}
        
        if r2.get("ret"):
            self.Dashboard()
            return {"success": True, "message": r2.get("mes", "Bonus yig'ildi!"), "num": r2.get("num", ""), "balance": self.last_balance}
        else:
            return {"success": False, "message": r2.get("mes", "Noma'lum xatolik!")}

    def HourlyFaucet(self):
        r = Requests.get(host + "faucet.php", self.headers())
        cek = self.scrap.Result(r[1])
        
        if cek.get("cloudflare"):
            return {"success": False, "message": "Cloudflare detected!"}

        set_cookie_matches = re.findall(r"^Set-Cookie:\s*([^;]*)", r[0], flags=re.MULTILINE | re.IGNORECASE)
        cookies = {}
        for item in set_cookie_matches:
            if "=" in item:
                key_, val_ = item.split("=", 1)
                cookies[key_] = val_

        if recaptcha and re.search(recaptcha, r[1]):
            cap = self.captcha.RecaptchaV2(recaptcha, host + "faucet.php")
            if not cap:
                return {"success": False, "message": "Captcha yechilmadi!"}
            data = "action=claim_hourly_faucet&g-recaptcha-response=" + cap + "&h-captcha-response=null&captcha=&ft=&csrf_test_name=" + cookies.get("csrf_cookie_name", "")
        else:
            data = "action=claim_hourly_faucet&csrf_test_name=" + cookies.get("csrf_cookie_name", "")

        r2 = safe_json_loads(Requests.post(host + "process.php", self.headers(), data)[1], "hourly_faucet")
        if r2 is None:
            return {"success": False, "message": "Server javob bermadi!"}
        
        if r2.get("ret"):
            self.Dashboard()
            return {"success": True, "message": r2.get("mes", "Hourly bonus yig'ildi!"), "num": r2.get("num", ""), "balance": self.last_balance}
        else:
            return {"success": False, "message": r2.get("mes", "Noma'lum xatolik!")}

# ==========================================================
#                   TELEGRAM BOT HANDLERLAR
# ==========================================================

user_data = {}
tron_bot = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sizga ruxsat berilmagan!")
        return
    
    global user_data
    user_data[user_id] = {"step": "cookie"}
    
    await update.message.reply_text(
        f"🤖 TRON BOT v{versi}\n\n"
        "📝 Cookie yuboring:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global tron_bot, user_data
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sizga ruxsat berilmagan!")
        return
    
    text = update.message.text.strip()
    
    if user_id not in user_data:
        await update.message.reply_text("❌ /start buyrug'ini bosing!")
        return
    
    step = user_data[user_id].get("step")
    
    if step == "cookie":
        Functions.setConfig("cookie", text)
        user_data[user_id]["step"] = "user_agent"
        await update.message.reply_text(
            "✅ Cookie saqlandi!\n\n"
            "📝 User-Agent yuboring:"
        )
    
    elif step == "user_agent":
        Functions.setConfig("user_agent", text)
        user_data[user_id]["step"] = "captcha_type"
        await update.message.reply_text(
            "✅ User-Agent saqlandi!\n\n"
            "🔑 Captcha xizmatini tanlang:\n"
            "1 - Multibot\n"
            "2 - Xevil"
        )
    
    elif step == "captcha_type":
        if text == "1":
            Functions.setConfig("type", "1")
            user_data[user_id]["step"] = "multibot_key"
            await update.message.reply_text(
                "✅ Multibot tanlandi!\n\n"
                "🔑 Multibot API Key yuboring:"
            )
        elif text == "2":
            Functions.setConfig("type", "2")
            user_data[user_id]["step"] = "xevil_key"
            await update.message.reply_text(
                "✅ Xevil tanlandi!\n\n"
                "🔑 Xevil API Key yuboring:"
            )
        else:
            await update.message.reply_text("❌ 1 yoki 2 yuboring!")
    
    elif step == "multibot_key":
        Functions.setConfig("multibot_apikey", text)
        # Darhol bot yaratish va menyuni chiqarish
        tron_bot = TronBot()
        user_data[user_id]["step"] = "done"
        await update.message.reply_text("✅ API Key saqlandi!")
        # Darhol menyuni chiqarish
        await show_menu(update)
    
    elif step == "xevil_key":
        Functions.setConfig("xevil_apikey", text)
        # Darhol bot yaratish va menyuni chiqarish
        tron_bot = TronBot()
        user_data[user_id]["step"] = "done"
        await update.message.reply_text("✅ API Key saqlandi!")
        # Darhol menyuni chiqarish
        await show_menu(update)
    
    elif step == "done":
        if text == "1":
            await update.message.reply_text("⏳ Bonus yig'ilmoqda...")
            result = tron_bot.ClaimBonus()
            if result['success']:
                msg = f"✅ {result['message']}\n💰 Balance: {result['balance']}"
                if result.get('num'):
                    msg += f"\n🎰 Number: {result['num']}"
            else:
                msg = f"❌ {result['message']}"
            await update.message.reply_text(msg)
            await show_menu(update)
        
        elif text == "2":
            await update.message.reply_text("⏳ Hourly bonus yig'ilmoqda...")
            result = tron_bot.HourlyFaucet()
            if result['success']:
                msg = f"✅ {result['message']}\n💰 Balance: {result['balance']}"
            else:
                msg = f"❌ {result['message']}"
            await update.message.reply_text(msg)
            await show_menu(update)
        
        else:
            await update.message.reply_text("❌ 1 yoki 2 yuboring!")

async def show_menu(update):
    try:
        dashboard = tron_bot.Dashboard()
        username = dashboard.get("Username", "Noma'lum")
        balance = dashboard.get("Balance", "0")
        api_balance = tron_bot.captcha.getBalance()
    except Exception as e:
        username = "Noma'lum"
        balance = "0"
        api_balance = "0"
    
    await update.message.reply_text(
        f"📊 **Dashboard**\n"
        f"👤 Username: {username}\n"
        f"💰 Balance: {balance}\n"
        f"💳 API Balance: {api_balance}\n\n"
        f"📌 **Menyu:**\n"
        f"1 - Bonus yig'ish\n"
        f"2 - Hourly bonus",
        parse_mode='Markdown'
    )

# ==========================================================
#                   ASOSIY FUNKSIYA
# ==========================================================

def main():
    print(f"\n{'='*50}")
    print(f"🤖 TRON Telegram Bot v{versi}")
    print(f"{'='*50}\n")
    print("✅ Telegram orqali boshqariladi!")
    print("📱 Botga /start yozing")
    print("\n🔄 Botni to'xtatish uchun Ctrl+C bosing\n")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi.")
    except Exception as e:
        print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    main()
