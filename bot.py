#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRON Telegram Bot - To'liq birlashtirilgan versiya
tron.py va bot.py birlashtirilgan - Railwayda ishlatish uchun
"""

import os
import re
import sys
import time
import json
import base64
import threading
import subprocess
import tempfile
import logging
from datetime import datetime
from urllib.parse import urlencode, urlparse, quote_plus
from typing import Optional, Dict, Any

import requests as _http
import urllib3

# Telegram bot
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    print("Iltimos, telegram kutubxonasini o'rnating: pip install python-telegram-bot --upgrade")
    sys.exit(1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
r = "\033[38;5;196m"
g = "\033[38;5;46m"
y = "\033[38;5;226m"
b1 = "\033[38;5;21m"
p1 = "\033[38;5;13m"
c1 = "\033[38;5;51m"
gr = "\033[38;5;240m"

# Warna latar belakang
mp = "\033[101m\033[1;37m"
hp = "\033[102m\033[1;30m"
kp = "\033[103m\033[1;37m"
bp = "\033[104m\033[1;37m"
up = "\033[105m\033[1;37m"
cp = "\033[106m\033[1;37m"
pm = "\033[107m\033[1;31m"
ph = "\033[107m\033[1;32m"
pk = "\033[107m\033[1;33m"
pb = "\033[107m\033[1;34m"
pu = "\033[107m\033[1;35m"
pc = "\033[107m\033[1;36m"
yh = d + "\033[43;30m"
bg_r = "\033[48;5;196m"
bg_g = "\033[48;5;46m"
bg_y = "\033[48;5;226m"
bg_b1 = "\033[48;5;21m"
bg_p1 = "\033[48;5;13m"
bg_c1 = "\033[48;5;51m"
bg_gr = "\033[48;5;240m"

# ==========================================================
#                    TELEGRAM KONFIGURATSIYA
# ==========================================================

# O'ZGARTIRING! @BotFather dan olingan token
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# O'ZGARTIRING! @userinfobot dan olingan ID
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================================
#                    YORDAMCHI FUNKSIYALAR
# ==========================================================

def safe_json_loads(s, debug_tag="response"):
    """json.loads ning chidamli versiyasi"""
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
#                        REQUESTS
# ==========================================================

class Requests:
    """Curl orqali so'rov yuborish"""
    
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
                    print(Display.Error("curl dasturi topilmadi!"), end="")
                    time.sleep(3)
                    continue
                except subprocess.TimeoutExpired:
                    print("Check your Connection!")
                    time.sleep(2)
                    continue

                if result.returncode != 0:
                    err = result.stderr.decode(errors="ignore").strip()
                    print(Display.Error("Curl Error : " + err + n), end="")
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

    @staticmethod
    def getXskip(url, head=0):
        return Requests.Curl(url, head, "", "", "", "", 1)

    @staticmethod
    def postXskip(url, head=0, data_post=0):
        return Requests.Curl(url, head, 1, data_post, "", "", 1)

    @staticmethod
    def getXcookie(url, head=0, cookie=0):
        if not cookie:
            cookie = "cookie.txt"
        return Requests.Curl(url, head, "", "", cookie)

    @staticmethod
    def postXcookie(url, head=0, data_post=0, cookie=0):
        if not cookie:
            cookie = "cookie.txt"
        return Requests.Curl(url, head, 1, data_post, cookie)

    @staticmethod
    def getXproxy(url, head=0, proxy=None):
        return Requests.Curl(url, head, "", "", 1, proxy)

    @staticmethod
    def postXproxy(url, head=0, data_post=0, proxy=None):
        return Requests.Curl(url, head, 1, data_post, 1, proxy)

# ==========================================================
#                         DISPLAY
# ==========================================================

class Display:
    """Ekran chiqishlari"""
    
    @staticmethod
    def Clear():
        if os.name == "posix":
            os.system("clear")
        else:
            os.system("cls")

    @staticmethod
    def Menu(no, title_):
        print(f"{h}---[{p}{no}{h}] {k}{title_}\n", end="")

    @staticmethod
    def Cetak(label, msg="[No Content]"):
        length = 9
        lenstr = length - len(label)
        lenstr = max(lenstr, 0)
        print(f"{h}[{p}{label}{h}{' ' * lenstr}]\u2500> {p}{msg}{n}", end="")

    @staticmethod
    def Title(activitas):
        text = activitas.upper()
        pad_total = max(45 - len(text), 0)
        left = pad_total // 2
        right = pad_total - left
        print(f"{bp}{' ' * left}{text}{' ' * right}{d}{n}", end="")

    @staticmethod
    def Line(length=45):
        print(f"{c}{'\u2500' * length}{n}", end="")

    @staticmethod
    def Ban(title_, versi_, server=0):
        Display.Clear()
        line = f"TRON PICK BOT v{versi_}"
        pad_total = max(45 - len(line), 0)
        left = pad_total // 2
        right = pad_total - left
        print("\033[1;36m", end="")
        print("\u2554" + "\u2550" * 40 + "\u2557\n", end="")
        print(f"\u2551{' ' * left}{line}{' ' * right}\u2551\n", end="")
        print("\u255a" + "\u2550" * 40 + "\u255d\n", end="")
        print("\033[0m\n", end="")

    @staticmethod
    def Error(except_):
        return f"{m}---[{p}!{m}] {p}{except_}"

    @staticmethod
    def Sukses(msg):
        return f"{h}---[{p}\u2713{h}] {p}{msg}{n}"

    @staticmethod
    def Isi(msg):
        return f"{m}\u256d[{p}Input {msg}{m}]{n}{m}\u2570> {h}"

# ==========================================================
#                        FUNCTIONS
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
    def Tmr(tmr):
        os.environ["TZ"] = "UTC"
        try:
            time.tzset()
        except AttributeError:
            pass
        sym = [" \u2500 ", " / ", " \u2502 ", " \\ "]
        timr = time.time() + tmr
        a = 0
        while True:
            a += 1
            res = timr - time.time()
            if res < 1:
                break
            t = time.gmtime(res)
            print(
                f"{sym[a % 4]}{p}{time.strftime('%H', t)}:{p}{time.strftime('%M', t)}:{p}{time.strftime('%S', t)}\r",
                end="",
            )
            time.sleep(0.1)
        print("\r           \r", end="")

    @staticmethod
    def setConfig(key):
        config = Functions._load_config()
        if key in config:
            return config[key]
        print(Display.Isi(key), end="")
        data = input()
        print(n, end="")
        config[key] = data
        Functions._save_config(config)
        return data

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

    @staticmethod
    def HiddenConfig(key, data):
        config = Functions._load_config()
        if not config.get(key):
            config[key] = data
            Functions._save_config(config)
        return config[key]

# ==========================================================
#                        HTMLSCRAP
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
            ban_parts = html.split('<div class="alert text-center alert-danger"><i class="fas fa-exclamation-circle"></i> Your account')
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
#                         CAPTCHA
# ==========================================================

class Captcha:
    def __init__(self):
        self.config = Functions._load_config()
        self.provider = self.config.get("provider", "Multibot")
        
        # API key ni olish
        if self.provider == "Multibot":
            self.url = "http://api.multibot.in/"
            self.key = self.config.get("multibot_apikey", "")
        else:
            self.url = "https://sctg.xyz/"
            self.key = self.config.get("xevil_apikey", "") + "|SOFTID1204538927"

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

    def _solvingProgress(self, xr, tmr, cap):
        if xr < 50:
            wr = h
        elif 50 <= xr < 80:
            wr = k
        else:
            wr = m
        xwr = [wr, p, wr, p]
        sym = [" \u2500 ", " / ", " \u2502 ", " \\ "]
        a = 0
        for i in range(tmr * 4, 0, -1):
            print(f"{xwr[a % 4]} Bypass {cap} {xr}%{sym[a % 4]} \r", end="")
            time.sleep(0.1)
            if xr < 99:
                xr += 1
            a += 1
        return xr

    def _getResult(self, data, method, header=0):
        cap = self._filter(data.split("method=")[1].split("&")[0])
        get_res = self._in_api(data, method, header)
        get_in = get_res if isinstance(get_res, dict) else json.loads(get_res or "{}")

        if not get_in.get("status"):
            msg = get_in.get("request")
            if msg:
                print(Display.Error(f"in_api @{self.provider} {msg}{n}"), end="")
            elif get_res:
                print(Display.Error(f"{get_res}{n}"), end="")
            else:
                print(Display.Error(f"in_api @{self.provider} something wrong\n"), end="")
            return 0

        a = 0
        while True:
            print(f" Bypass {cap} {a}% |   \r", end="")
            get_res = self._res_api(get_in["request"])
            if get_res.get("request") == "CAPCHA_NOT_READY":
                import random
                ran = random.randint(5, 10)
                a += ran
                if a > 99:
                    a = 99
                print(f" Bypass {cap} {a}% \u2500 \r", end="")
                a = self._solvingProgress(a, 5, cap)
                continue
            if get_res.get("status"):
                print(f" Bypass {cap} 100%", end="")
                time.sleep(1)
                print("\r                              \r", end="")
                print(f"{h}[{p}\u221a{h}] Bypass {cap} success", end="")
                time.sleep(2)
                print("\r                              \r", end="")
                return get_res["request"]
            print(f"{m}[{p}!{m}] Bypass {cap} failed", end="")
            time.sleep(2)
            print("\r                              \r", end="")
            print(Display.Error(f"{cap} @{self.provider} Error\n"), end="")
            return 0

    def _filter(self, method):
        mapping = {
            "userrecaptcha": "RecaptchaV2",
            "hcaptcha": "Hcaptcha",
            "turnstile": "Turnstile",
            "universal": "Ocr",
            "base64": "Ocr",
            "antibot": "Antibot",
            "authkong": "Authkong",
            "teaserfast": "Teaserfast",
        }
        return mapping.get(method)

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

    def Hcaptcha(self, sitekey, pageurl):
        data = urlencode({"method": "hcaptcha", "sitekey": sitekey, "pageurl": pageurl})
        return self._getResult(data, "GET")

    def Turnstile(self, sitekey, pageurl):
        data = urlencode({"method": "turnstile", "sitekey": sitekey, "pageurl": pageurl})
        return self._getResult(data, "GET")

# ==========================================================
#                            BOT
# ==========================================================

class TronBot:
    def __init__(self):
        self.config = Functions._load_config()
        self.cookie = self.config.get("cookie", "")
        self.uagent = self.config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.captcha = Captcha()
        self.scrap = HtmlScrap()
        self.is_running = False
        self.last_balance = "0"
        self.last_api_balance = "0"
        self.last_username = "Noma'lum"
        self.start_time = time.time()

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

        try:
            self.last_api_balance = str(self.captcha.getBalance())
            data["Bal_Api"] = self.last_api_balance
        except Exception:
            data["Bal_Api"] = "0"

        return data

    def _getCsrf(self):
        cookie = self.cookie
        data = {}
        for e in cookie.split(";"):
            e = e.strip()
            if "=" in e:
                key_, val_ = e.split("=", 1)
                data[key_] = val_
        return data.get("csrf_cookie_name")

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

        # Captcha tekshirish
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

        try:
            tmr = r[1].split("select_hourly_faucet|")[1].split("|")[0]
        except IndexError:
            tmr = None

        set_cookie_matches = re.findall(r"^Set-Cookie:\s*([^;]*)", r[0], flags=re.MULTILINE | re.IGNORECASE)
        cookies = {}
        for item in set_cookie_matches:
            if "=" in item:
                key_, val_ = item.split("=", 1)
                cookies[key_] = val_

        # Captcha tekshirish
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

    def get_status(self):
        self.Dashboard()
        uptime = int(time.time() - self.start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        seconds = uptime % 60
        
        return {
            "status": "Ishlamoqda" if self.is_running else "To'xtatilgan",
            "username": self.last_username,
            "balance": self.last_balance,
            "api_balance": self.last_api_balance,
            "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "version": versi
        }

# ==========================================================
#                   TELEGRAM BOT MANAGER
# ==========================================================

class TronBotManager:
    def __init__(self):
        self.tron_bot = None
        self.is_running = False
        self.claim_thread = None
        self.stop_claim = False

    def init_bot(self):
        try:
            self.tron_bot = TronBot()
            self.is_running = True
            self.tron_bot.is_running = True
            status = self.tron_bot.get_status()
            return True, f"Bot muvaffaqiyatli ishga tushirildi!\n👤 {status['username']}\n💰 {status['balance']}"
        except Exception as e:
            logger.error(f"Bot ishga tushirishda xatolik: {e}")
            return False, f"Xatolik: {str(e)}"

    def get_status(self):
        if self.tron_bot and self.is_running:
            return self.tron_bot.get_status()
        return {
            "status": "To'xtatilgan",
            "username": "Noma'lum",
            "balance": "0",
            "api_balance": "0",
            "uptime": "00:00:00",
            "version": versi
        }

    def claim_bonus(self):
        if not self.tron_bot or not self.is_running:
            return {"success": False, "message": "Bot ishlamayapti!"}
        return self.tron_bot.ClaimBonus()

    def claim_hourly(self):
        if not self.tron_bot or not self.is_running:
            return {"success": False, "message": "Bot ishlamayapti!"}
        return self.tron_bot.HourlyFaucet()

    def auto_claim_start(self):
        if self.claim_thread and self.claim_thread.is_alive():
            return {"success": False, "message": "Avtomatik yig'ish allaqachon ishlamoqda!"}
        
        self.stop_claim = False
        self.claim_thread = threading.Thread(target=self._auto_claim_loop)
        self.claim_thread.daemon = True
        self.claim_thread.start()
        return {"success": True, "message": "Avtomatik bonus yig'ish boshlandi!"}

    def auto_claim_stop(self):
        self.stop_claim = True
        if self.claim_thread:
            self.claim_thread.join(timeout=5)
        return {"success": True, "message": "Avtomatik bonus yig'ish to'xtatildi!"}

    def _auto_claim_loop(self):
        while not self.stop_claim:
            try:
                self.claim_bonus()
                time.sleep(30)
                self.claim_hourly()
                time.sleep(3600)
            except Exception as e:
                logger.error(f"Avtomatik yig'ishda xatolik: {e}")
                time.sleep(60)

    def set_config(self, key, value):
        config = Functions._load_config()
        config[key] = value
        Functions._save_config(config)
        
        # TRON bot konfiguratsiyasini yangilash
        if self.tron_bot:
            if key == "cookie":
                self.tron_bot.cookie = value
            elif key == "user_agent":
                self.tron_bot.uagent = value
            elif key == "multibot_apikey" or key == "xevil_apikey":
                self.tron_bot.captcha = Captcha()
        
        return {"success": True, "message": f"{key} o'zgartirildi!"}

# ==========================================================
#                   TELEGRAM BOT HANDLERLAR
# ==========================================================

bot_manager = TronBotManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sizga ruxsat berilmagan!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🚀 Botni Ishga Tushirish", callback_data="start_bot")],
        [InlineKeyboardButton("📊 Holat", callback_data="status")],
        [InlineKeyboardButton("💰 Bonus Yig'ish", callback_data="claim_bonus")],
        [InlineKeyboardButton("🕐 Hourly Bonus", callback_data="claim_hourly")],
        [InlineKeyboardButton("🔄 Avtomatik Yig'ish", callback_data="auto_claim")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        [InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🤖 **TRON BOT v{versi}**\n\nBotni boshqarish uchun tugmalardan foydalaning:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Sizga ruxsat berilmagan!")
        return
    
    data = query.data
    
    if data == "start_bot":
        success, message = bot_manager.init_bot()
        await query.edit_message_text(
            f"{'✅' if success else '❌'} {message}",
            reply_markup=await get_main_keyboard()
        )
    
    elif data == "status":
        status = bot_manager.get_status()
        text = (
            f"📊 **Bot Holati**\n\n"
            f"🔹 Holat: {status['status']}\n"
            f"👤 Username: {status['username']}\n"
            f"💰 Balance: {status['balance']}\n"
            f"💳 API Balance: {status['api_balance']}\n"
            f"⏱️ Ish vaqti: {status['uptime']}\n"
            f"📦 Versiya: {status['version']}"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=await get_main_keyboard())
    
    elif data == "claim_bonus":
        await query.edit_message_text("⏳ Bonus yig'ilmoqda...", reply_markup=await get_main_keyboard())
        result = bot_manager.claim_bonus()
        if result['success']:
            text = f"✅ {result['message']}\n💰 Balance: {result.get('balance', 'Noma'lum')}"
            if result.get('num'):
                text += f"\n🎰 Number: {result['num']}"
        else:
            text = f"❌ {result['message']}"
        await query.edit_message_text(text, reply_markup=await get_main_keyboard())
    
    elif data == "claim_hourly":
        await query.edit_message_text("⏳ Hourly bonus yig'ilmoqda...", reply_markup=await get_main_keyboard())
        result = bot_manager.claim_hourly()
        if result['success']:
            text = f"✅ {result['message']}\n💰 Balance: {result.get('balance', 'Noma'lum')}"
        else:
            text = f"❌ {result['message']}"
        await query.edit_message_text(text, reply_markup=await get_main_keyboard())
    
    elif data == "auto_claim":
        keyboard = [
            [InlineKeyboardButton("▶️ Boshlash", callback_data="auto_start")],
            [InlineKeyboardButton("⏹️ To'xtatish", callback_data="auto_stop")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔄 **Avtomatik Bonus Yig'ish**\n\nAvtomatik rejimda bot har 30 soniyada bonus va har soatda hourly bonus yig'adi.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data == "auto_start":
        result = bot_manager.auto_claim_start()
        await query.edit_message_text(
            f"{'✅' if result['success'] else '❌'} {result['message']}",
            reply_markup=await get_main_keyboard()
        )
    
    elif data == "auto_stop":
        result = bot_manager.auto_claim_stop()
        await query.edit_message_text(
            f"{'✅' if result['success'] else '❌'} {result['message']}",
            reply_markup=await get_main_keyboard()
        )
    
    elif data == "settings":
        keyboard = [
            [InlineKeyboardButton("🍪 Cookie Sozlash", callback_data="set_cookie")],
            [InlineKeyboardButton("🔄 User-Agent Sozlash", callback_data="set_useragent")],
            [InlineKeyboardButton("🔑 Multibot API Key", callback_data="set_multibot")],
            [InlineKeyboardButton("🔑 Xevil API Key", callback_data="set_xevil")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⚙️ **Sozlamalar**\n\nSozlamani tanlang:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data in ["set_cookie", "set_useragent", "set_multibot", "set_xevil"]:
        context.user_data['setting'] = data.replace("set_", "")
        names = {
            "cookie": "🍪 Cookie",
            "useragent": "🔄 User-Agent",
            "multibot": "🔑 Multibot API Key",
            "xevil": "🔑 Xevil API Key"
        }
        await query.edit_message_text(
            f"{names.get(context.user_data['setting'], 'Sozlama')}\n\nIltimos, yangi qiymatni kiriting:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]])
        )
    
    elif data == "info":
        text = (
            f"ℹ️ **TRON BOT v{versi}**\n\n"
            "Bot TRON saytida avtomatik ravishda bonus yig'ish uchun mo'ljallangan.\n\n"
            "📌 **Xususiyatlar:**\n"
            "• Bonus yig'ish\n"
            "• Hourly bonus yig'ish\n"
            "• Avtomatik rejim\n"
            "• Balans kuzatish\n"
            "• Cookie boshqarish\n\n"
            "🔗 Sayt: https://tronpick.io/"
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=await get_main_keyboard())
    
    elif data == "back":
        await query.edit_message_text(
            "🏠 **Asosiy menyu**",
            parse_mode='Markdown',
            reply_markup=await get_main_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Sizga ruxsat berilmagan!")
        return
    
    text = update.message.text
    
    if context.user_data.get('setting'):
        setting = context.user_data['setting']
        result = bot_manager.set_config(setting, text)
        await update.message.reply_text(
            f"{'✅' if result['success'] else '❌'} {result['message']}"
        )
        context.user_data['setting'] = None
        await update.message.reply_text(
            "🏠 Asosiy menyu",
            reply_markup=await get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "❓ Tushunarsiz buyruq. /start ni bosing.",
            reply_markup=await get_main_keyboard()
        )

async def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚀 Botni Ishga Tushirish", callback_data="start_bot")],
        [InlineKeyboardButton("📊 Holat", callback_data="status")],
        [InlineKeyboardButton("💰 Bonus Yig'ish", callback_data="claim_bonus")],
        [InlineKeyboardButton("🕐 Hourly Bonus", callback_data="claim_hourly")],
        [InlineKeyboardButton("🔄 Avtomatik Yig'ish", callback_data="auto_claim")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        [InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================================
#                   ASOSIY FUNKSIYA
# ==========================================================

def main():
    print(f"\n{'='*50}")
    print(f"🤖 TRON Telegram Bot v{versi}")
    print(f"{'='*50}\n")
    
    # Environment variables tekshirish
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ XATOLIK: BOT_TOKEN environment variable ni o'rnating!")
        print("   Railwayda: Environment Variables → BOT_TOKEN")
        print("   Yoki bot.py da BOT_TOKEN ni o'zgartiring")
        sys.exit(1)
    
    if ADMIN_ID == 123456789:
        print("❌ XATOLIK: ADMIN_ID environment variable ni o'rnating!")
        print("   Railwayda: Environment Variables → ADMIN_ID")
        print("   Yoki bot.py da ADMIN_ID ni o'zgartiring")
        sys.exit(1)
    
    print(f"✅ Bot ishga tushmoqda...")
    print(f"   Admin ID: {ADMIN_ID}")
    print(f"   Token: {BOT_TOKEN[:15]}...")
    print("\n🔄 Botni to'xtatish uchun Ctrl+C bosing\n")
    
    # Bot yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Botni ishga tushirish
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi.")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
