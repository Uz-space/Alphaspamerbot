#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import json
import base64
import subprocess
import tempfile
import threading
import logging
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse, quote_plus

import requests as _http
import urllib3

# ==========================================================
#                    TELEGRAM BOT
# ==========================================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Bot tokeni
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"

# Papkalar
BASE_DIR = Path(__file__).parent.absolute()
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for dir_name in [SCRIPTS_DIR, LOGS_DIR, CONFIG_DIR]:
    dir_name.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================================
#                    TRON SKRIPT (TO'LIQ)
# ==========================================================

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
        try:
            with open(f"debug_{debug_tag}.txt", "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
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
                    print(Display.Error("curl dasturi topilmadi!\n"), end="")
                    time.sleep(3)
                    continue
                except subprocess.TimeoutExpired:
                    print("Check your Connection!")
                    time.sleep(2)
                    print("\r                         \r", end="")
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
                    print("\r                         \r", end="")
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
#                         Display
# ==========================================================
class Display:
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
        api = Display.ipApi()
        Display.Clear()
        if api:
            os.environ["TZ"] = api.get("timezone", "UTC")
            try:
                time.tzset()
            except AttributeError:
                pass
            line = f"{api.get('city','')}, {api.get('regionName','')}, {api.get('country','')}"
            pad_total = max(45 - len(line), 0)
            left = pad_total // 2
            right = pad_total - left
            print(f"{' ' * left}{line}{' ' * right}{n}", end="")

        print("\033[1;36m", end="")
        print("\u2554" + "\u2550" * 40 + "\u2557\n", end="")
        print(f"\u2551          TRONPICK BOT v{versi_}      \u2551\n", end="")
        print("\u255a" + "\u2550" * 40 + "\u255d\n", end="")
        print("\033[0m\n", end="")

        label = "ALPHA PREMIUM SCRIPT"
        pad_total = max(45 - len(label), 0)
        left = pad_total // 2
        right = pad_total - left
        print(f"{mp}{' ' * left}{label}{' ' * right}{d}{n}{n}", end="")

    @staticmethod
    def ipApi():
        try:
            r = json.loads(_http.get("http://ip-api.com/json", timeout=10).text)
            if r.get("status") == "success":
                return r
        except Exception:
            return None
        return None

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
    def view(youtube_):
        tanggal = time.strftime("%d%m%y")
        config = Functions._load_config()
        view_ = config.get("view")
        if tanggal == view_:
            return 0
        config["view"] = tanggal
        if os.name == "posix":
            os.system(f"termux-open-url {youtube_}")
        else:
            os.system(f"start {youtube_}")
        Functions._save_config(config)

    @staticmethod
    def HiddenConfig(key, data):
        config = Functions._load_config()
        if not config.get(key):
            config[key] = data
            Functions._save_config(config)
        return config[key]

    @staticmethod
    def temporary(newdata, data=0):
        if not data:
            data = {}
        merged = dict(data)
        merged.update(newdata)
        return merged

    @staticmethod
    def cfDecodeEmail(encodedString):
        kk = int(encodedString[0:2], 16)
        email = ""
        i = 2
        while i < len(encodedString) - 1:
            email += chr(int(encodedString[i:i + 2], 16) ^ kk)
            i += 2
        return email

    @staticmethod
    def getConfig(key):
        config = Functions._load_config()
        return config.get(key)

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
    def __init__(self, config_data=None):
        self.config_data = config_data or {}
        self._setup_captcha()

    def _setup_captcha(self):
        # Agar konfiguratsiyada type bo'lmasa, Multibot default
        captcha_type = self.config_data.get('type', '1')
        
        if captcha_type == "1":
            self.url = "http://api.multibot.in/"
            self.key = self.config_data.get('multibot_apikey', '')
            self.provider = "Multibot"
        else:
            self.url = "https://sctg.xyz/"
            self.key = self.config_data.get('xevil_apikey', '') + "|SOFTID1204538927"
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
            return res.get("balance")
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

    def Authkong(self, sitekey, pageurl):
        data = urlencode({"method": "authkong", "sitekey": sitekey, "pageurl": pageurl})
        return self._getResult(data, "GET")

    def Ocr(self, img):
        if self.provider == "Xevil":
            data = f"method=base64&body={img}"
        else:
            data = urlencode({"method": "universal", "body": img})
        return self._getResult(data, "POST")

    def AntiBot(self, source):
        try:
            main = source.split("Bot links")[1].split("data:image/png;base64,")[1].split('"')[0]
        except IndexError:
            return 0
        if not main:
            return 0

        if self.provider == "Xevil":
            data = f"method=antibot&main={main}"
        else:
            data = {"method": "antibot", "main": main}

        src = source.split(r'rel=\"')
        for xidx, sour in enumerate(src):
            if xidx == 0:
                continue
            no = sour.split('\\"')[0]
            if self.provider == "Xevil":
                img = sour.split("data:image/png;base64,")[1].split('\\"')[0]
                data += f"&{no}={img}"
            else:
                img = sour.split('src=\\"')[1].split('\\"')[0]
                data[no] = img

        if self.provider == "Xevil":
            res = self._getResult(data, "POST")
        else:
            data = urlencode(data)
            ua = "application/x-www-form-urlencoded"
            res = self._getResult(data, "POST", ua)

        if res:
            return "+" + str(res).replace(",", "+")
        return 0

    def Teaserfast(self, main, small):
        if self.provider == "Multibot":
            return {"error": True, "msg": "not support key!"}
        data = urlencode({"method": "teaserfast", "main_photo": main, "task": small})
        ua = "application/x-www-form-urlencoded"
        return self._getResult(data, "POST", ua)

# ==========================================================
#                          Iewil
# ==========================================================
class Iewil:
    def __init__(self, apikey=None):
        self.url = "https://iewilbot.my.id/res.php"
        self.apikey = apikey

    def _requests(self, postParameter):
        try:
            resp = _http.post(self.url, data=postParameter, timeout=30)
            if resp.status_code != 200:
                return json.dumps({"status": 0, "message": f"iewilbot HTTP code {resp.status_code}"})
            return resp.text
        except Exception as e:
            return json.dumps({"status": 0, "message": str(e)})

    def _getResult(self, postParameter):
        try:
            r = json.loads(self._requests(postParameter))
        except Exception:
            r = None

        if r and r.get("status"):
            return r.get("result")
        if r and r.get("msg"):
            print(str(r["msg"])[:30], end="")
            time.sleep(2)
            print("\r                                   \r", end="")
        if not r:
            print("captcha cannot be solve", end="")
            time.sleep(2)
            print("\r                                   \r", end="")
        return None

    def IconCoordiant(self, base64Img):
        postParameter = urlencode({"img": base64Img, "method": "icon_coordinat"})
        return self._getResult(postParameter)

    def Turnstile(self, sitekey, pageurl):
        postParameter = urlencode({"pageurl": pageurl, "sitekey": sitekey, "method": "turnstile"})
        return self._getResult(postParameter)

    def gp(self, src):
        postParameter = urlencode({"main": base64.b64encode(src.encode()).decode(), "method": "gp"})
        return self._getResult(postParameter)

    def altcha(self, signature, salt, challenge):
        postParameter = urlencode(
            {"signature": signature, "salt": salt, "challenge": challenge, "method": "altcha"}
        )
        return self._getResult(postParameter)

    def Antibot(self, source):
        data = {"method": "antibot"}
        try:
            main = source.split("Bot links")[1].split('src="')[1].split('"')[0]
        except IndexError:
            main = None
        data["main"] = main

        src = source.split(r'rel=\"')
        for xidx, sour in enumerate(src):
            if xidx == 0:
                continue
            no = sour.split('\\"')[0]
            img = sour.split('src=\\"')[1].split('\\"')[0]
            data[no] = img

        postParameter = urlencode(data)
        try:
            cap = json.loads(
                _http.post("https://iewilbot.my.id/res.php", data=postParameter, timeout=30).text
            )
        except Exception:
            return 0
        if not cap.get("status"):
            return 0
        return cap.get("result")

# ==========================================================
#                        FreeCaptcha
# ==========================================================
class FreeCaptcha:
    @staticmethod
    def Icon_hash(header):
        url = host + "system/libs/captcha/request.php"
        head = header + ["X-Requested-With: XMLHttpRequest"]
        getCap = json.loads((Requests.post(url, head, "cID=0&rT=1&tM=light") or [None, "{}"])[1])
        if not getCap:
            url = host + "src/captcha-request.php"
            getCap = json.loads((Requests.post(url, head, "cID=0&rT=1&tM=light") or [None, "{}"])[1])

        head2 = header + ["accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"]
        data = {}
        for cid in getCap:
            resp = Requests.get(f"{url}?cid=0&hash={cid}", head2)
            data[cid] = base64.b64encode(resp[1].encode() if isinstance(resp[1], str) else resp[1]).decode()

        data_enc = urlencode(data)
        cap = json.loads((Requests.post("https://iewilbot.my.id/res.php", "", data_enc) or [None, "{}"])[1])
        if not cap.get("status"):
            return 0
        Requests.postXskip(url, head, f"cID=0&pC={cap['result']}&rT=2")
        return cap.get("result")

# ==========================================================
#                        Cloudflare
# ==========================================================
class Cloudflare:
    def __init__(self):
        self.python = (
            "aW1wb3J0IG9zLCBzeXMsIHRpbWUsIGpzb24KZnJvbSBzZWxlZHJvaWQgaW1wb3J0IHdlYmRyaXZlcgpmcm9tIHNlbGVkcm9pZC53ZWJkcml2ZXIuY29tbW9uLmJ5IGltcG9ydCBCeQoKZHJpdmVyID0gd2ViZHJpdmVyLkNocm9tZShndWk9RmFsc2UpCmhvc3QgPSBzeXMuYXJndlsxXQoKZGVmIENsb3VkZmxhcmUoKToKCXRpdGxlID0gZHJpdmVyLnRpdGxlCglpZiBhbnkoc3ViLmxvd2VyKCkgaW4gdGl0bGUubG93ZXIoKSBmb3Igc3ViIGluIFsiY2xvdWRmbGFyZSIsImp1c3QgYSBtb21lbnQuLi4iXSk6CgkJdGltZS5zbGVlcCgxMCkKCQlyZXR1cm4gRmFsc2UKCWVsc2U6CgkJcmV0dXJuIFRydWUKCnRyeToKCWRyaXZlci5nZXQoaG9zdCkKCXdoaWxlIG5vdCBDbG91ZGZsYXJlKCk6CgkJdGltZS5zbGVlcCgzKQoJCgljZl9jbGVhcmFuY2UgPSBkcml2ZXIuZ2V0X2Nvb2tpZSgiY2ZfY2xlYXJhbmNlIikKCXVzZXJfYWdlbnQgPSBkcml2ZXIudXNlcl9hZ2VudApleGNlcHQgRXhjZXB0aW9uIGFzIGU6CglwcmludChmIntlfSIpCmZpbmFsbHk6Cgl0aXRsZSA9IGRyaXZlci50aXRsZQoJaWYgYW55KHN1Yi5sb3dlcigpIGluIHRpdGxlLmxvd2VyKCkgZm9yIHN1YiBpbiBbImNsb3VkZmxhcmUiLCJqdXN0IGEgbW9tZW50Li4uIl0pOgoJCWRhdGEgPSB7CgkJImNmX2NsZWFyYW5jZSIgOiBGYWxzZSwKCQkidXNlci1hZ2VudCIgOiB1c2VyX2FnZW50CgkJfQoJZWxzZToKCQlkYXRhID0gewoJCSJjZl9jbGVhcmFuY2UiIDogY2ZfY2xlYXJhbmNlLnNwbGl0KCI9IilbMV0sCgkJInVzZXItYWdlbnQiIDogdXNlcl9hZ2VudAoJCX0KCXdpdGggb3BlbignY2YuanNvbicsICd3JykgYXMgZmlsZToKCQlqc29uLmR1bXAoZGF0YSwgZmlsZSwgaW5kZW50PTQpCglkcml2ZXIuY2xvc2UoKQo="
        )
        self.JsonFile = "tronpick_config.json"
        self.pythonFile = "cf.py"
        self.bypassFile = "cf.json"

    def _getOriConfig(self):
        with open(self.JsonFile, "r") as f:
            config = json.load(f)
        return [config.get("cookie"), config.get("user_agent")]

    def BypassCf(self, host_):
        with open(self.pythonFile, "wb") as f:
            f.write(base64.b64decode(self.python))
        time.sleep(2)
        subprocess.run(["python", self.pythonFile, host_])
        time.sleep(2)
        os.remove(self.pythonFile)
        return self._editConfig()

    def _editConfig(self):
        getOriConfig = self._getOriConfig()
        with open(self.bypassFile, "r") as f:
            new_data = json.load(f)
        new_cf_clearance = new_data.get("cf_clearance")
        os.remove(self.bypassFile)

        cf_clearance_ori = getOriConfig[0].split("cf_clearance=")[1].split(";")[0]
        data = {
            "cookie": getOriConfig[0].replace(cf_clearance_ori, new_cf_clearance),
            "user-agent": new_data.get("user-agent"),
        }
        return data

# ==========================================================
#                            Bot
# ==========================================================
if class_version < class_require:
    print("\033[1;31mVersi class sudah kadaluarsa\n", end="")
    sys.exit()

class BotTRON:
    def __init__(self, bot_context=None, user_id=None, config_data=None):
        self.bot_context = bot_context
        self.user_id = user_id
        self.config_data = config_data or {}
        
        # Konfiguratsiyani faylga yozish
        config_file = "tronpick_config.json"
        with open(config_file, 'w') as f:
            json.dump(self.config_data, f, indent=4)
        
        os.system("cls" if os.name == "nt" else "clear")
        print("\033[1;36m", end="")
        print("\u2554" + "\u2550" * 40 + "\u2557\n", end="")
        print(f"\u2551         TRONPICK BOT v{versi}      \u2551\n", end="")
        print("\u255a" + "\u2550" * 40 + "\u255d\n", end="")
        print("\033[0m\n", end="")

        self.iewil = None
        self._enter_cookie_flow()

    def send_output(self, message):
        if self.bot_context and self.user_id:
            try:
                self.bot_context.bot.send_message(
                    chat_id=int(self.user_id),
                    text=message
                )
            except Exception as e:
                print(f"Send error: {e}")
        print(message)

    def _enter_cookie_flow(self):
        while True:
            if not Functions.getConfig("cookie"):
                Display.Line()

            self.cf = Cloudflare()
            self.cookie = Functions.setConfig("cookie")
            self.uagent = Functions.setConfig("user_agent")
            self.captcha = Captcha(self.config_data)

            if len(sys.argv) > 1:
                try:
                    cek = json.loads(
                        _http.get("https://api-iewil.my.id/getInfo?key=" + sys.argv[1], timeout=30).text
                    )
                except Exception:
                    cek = {}
                self.iewil = Iewil(sys.argv[1]) if cek.get("status") else None

            if self.iewil:
                Display.Line()
                print(Display.Sukses("pertamax status is activated"), end="")
                time.sleep(5)

            self.scrap = HtmlScrap()

            Display.Ban(title, versi, 1)

            if self._dashboard_flow():
                continue
            break

        self._menu_flow()

    def _dashboard_flow(self):
        retry = 0
        cloudflare_flag = False
        while True:
            r = self.Dashboard()
            if r.get("cloudflare"):
                cloudflare_flag = True
                print(Display.Error("Cloudflare detect\n"), end="")
                Display.Line()
                print(Display.Error(f"Bypass Cloudflare {retry}"), end="")
                cf = self.cf.BypassCf(host)
                self.cookie = cf["cookie"]
                self.uagent = cf["user-agent"]
                time.sleep(2)
                print("\r                              \r", end="")
                retry += 1
                if retry > 3:
                    Functions.removeConfig("cookie")
                    Functions.removeConfig("user_agent")
                    return True
                continue

            if cloudflare_flag:
                print(Display.Sukses("Cloudflare bypassed"), end="")
                Display.Line()

            if not r.get("Login"):
                Functions.removeConfig("cookie")
                Functions.removeConfig("user_agent")
                print(Display.Error("Cookie Expired\n"), end="")
                Display.Line()
                return True

            Display.Cetak("Username", r["Username"])
            Display.Cetak("Balance", r["Balance"])
            Display.Cetak("Bal_Api", self.captcha.getBalance())
            Display.Line()
            return False

    def _menu_flow(self):
        while True:
            r = Requests.get(host + "faucet.php", self.headers())
            try:
                bonus = r[1].split('<span id="free_spins">')[1].split("</span>")[0]
            except IndexError:
                bonus = ""

            Display.Menu(1, f"Claim Bonus [{bonus}]")
            Display.Menu(2, "Hourly Bonus [Unlimited]")
            print(Display.Isi("Nomor"), end="")
            pil = input()

            Display.Line()
            if pil == "1":
                self.ClaimBonus()
            if pil == "2":
                if self.HourlyFaucet():
                    Functions.removeConfig("cookie")
                    Functions.removeConfig("user_agent")
                    self._enter_cookie_flow()
                    return

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

        matches = re.findall(r'<b id="(total_wagered|wagering_target)">([^<]+)</b>', r)
        values = [v for _, v in matches]
        data["Total Wagered"] = values[0] if len(values) > 0 else None
        data["Wagering Target"] = values[1] if len(values) > 1 else None

        try:
            data["Level"] = (
                r.split("Your level is  <b>")[1].split("</b>")[0]
                + " "
                + r.split('aria-valuemax="100">')[1].split("</div>")[0]
            )
        except IndexError:
            data["Level"] = None

        try:
            data["Username"] = r.split("&username=")[1].split("&")[0].strip()
        except IndexError:
            data["Username"] = None

        try:
            data["Balance"] = r.split('class="drop_down_header_text user_balance">')[1].split("<")[0]
        except IndexError:
            data["Balance"] = None

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

    def HourlyFaucet(self):
        retry = 0
        cloudflare_flag = False
        while True:
            r = Requests.get(host + "faucet.php", self.headers())
            cek = self.scrap.Result(r[1])
            if cek.get("cloudflare"):
                cloudflare_flag = True
                print(Display.Error("Cloudflare Detect\n"), end="")
                Display.Line()
                print(Display.Error(f"Bypass Cloudflare {retry}"), end="")
                cf = self.cf.BypassCf(host)
                self.cookie = cf["cookie"]
                self.uagent = cf["user-agent"]
                time.sleep(2)
                print("\r                              \r", end="")
                retry += 1
                if retry > 3:
                    return 1
                continue

            if cloudflare_flag:
                print(Display.Sukses("Cloudflare bypassed"), end="")
                Display.Line()
                cloudflare_flag = False

            retry = 0
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

            recaptcha_ = recaptcha
            turnstile_ = turnstile
            hcaptcha_ = hcaptcha

            if recaptcha_ and re.search(recaptcha_, r[1]):
                cap = self.captcha.RecaptchaV2(recaptcha_, host + "faucet.php")
                if not cap:
                    continue
                data = (
                    "action=claim_hourly_faucet&g-recaptcha-response="
                    + cap
                    + "&h-captcha-response=null&captcha=&ft=&csrf_test_name="
                    + cookies.get("csrf_cookie_name", "")
                )
            elif turnstile_ and re.search(turnstile_, r[1]):
                cap = (
                    self.iewil.Turnstile(turnstile_, host + "faucet.php")
                    if self.iewil
                    else self.captcha.Turnstile(turnstile_, host + "faucet.php")
                )
                if not cap:
                    continue
                data = (
                    "action=claim_hourly_faucet&clbt=1&g-recaptcha-response=null&captcha=&h-captcha-response=null&c_captcha_response="
                    + cap
                    + "&csrf_test_name="
                    + cookies.get("csrf_cookie_name", "")
                )
            else:
                print(Display.Error("Sitekey Error\n"), end="")
                continue

            r2 = safe_json_loads(Requests.post(host + "process.php", self.headers(), data)[1], "hourly_faucet")
            if r2 is None:
                print(Display.Error(
                    "Server javobini o'qib bo'lmadi (JSON emas). Qayta urinilyapti...\n"
                ), end="")
                time.sleep(3)
                continue
            if r2.get("ret"):
                Display.Cetak("Number", r2["num"])
                print(Display.Sukses(r2["mes"]), end="")
                Display.Cetak("Balance", self.Dashboard()["Balance"])
                Display.Cetak("Bal_Api", self.captcha.getBalance())
                Display.Line()
            else:
                if r2.get("mes"):
                    print(Display.Error(r2["mes"] + "\n"), end="")
                else:
                    print(r2)
                Display.Line()

            Functions.Tmr(3600)

    def ClaimBonus(self):
        while True:
            r = Requests.get(host + "faucet.php", self.headers())
            try:
                bonus = r[1].split('<span id="free_spins">')[1].split("</span>")[0]
            except IndexError:
                bonus = None

            if not bonus:
                print(Display.Error("No Bonus\n"), end="")
                break

            set_cookie_matches = re.findall(r"^Set-Cookie:\s*([^;]*)", r[0], flags=re.MULTILINE | re.IGNORECASE)
            cookies = {}
            for item in set_cookie_matches:
                if "=" in item:
                    key_, val_ = item.split("=", 1)
                    cookies[key_] = val_

            data = "action=claim_bonus_faucet&csrf_test_name=" + cookies.get("csrf_cookie_name", "")
            r2 = safe_json_loads(Requests.post(host + "process.php", self.headers(), data)[1], "claim_bonus")
            if r2 is None:
                print(Display.Error(
                    "Server javobini o'qib bo'lmadi (JSON emas).\n"
                ), end="")
                break
            if r2.get("ret"):
                Display.Cetak("Number", r2["num"])
                print(Display.Sukses(r2["mes"]), end="")
                Display.Cetak("Balance", self.Dashboard()["Balance"])
                Display.Line()

# ==========================================================
#                    TELEGRAM BOT HANDLERLAR
# ==========================================================

running_processes = {}
user_data_file = "user_data.json"

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

def get_log_path(user_id, script_name):
    return LOGS_DIR / f"{user_id}_{script_name}.log"

def run_tron_in_thread(user_id, context, config_data):
    try:
        log_file = get_log_path(user_id, "tron")
        
        # TRON skriptini ishga tushirish
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        # TRON botni ishga tushirish
        bot_tron = BotTRON(bot_context=context, user_id=user_id, config_data=config_data)
        
        # Log faylga yozish
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] TRON bot ishga tushdi\n")
            f.write(f"Captcha Type: {config_data.get('type', 'Multibot')}\n")
            f.write(f"Cookie: {config_data.get('cookie', 'N/A')[:50]}...\n")
        
        # Bot tugaganidan keyin xabar berish
        context.bot.send_message(
            chat_id=int(user_id),
            text="⏹ TRON to'xtadi!"
        )
        
        # Log faylni oxirini yuborish
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) > 4000:
                content = content[-4000:] + "\n\n... (oxirgi 4000 belgi)"
            context.bot.send_message(
                chat_id=int(user_id),
                text=f"📄 TRON log:\n\n```\n{content}\n```",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"TRON error: {e}")
        context.bot.send_message(
            chat_id=int(user_id),
            text=f"❌ Xatolik: {str(e)[:300]}"
        )

# ==========================================================
#                    TELEGRAM BOT COMMANDS
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "registered_at": datetime.now().isoformat(),
            "config": {}
        }
        save_user_data(user_data)
    
    keyboard = [
        [InlineKeyboardButton("🔧 Sozlash", callback_data="settings")],
        [InlineKeyboardButton("🚀 Ishga tushirish", callback_data="run")],
        [InlineKeyboardButton("📊 Holat", callback_data="status")],
        [InlineKeyboardButton("📄 Log", callback_data="logs")],
        [InlineKeyboardButton("⏹ To'xtatish", callback_data="stop")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        f"🔮 **TRON BOT**\n"
        f"✅ TRON skriptini ishga tushiradi\n"
        f"✅ Multibot yoki Xevil captcha tanlash mumkin\n\n"
        f"📌 **Buyruqlar:**\n"
        f"/start - Boshlash\n"
        f"/settings - Sozlamalar\n"
        f"/set - Ma'lumot kiritish\n"
        f"/run - Ishga tushirish\n"
        f"/stop - To'xtatish\n"
        f"/logs - Loglarni ko'rish\n"
        f"/status - Holatni tekshirish",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data = load_user_data()
    config = user_data.get(user_id, {}).get("config", {})
    
    keyboard = [
        [InlineKeyboardButton("📝 Cookie", callback_data="set_cookie")],
        [InlineKeyboardButton("📝 User Agent", callback_data="set_user_agent")],
        [InlineKeyboardButton("🤖 Captcha Type", callback_data="set_captcha")],
        [InlineKeyboardButton("🔑 Multibot API Key", callback_data="set_multibot")],
        [InlineKeyboardButton("🔑 Xevil API Key", callback_data="set_xevil")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🔧 **Sozlamalar**\n\n"
    text += f"📋 Cookie: `{config.get('cookie', '❌')[:30]}...`\n" if config.get('cookie') else "📋 Cookie: ❌\n"
    text += f"📋 User Agent: `{config.get('user_agent', '❌')[:30]}...`\n" if config.get('user_agent') else "📋 User Agent: ❌\n"
    text += f"🤖 Captcha: `{config.get('type', 'Multibot (1)')}`\n"
    text += f"🔑 Multibot API: `{config.get('multibot_apikey', '❌')[:10]}...`\n" if config.get('multibot_apikey') else "🔑 Multibot API: ❌\n"
    text += f"🔑 Xevil API: `{config.get('xevil_apikey', '❌')[:10]}...`\n" if config.get('xevil_apikey') else "🔑 Xevil API: ❌\n"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def set_captcha_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🤖 Multibot (1)", callback_data="captcha_1")],
        [InlineKeyboardButton("🔮 Xevil (2)", callback_data="captcha_2")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 **Captcha turini tanlang:**\n\n"
        "1. Multibot - arzon, ko'p xizmat\n"
        "2. Xevil - tez, ishonchli",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def captcha_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    captcha_type = query.data.replace("captcha_", "")
    
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {"config": {}}
    user_data[user_id]["config"]["type"] = captcha_type
    save_user_data(user_data)
    
    await query.edit_message_text(
        f"✅ Captcha turi sozlandi!\n\n"
        f"🤖 Tanlangan: `{'Multibot' if captcha_type == '1' else 'Xevil'}`\n\n"
        f"🔑 Endi API kalitni kiriting:\n"
        f"/set multibot_apikey - Multibot uchun\n"
        f"/set xevil_apikey - Xevil uchun",
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    if data == "settings":
        await settings_menu(update, context)
    elif data == "set_captcha":
        await set_captcha_menu(update, context)
    elif data.startswith("captcha_"):
        await captcha_select(update, context)
    elif data == "set_cookie":
        context.user_data['waiting_for_config'] = True
        context.user_data['config_key'] = 'cookie'
        await query.edit_message_text("📝 Cookie ni kiriting:")
    elif data == "set_user_agent":
        context.user_data['waiting_for_config'] = True
        context.user_data['config_key'] = 'user_agent'
        await query.edit_message_text("📝 User Agent ni kiriting:")
    elif data == "set_multibot":
        context.user_data['waiting_for_config'] = True
        context.user_data['config_key'] = 'multibot_apikey'
        await query.edit_message_text("🔑 Multibot API kalitni kiriting:")
    elif data == "set_xevil":
        context.user_data['waiting_for_config'] = True
        context.user_data['config_key'] = 'xevil_apikey'
        await query.edit_message_text("🔑 Xevil API kalitni kiriting:")
    elif data == "run":
        await run_tron(update, context)
    elif data == "status":
        await status_command(update, context)
    elif data == "logs":
        await view_logs(update, context)
    elif data == "stop":
        await stop_tron(update, context)
    elif data == "back_to_menu":
        await start(update, context)

async def set_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if context.args:
        config_key = context.args[0].lower()
        valid_keys = ['cookie', 'user_agent', 'multibot_apikey', 'xevil_apikey', 'type']
        
        if config_key not in valid_keys:
            await update.message.reply_text(f"❌ Mavjud: {', '.join(valid_keys)}")
            return
        
        context.user_data['waiting_for_config'] = True
        context.user_data['config_key'] = config_key
        await update.message.reply_text(f"📝 {config_key} qiymatini kiriting:")
        return
    
    user_data = load_user_data()
    if user_id in user_data and user_data[user_id].get("config"):
        config = user_data[user_id]["config"]
        text = "📋 **Konfiguratsiya:**\n\n"
        for key, value in config.items():
            if key == 'cookie' and len(value) > 20:
                value = value[:20] + "..."
            text += f"• *{key}*: `{value}`\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Konfiguratsiya mavjud emas!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    if message_text.startswith('/'):
        return
    
    if context.user_data.get('waiting_for_config'):
        config_key = context.user_data.get('config_key')
        if config_key:
            user_data = load_user_data()
            if user_id not in user_data:
                user_data[user_id] = {"config": {}}
            user_data[user_id]["config"][config_key] = message_text
            save_user_data(user_data)
            
            context.user_data['waiting_for_config'] = False
            context.user_data['config_key'] = None
            
            await update.message.reply_text(f"✅ {config_key} sozlandi!")
            return
    
    await update.message.reply_text(
        "ℹ️ Tugmalardan foydalaning yoki /start bosing."
    )

async def run_tron(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if isinstance(update, Update) and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    user_data = load_user_data()
    if user_id not in user_data:
        await message.reply_text("❌ Avval /start bosing!")
        return
    
    config = user_data[user_id].get("config", {})
    required = ['cookie', 'user_agent']
    missing = [r for r in required if r not in config]
    
    if missing:
        await message.reply_text(f"❌ Sozlang: /set {missing[0]}")
        return
    
    # Captcha tekshirish
    captcha_type = config.get('type', '1')
    if captcha_type == '1' and not config.get('multibot_apikey'):
        await message.reply_text("❌ Multibot API kalit kiritilmagan!\n/set multibot_apikey")
        return
    if captcha_type == '2' and not config.get('xevil_apikey'):
        await message.reply_text("❌ Xevil API kalit kiritilmagan!\n/set xevil_apikey")
        return
    
    key = f"{user_id}_tron"
    if key in running_processes and running_processes[key].get("status") == "running":
        await message.reply_text("⚠️ TRON allaqachon ishlayapti!")
        return
    
    await message.reply_text(
        f"🚀 **TRON ishga tushirilmoqda...**\n\n"
        f"📋 Cookie: ✅\n"
        f"📋 User Agent: ✅\n"
        f"🤖 Captcha: `{'Multibot' if captcha_type == '1' else 'Xevil'}`\n"
        f"⏳ Iltimos kuting...",
        parse_mode="Markdown"
    )
    
    # TRON ni ishga tushirish
    thread = threading.Thread(
        target=run_tron_in_thread,
        args=(user_id, context, config),
        daemon=True
    )
    thread.start()
    
    running_processes[key] = {
        "thread": thread,
        "start_time": datetime.now().isoformat(),
        "status": "running"
    }

async def stop_tron(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    key = f"{user_id}_tron"
    
    if isinstance(update, Update) and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    if key not in running_processes:
        await message.reply_text("❌ TRON ishlamayapti!")
        return
    
    running_processes[key]["status"] = "stopped"
    await message.reply_text("⏹ TRON to'xtatildi!")

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    log_file = get_log_path(user_id, "tron")
    
    if isinstance(update, Update) and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > 4000:
            content = content[-4000:] + "\n\n... (oxirgi 4000 belgi)"
        
        await message.reply_text(
            f"📄 TRON log:\n\n```\n{content}\n```",
            parse_mode="Markdown"
        )
    else:
        await message.reply_text("❌ Log topilmadi!")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    key = f"{user_id}_tron"
    
    if isinstance(update, Update) and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    text = "📊 **TRON holati:**\n\n"
    if key in running_processes:
        status_data = running_processes[key]
        emoji = "🟢" if status_data["status"] == "running" else "🔴"
        text += f"Holat: {emoji} {status_data['status']}\n"
        text += f"Boshlangan: {status_data.get('start_time', 'N/A')}\n"
    else:
        text += "Holat: ⚪ ishlamayapti\n"
    
    user_data = load_user_data()
    if user_id in user_data and user_data[user_id].get("config"):
        config = user_data[user_id]["config"]
        text += "\n📋 **Konfiguratsiya:**\n"
        for key, value in config.items():
            if key == 'cookie' and len(value) > 20:
                value = value[:20] + "..."
            text += f"• {key}: `{value}`\n"
    
    await message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ==========================================================
#                    MAIN
# ==========================================================

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set", set_config))
    application.add_handler(CommandHandler("run", run_tron))
    application.add_handler(CommandHandler("stop", stop_tron))
    application.add_handler(CommandHandler("logs", view_logs))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*60)
    print("🔮 TRON BOT ishga tushdi!")
    print(f"📁 Loglar: {LOGS_DIR}")
    print("="*60)
    print("\n📌 Bot buyruqlari:")
    print("  /start - Boshlash")
    print("  /set cookie - Cookie kiritish")
    print("  /set user_agent - User Agent kiritish")
    print("  /set multibot_apikey - Multibot API kalit")
    print("  /set xevil_apikey - Xevil API kalit")
    print("  /run - TRON ni ishga tushirish")
    print("  /stop - To'xtatish")
    print("  /logs - Loglarni ko'rish")
    print("  /status - Holatni tekshirish")
    print("="*60)
    
    application.run_polling()

if __name__ == "__main__":
    main()
