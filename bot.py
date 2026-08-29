#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Telegram bot uchun kutubxona
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    os.system("pip install python-telegram-bot==20.7 --break-system-packages")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Asosiy TRON botni import qilish
from tron import Bot as TronBot, Functions, Display, host, title, versi, Captcha, Iewil

# ==========================================================
#                       KONFIGURATSIYA
# ==========================================================
CONFIG_FILE = "telegram_config.json"
BOT_TOKEN = "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8"  # O'z tokenizni qo'ying
ADMIN_IDS = []  # Admin ID lar ro'yxati: [123456789, 987654321]

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================================
#                       API KONFIGURATSIYA
# ==========================================================
API_TYPES = {
    "multibot": {
        "name": "Multibot",
        "url": "http://api.multibot.in/",
        "key_required": True,
        "balance_endpoint": "res.php?action=userinfo&key={key}"
    },
    "xevil": {
        "name": "Xevil",
        "url": "https://sctg.xyz/",
        "key_required": True,
        "balance_endpoint": "res.php?action=userinfo&key={key}"
    },
    "iewil": {
        "name": "Iewil",
        "url": "https://iewilbot.my.id/res.php",
        "key_required": True,
        "balance_endpoint": None
    },
    "2captcha": {
        "name": "2Captcha",
        "url": "https://2captcha.com/",
        "key_required": True,
        "balance_endpoint": "res.php?action=getbalance&key={key}"
    },
    "capsolver": {
        "name": "CapSolver",
        "url": "https://api.capsolver.com/",
        "key_required": True,
        "balance_endpoint": "getBalance?apiKey={key}"
    },
    "anticaptcha": {
        "name": "AntiCaptcha",
        "url": "https://api.anti-captcha.com/",
        "key_required": True,
        "balance_endpoint": "getBalance"
    }
}

# ==========================================================
#                       YORDAMCHI FUNKSIYALAR
# ==========================================================
def load_config() -> Dict[str, Any]:
    """Telegram konfiguratsiyasini yuklash"""
    if not os.path.exists(CONFIG_FILE):
        return {"users": {}, "sessions": {}, "apis": {}}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "sessions": {}, "apis": {}}

def save_config(config: Dict[str, Any]) -> None:
    """Telegram konfiguratsiyasini saqlash"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS

def get_user_session(user_id: int) -> Optional[Dict[str, Any]]:
    """Foydalanuvchi sessiyasini olish"""
    config = load_config()
    return config.get("sessions", {}).get(str(user_id))

def set_user_session(user_id: int, session_data: Dict[str, Any]) -> None:
    """Foydalanuvchi sessiyasini saqlash"""
    config = load_config()
    if "sessions" not in config:
        config["sessions"] = {}
    config["sessions"][str(user_id)] = session_data
    save_config(config)

def remove_user_session(user_id: int) -> None:
    """Foydalanuvchi sessiyasini o'chirish"""
    config = load_config()
    if "sessions" in config and str(user_id) in config["sessions"]:
        del config["sessions"][str(user_id)]
        save_config(config)

def get_user_api(user_id: int) -> Optional[Dict[str, Any]]:
    """Foydalanuvchi API ma'lumotlarini olish"""
    config = load_config()
    return config.get("apis", {}).get(str(user_id))

def set_user_api(user_id: int, api_data: Dict[str, Any]) -> None:
    """Foydalanuvchi API ma'lumotlarini saqlash"""
    config = load_config()
    if "apis" not in config:
        config["apis"] = {}
    config["apis"][str(user_id)] = api_data
    save_config(config)

def remove_user_api(user_id: int) -> None:
    """Foydalanuvchi API ma'lumotlarini o'chirish"""
    config = load_config()
    if "apis" in config and str(user_id) in config["apis"]:
        del config["apis"][str(user_id)]
        save_config(config)

def format_balance(balance: str) -> str:
    """Balansni formatlash"""
    try:
        bal = float(balance)
        return f"{bal:,.2f}"
    except:
        return balance

def check_api_balance(api_type: str, api_key: str) -> Optional[float]:
    """API balansini tekshirish"""
    import requests
    
    try:
        if api_type == "multibot":
            url = f"http://api.multibot.in/res.php?action=userinfo&key={api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data.get("balance", 0)
            
        elif api_type == "xevil":
            url = f"https://sctg.xyz/res.php?action=userinfo&key={api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data.get("balance", 0)
            
        elif api_type == "2captcha":
            url = f"https://2captcha.com/res.php?action=getbalance&key={api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data.get("balance", 0)
            
        elif api_type == "capsolver":
            url = f"https://api.capsolver.com/getBalance?apiKey={api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data.get("balance", 0)
            
        elif api_type == "anticaptcha":
            url = "https://api.anti-captcha.com/getBalance"
            resp = requests.post(url, json={"clientKey": api_key}, timeout=10)
            data = resp.json()
            return data.get("balance", 0)
            
        elif api_type == "iewil":
            url = f"https://api-iewil.my.id/getInfo?key={api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return data.get("balance", 0) if data.get("status") else 0
            
    except Exception as e:
        logger.error(f"API balans tekshirishda xatolik: {e}")
        return None
        
    return None

# ==========================================================
#                       TELEGRAM BOT KLASSI
# ==========================================================
class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.bot_instances = {}
        self.running_tasks = {}
        
    def setup(self):
        """Botni sozlash"""
        self.application = Application.builder().token(self.token).build()
        
        # Komandalar
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("login", self.login_command))
        self.application.add_handler(CommandHandler("logout", self.logout_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("claim", self.claim_command))
        self.application.add_handler(CommandHandler("hourly", self.hourly_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("dashboard", self.dashboard_command))
        
        # API komandalar
        self.application.add_handler(CommandHandler("setapi", self.setapi_command))
        self.application.add_handler(CommandHandler("apistatus", self.apistatus_command))
        self.application.add_handler(CommandHandler("apibalance", self.apibalance_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Xatoliklarni ushlash
        self.application.add_error_handler(self.error_handler)
        
    def run(self):
        """Botni ishga tushirish"""
        logger.info("🤖 Bot ishga tushmoqda...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    # ==================== KOMANDALAR ====================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/start - Boshlash"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "NoUsername"
        
        welcome_text = f"""
🎰 *TRONPICK BOT v{versi}*

Assalomu alaykum, @{username}! 👋

Bu bot TRONPICK saytida avtomatik ravishda bonus yig'ish uchun yaratilgan.

📌 *Asosiy komandalar:*
/start - Botni qayta ishga tushirish
/help - Yordam
/login - Hisobingizga kirish
/logout - Hisobingizdan chiqish
/status - Bot holati
/balance - Balansni ko'rish
/dashboard - Dashboard ma'lumotlari
/claim - Bonusni yig'ish
/hourly - Hourly bonusni yig'ish (1 soat)
/stop - Joriy vazifani to'xtatish

🔑 *API komandalar:*
/setapi - API sozlash (Multibot, Xevil, Iewil, 2Captcha, CapSolver, AntiCaptcha)
/apistatus - API holati
/apibalance - API balansi

⚙️ *Sozlash:*
Avval /login komandasi orqali cookie va user-agent ni sozlang.
So'ng /setapi orqali captcha API ni sozlang.

📱 *Bot holati:* ✅ Ishlayapti
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
            [InlineKeyboardButton("💰 Balans", callback_data="balance")],
            [InlineKeyboardButton("🎯 Bonus Yig'ish", callback_data="claim")],
            [InlineKeyboardButton("⏰ Hourly Bonus", callback_data="hourly")],
            [InlineKeyboardButton("🔑 API Sozlamalari", callback_data="api_settings")],
            [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/help - Yordam"""
        help_text = """
📖 *Yordam*

🔑 *Kirish:*
/login - Hisobingizga kirish uchun cookie va user-agent so'raydi

🔧 *API Sozlash:*
/setapi - Captcha API ni sozlash
  • Multibot - http://api.multibot.in/
  • Xevil - https://sctg.xyz/
  • Iewil - https://iewilbot.my.id/
  • 2Captcha - https://2captcha.com/
  • CapSolver - https://capsolver.com/
  • AntiCaptcha - https://anti-captcha.com/

/apistatus - API holatini ko'rish
/apibalance - API balansini ko'rish

💳 *Ma'lumotlar:*
/balance - Joriy balansni ko'rish
/dashboard - To'liq dashboard ma'lumotlari

🎯 *Bonuslar:*
/claim - Kunlik bonusni yig'ish
/hourly - Hourly bonusni yig'ish (1 soat interval)

🔧 *Boshqaruv:*
/status - Bot holatini tekshirish
/logout - Hisobingizdan chiqish
/stop - Joriy vazifani to'xtatish

⚠️ *Muhim:*
1. Cookie va user-agent ni /login orqali kiriting
2. Captcha uchun API ni /setapi orqali sozlang
3. Hourly bonus har 1 soatda bir marta yig'iladi
4. Xato xabarlar kelganda /status ni tekshiring
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")
        
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/login - Hisobga kirish"""
        user_id = update.effective_user.id
        
        # Foydalanuvchini ro'yxatga olish
        config = load_config()
        if "users" not in config:
            config["users"] = {}
        config["users"][str(user_id)] = {
            "username": update.effective_user.username or "Unknown",
            "first_name": update.effective_user.first_name or "",
            "last_login": datetime.now().isoformat()
        }
        save_config(config)
        
        await update.message.reply_text(
            "🔑 *Hisobga kirish*\n\n"
            "Iltimos, quyidagi ma'lumotlarni kiriting:\n\n"
            "1️⃣ *Cookie* (to'liq qator)\n"
            "2️⃣ *User-Agent*\n\n"
            "Format: `cookie|user_agent`\n\n"
            "Misol:\n"
            "`cf_clearance=...; PHPSESSID=...|Mozilla/5.0...`\n\n"
            "Yoki alohida:\n"
            "Avval cookieni, keyin user-agent ni yuboring.",
            parse_mode="Markdown"
        )
        
        context.user_data['login_state'] = 'waiting_cookie'
        
    async def logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/logout - Hisobdan chiqish"""
        user_id = update.effective_user.id
        
        remove_user_session(user_id)
        
        if user_id in self.bot_instances:
            del self.bot_instances[user_id]
            
        if user_id in self.running_tasks:
            self.running_tasks[user_id] = None
            
        await update.message.reply_text(
            "✅ *Hisobdan chiqildi*\n\n"
            "Cookie va user-agent ma'lumotlari o'chirildi.\n"
            "Qayta kirish uchun /login komandasidan foydalaning.",
            parse_mode="Markdown"
        )
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/status - Bot holati"""
        user_id = update.effective_user.id
        
        session = get_user_session(user_id)
        api = get_user_api(user_id)
        is_logged_in = session is not None
        
        status_text = f"""
📊 *Bot Holati*

👤 *Foydalanuvchi:* @{update.effective_user.username or 'Unknown'}
🔑 *Kirish holati:* {'✅ Kirilgan' if is_logged_in else '❌ Kirilmagan'}
📱 *Sessiya:* {'Mavjud' if is_logged_in else 'Yo\'q'}
🔄 *Vazifa:* {'Ishlayapti' if user_id in self.running_tasks and self.running_tasks.get(user_id) else 'To\'xtatilgan'}

🔧 *API Holati:*
• Provider: {api.get('provider', 'Sozlanmagan') if api else 'Sozlanmagan'}
• API Key: {'✅ Sozlangan' if api and api.get('api_key') else '❌ Sozlanmagan'}
• Balans: {'🔄 Tekshirilmoqda...' if api else 'N/A'}

📅 *So'nggi faollik:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
📌 *Bot versiyasi:* v{versi}
        """
        
        keyboard = []
        if is_logged_in:
            keyboard.append([InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")])
            keyboard.append([InlineKeyboardButton("💰 Balans", callback_data="balance")])
            keyboard.append([InlineKeyboardButton("🎯 Claim Bonus", callback_data="claim")])
            keyboard.append([InlineKeyboardButton("⏰ Hourly Bonus", callback_data="hourly")])
        keyboard.append([InlineKeyboardButton("🔑 API Sozlamalari", callback_data="api_settings")])
        keyboard.append([InlineKeyboardButton("🚪 Chiqish", callback_data="logout")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/balance - Balansni ko'rish"""
        user_id = update.effective_user.id
        
        session = get_user_session(user_id)
        if not session:
            await update.message.reply_text(
                "❌ *Xatolik:* Avval /login komandasi orqali hisobingizga kiring!",
                parse_mode="Markdown"
            )
            return
            
        try:
            bot = self._get_bot_instance(user_id, session)
            r = bot.Dashboard()
            
            if not r.get("Login"):
                await update.message.reply_text(
                    "❌ *Cookie muddati tugagan!*\n"
                    "Iltimos, qayta /login qiling.",
                    parse_mode="Markdown"
                )
                remove_user_session(user_id)
                return
                
            # API balansini tekshirish
            api = get_user_api(user_id)
            api_balance = "Sozlanmagan"
            if api and api.get('api_key'):
                api_balance = check_api_balance(api.get('provider', '').lower(), api.get('api_key'))
                api_balance = f"{api_balance:.2f}" if api_balance else "Xatolik"
                
            balance_text = f"""
💰 *Balans Ma'lumotlari*

👤 *Foydalanuvchi:* {r.get('Username', 'Noma\'lum')}
💵 *TRON Balans:* {r.get('Balance', '0')} TRX
📊 *Level:* {r.get('Level', 'Noma\'lum')}

📈 *Statistika:*
• Total Wagered: {r.get('Total Wagered', '0')}
• Wagering Target: {r.get('Wagering Target', '0')}
            
🔑 *API Balans:*
• Provider: {api.get('provider', 'Sozlanmagan') if api else 'Sozlanmagan'}
• Balans: {api_balance}
            
📅 *So'nggi yangilanish:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Yangilash", callback_data="balance")],
                [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
                [InlineKeyboardButton("🎯 Bonus Yig'ish", callback_data="claim")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                balance_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ *Xatolik:* {str(e)}\n\n"
                "Iltimos, qayta urinib ko'ring.",
                parse_mode="Markdown"
            )
            
    async def dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/dashboard - Dashboard ma'lumotlari"""
        user_id = update.effective_user.id
        
        session = get_user_session(user_id)
        if not session:
            await update.message.reply_text(
                "❌ *Xatolik:* Avval /login komandasi orqali hisobingizga kiring!",
                parse_mode="Markdown"
            )
            return
            
        try:
            bot = self._get_bot_instance(user_id, session)
            r = bot.Dashboard()
            
            if not r.get("Login"):
                await update.message.reply_text(
                    "❌ *Cookie muddati tugagan!* Qayta /login qiling.",
                    parse_mode="Markdown"
                )
                remove_user_session(user_id)
                return
                
            dashboard_text = f"""
📊 *Dashboard Ma'lumotlari*

👤 *Foydalanuvchi:* {r.get('Username', 'Noma\'lum')}
💵 *Balans:* {r.get('Balance', '0')} TRX
📊 *Level:* {r.get('Level', 'Noma\'lum')}

📈 *Statistika:*
• Total Wagered: {r.get('Total Wagered', '0')}
• Wagering Target: {r.get('Wagering Target', '0')}

📅 *Sana:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Yangilash", callback_data="dashboard")],
                [InlineKeyboardButton("💰 Balans", callback_data="balance")],
                [InlineKeyboardButton("🎯 Bonus Yig'ish", callback_data="claim")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                dashboard_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ *Xatolik:* {str(e)}",
                parse_mode="Markdown"
            )
            
    async def claim_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/claim - Bonusni yig'ish"""
        user_id = update.effective_user.id
        
        session = get_user_session(user_id)
        if not session:
            await update.message.reply_text(
                "❌ *Xatolik:* Avval /login komandasi orqali hisobingizga kiring!",
                parse_mode="Markdown"
            )
            return
            
        api = get_user_api(user_id)
        if not api or not api.get('api_key'):
            await update.message.reply_text(
                "❌ *Xatolik:* Avval /setapi komandasi orqali API ni sozlang!\n\n"
                "Qo'llab-quvvatlanadigan API'lar:\n"
                "• Multibot\n"
                "• Xevil\n"
                "• Iewil\n"
                "• 2Captcha\n"
                "• CapSolver\n"
                "• AntiCaptcha",
                parse_mode="Markdown"
            )
            return
            
        await update.message.reply_text(
            "🎯 *Bonus yig'ish boshlandi...*\n\n"
            f"🔑 API: {api.get('provider')}\n"
            "Iltimos, kuting...",
            parse_mode="Markdown"
        )
        
        def claim_task():
            try:
                bot = self._get_bot_instance(user_id, session)
                bot.ClaimBonus()
                
                self._send_message(user_id, "✅ *Bonus muvaffaqiyatli yig'ildi!*", parse_mode="Markdown")
                
            except Exception as e:
                self._send_message(user_id, f"❌ *Xatolik:* {str(e)}", parse_mode="Markdown")
                
        thread = threading.Thread(target=claim_task)
        thread.daemon = True
        thread.start()
        self.running_tasks[user_id] = thread
        
    async def hourly_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/hourly - Hourly bonusni yig'ish"""
        user_id = update.effective_user.id
        
        session = get_user_session(user_id)
        if not session:
            await update.message.reply_text(
                "❌ *Xatolik:* Avval /login komandasi orqali hisobingizga kiring!",
                parse_mode="Markdown"
            )
            return
            
        await update.message.reply_text(
            "⏰ *Hourly bonus yig'ish boshlandi...*\n\n"
            "Bu jarayon 1 soat davom etadi.\n"
            "To'xtatish uchun /stop komandasini bosing.",
            parse_mode="Markdown"
        )
        
        def hourly_task():
            try:
                bot = self._get_bot_instance(user_id, session)
                result = bot.HourlyFaucet()
                
                if result:
                    self._send_message(
                        user_id, 
                        "✅ *Hourly bonus muvaffaqiyatli yig'ildi!*\n\n"
                        "Keyingi bonus 1 soatdan keyin...",
                        parse_mode="Markdown"
                    )
                else:
                    self._send_message(
                        user_id,
                        "❌ *Hourly bonus yig'ishda xatolik yuz berdi!*",
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                self._send_message(
                    user_id,
                    f"❌ *Xatolik:* {str(e)}",
                    parse_mode="Markdown"
                )
                
        thread = threading.Thread(target=hourly_task)
        thread.daemon = True
        thread.start()
        self.running_tasks[user_id] = thread
        
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/stop - Joriy vazifani to'xtatish"""
        user_id = update.effective_user.id
        
        if user_id in self.running_tasks and self.running_tasks.get(user_id):
            self.running_tasks[user_id] = None
            await update.message.reply_text(
                "🛑 *Vazifa to'xtatildi!*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "ℹ️ *Hozirgi vaqtda hech qanday vazifa ishlamayapti.*",
                parse_mode="Markdown"
            )
            
    # ==================== API KOMANDALAR ====================
    
    async def setapi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/setapi - API sozlash"""
        user_id = update.effective_user.id
        
        api_list = "\n".join([
            f"• {name.upper()} - {info['url']}"
            for name, info in API_TYPES.items()
        ])
        
        await update.message.reply_text(
            f"🔑 *API Sozlash*\n\n"
            "Qo'llab-quvvatlanadigan API'lar:\n"
            f"{api_list}\n\n"
            "Format: `provider|api_key`\n\n"
            "Misol:\n"
            "`multibot|YOUR_API_KEY`\n"
            "`xevil|YOUR_API_KEY`\n"
            "`iewil|YOUR_API_KEY`\n"
            "`2captcha|YOUR_API_KEY`\n"
            "`capsolver|YOUR_API_KEY`\n"
            "`anticaptcha|YOUR_API_KEY`",
            parse_mode="Markdown"
        )
        
        context.user_data['api_state'] = 'waiting_api'
        
    async def apistatus_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/apistatus - API holati"""
        user_id = update.effective_user.id
        
        api = get_user_api(user_id)
        if not api:
            await update.message.reply_text(
                "❌ *API sozlanmagan!*\n\n"
                "Iltimos, /setapi komandasi orqali API ni sozlang.",
                parse_mode="Markdown"
            )
            return
            
        # API balansini tekshirish
        balance = check_api_balance(api.get('provider', '').lower(), api.get('api_key'))
        
        status_text = f"""
🔑 *API Holati*

📌 *Provider:* {api.get('provider', 'Noma\'lum')}
🔑 *API Key:* {api.get('api_key', 'N/A')[:10]}...
💰 *Balans:* {balance if balance is not None else 'Tekshirib bo\'lmadi'}
📅 *Sozlangan sana:* {api.get('created_at', 'Noma\'lum')}

📊 *API imkoniyatlari:*
• RecaptchaV2: {'✅' if api.get('provider') in ['Multibot', 'Xevil', '2Captcha', 'CapSolver', 'AntiCaptcha'] else '❌'}
• Hcaptcha: {'✅' if api.get('provider') in ['Multibot', 'Xevil', '2Captcha', 'CapSolver'] else '❌'}
• Turnstile: {'✅' if api.get('provider') in ['Multibot', 'Xevil', 'Iewil', 'CapSolver'] else '❌'}
• OCR: {'✅' if api.get('provider') in ['Multibot', 'Xevil'] else '❌'}
• AntiBot: {'✅' if api.get('provider') in ['Multibot', 'Xevil', 'Iewil'] else '❌'}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Yangilash", callback_data="apistatus")],
            [InlineKeyboardButton("💰 API Balans", callback_data="apibalance")],
            [InlineKeyboardButton("🔑 API O'zgartirish", callback_data="api_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    async def apibalance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/apibalance - API balansi"""
        user_id = update.effective_user.id
        
        api = get_user_api(user_id)
        if not api:
            await update.message.reply_text(
                "❌ *API sozlanmagan!*\n\n"
                "Iltimos, /setapi komandasi orqali API ni sozlang.",
                parse_mode="Markdown"
            )
            return
            
        await update.message.reply_text(
            "🔄 *API balansi tekshirilmoqda...*\n"
            "Iltimos, kuting.",
            parse_mode="Markdown"
        )
        
        balance = check_api_balance(api.get('provider', '').lower(), api.get('api_key'))
        
        if balance is not None:
            await update.message.reply_text(
                f"💰 *API Balans*\n\n"
                f"📌 *Provider:* {api.get('provider')}\n"
                f"💵 *Balans:* {balance:.2f} $\n"
                f"📅 *Sana:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ *API balansini tekshirib bo'lmadi!*\n\n"
                "Iltimos, API kalitini tekshiring va /setapi orqali qayta sozlang.",
                parse_mode="Markdown"
            )
            
    # ==================== CALLBACK HANDLER ====================
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback query handler"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "dashboard":
            await self.dashboard_command(update, context)
        elif data == "balance":
            await self.balance_command(update, context)
        elif data == "claim":
            await self.claim_command(update, context)
        elif data == "hourly":
            await self.hourly_command(update, context)
        elif data == "login":
            await self.login_command(update, context)
        elif data == "logout":
            await self.logout_command(update, context)
        elif data == "settings":
            await self._settings_menu(update, context)
        elif data == "api_settings":
            await self._api_settings_menu(update, context)
        elif data == "apistatus":
            await self.apistatus_command(update, context)
        elif data == "apibalance":
            await self.apibalance_command(update, context)
        elif data.startswith("api_select_"):
            provider = data.replace("api_select_", "")
            context.user_data['selected_api'] = provider
            await query.edit_message_text(
                f"🔑 *{provider.upper()} API sozlash*\n\n"
                f"API kalitingizni yuboring:\n\n"
                f"Format: `api_key`\n\n"
                f"Misol: `YOUR_API_KEY_HERE`",
                parse_mode="Markdown"
            )
            context.user_data['api_state'] = 'waiting_api_key'
            
    # ==================== XABAR HANDLER ====================
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Oddiy xabarlarni qayta ishlash"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Login jarayoni
        if context.user_data.get('login_state') == 'waiting_cookie':
            context.user_data['cookie'] = text
            context.user_data['login_state'] = 'waiting_user_agent'
            await update.message.reply_text(
                "✅ *Cookie qabul qilindi!*\n\n"
                "Endi User-Agent ni yuboring:\n"
                "Masalan: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...`",
                parse_mode="Markdown"
            )
            return
            
        elif context.user_data.get('login_state') == 'waiting_user_agent':
            cookie = context.user_data.get('cookie')
            user_agent = text
            
            session_data = {
                "cookie": cookie,
                "user_agent": user_agent
            }
            set_user_session(user_id, session_data)
            
            context.user_data['login_state'] = None
            context.user_data.pop('cookie', None)
            
            await update.message.reply_text(
                "✅ *Hisobingizga muvaffaqiyatli kirdingiz!*\n\n"
                f"📌 *Cookie:* {cookie[:50]}...\n"
                f"📌 *User-Agent:* {user_agent[:50]}...\n\n"
                "Keyingi qadam: /setapi orqali captcha API ni sozlang\n\n"
                "Endi quyidagi komandalardan foydalanishingiz mumkin:\n"
                "/balance - Balansni ko'rish\n"
                "/claim - Bonus yig'ish\n"
                "/hourly - Hourly bonus yig'ish\n"
                "/dashboard - Dashboard ma'lumotlari",
                parse_mode="Markdown"
            )
            return
            
        # API sozlash jarayoni
        if context.user_data.get('api_state') == 'waiting_api':
            # Foydalanuvchi provider|api_key formatida yuborgan
            if '|' in text:
                provider, api_key = text.split('|', 1)
                provider = provider.strip().lower()
                api_key = api_key.strip()
                
                if provider not in API_TYPES:
                    await update.message.reply_text(
                        f"❌ *Xatolik:* '{provider}' qo'llab-quvvatlanmaydi!\n\n"
                        "Qo'llab-quvvatlanadigan API'lar:\n"
                        f"{', '.join(API_TYPES.keys())}",
                        parse_mode="Markdown"
                    )
                    return
                    
                # API balansini tekshirish
                balance = check_api_balance(provider, api_key)
                if balance is None:
                    await update.message.reply_text(
                        f"❌ *Xatolik:* API kaliti noto'g'ri yoki balansni tekshirib bo'lmadi!\n\n"
                        "Iltimos, API kalitini tekshirib qayta yuboring.",
                        parse_mode="Markdown"
                    )
                    return
                    
                # API ma'lumotlarini saqlash
                api_data = {
                    "provider": API_TYPES[provider]['name'],
                    "api_key": api_key,
                    "created_at": datetime.now().isoformat()
                }
                set_user_api(user_id, api_data)
                
                context.user_data['api_state'] = None
                
                await update.message.reply_text(
                    f"✅ *API muvaffaqiyatli sozlandi!*\n\n"
                    f"📌 *Provider:* {API_TYPES[provider]['name']}\n"
                    f"💰 *Balans:* {balance:.2f} $\n"
                    f"📅 *Sana:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                    "Endi bonus yig'ishni boshlashingiz mumkin:\n"
                    "/claim - Kunlik bonus\n"
                    "/hourly - Hourly bonus",
                    parse_mode="Markdown"
                )
                return
            else:
                await update.message.reply_text(
                    "❌ *Xatolik:* Noto'g'ri format!\n\n"
                    "Format: `provider|api_key`\n\n"
                    "Misol: `multibot|YOUR_API_KEY`\n"
                    "Qo'llab-quvvatlanadigan provider'lar:\n"
                    f"{', '.join(API_TYPES.keys())}",
                    parse_mode="Markdown"
                )
                return
                
        elif context.user_data.get('api_state') == 'waiting_api_key':
            provider = context.user_data.get('selected_api')
            api_key = text.strip()
            
            if not provider:
                await update.message.reply_text(
                    "❌ *Xatolik:* Provider tanlanmagan!\n"
                    "Iltimos, /setapi komandasini qayta bosing.",
                    parse_mode="Markdown"
                )
                context.user_data['api_state'] = None
                return
                
            # API balansini tekshirish
            balance = check_api_balance(provider, api_key)
            if balance is None:
                await update.message.reply_text(
                    f"❌ *Xatolik:* API kaliti noto'g'ri yoki balansni tekshirib bo'lmadi!\n\n"
                    "Iltimos, API kalitini tekshirib qayta yuboring.",
                    parse_mode="Markdown"
                )
                return
                
            # API ma'lumotlarini saqlash
            api_data = {
                "provider": API_TYPES[provider]['name'],
                "api_key": api_key,
                "created_at": datetime.now().isoformat()
            }
            set_user_api(user_id, api_data)
            
            context.user_data['api_state'] = None
            context.user_data.pop('selected_api', None)
            
            await update.message.reply_text(
                f"✅ *API muvaffaqiyatli sozlandi!*\n\n"
                f"📌 *Provider:* {API_TYPES[provider]['name']}\n"
                f"💰 *Balans:* {balance:.2f} $\n"
                f"📅 *Sana:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                "Endi bonus yig'ishni boshlashingiz mumkin:\n"
                "/claim - Kunlik bonus\n"
                "/hourly - Hourly bonus",
                parse_mode="Markdown"
            )
            return
            
        # Agar boshqa xabar bo'lsa
        await update.message.reply_text(
            "❓ *Noma'lum buyruq.*\n"
            "Yordam uchun /help bosing.",
            parse_mode="Markdown"
        )
        
    # ==================== YORDAMCHI FUNKSIYALAR ====================
    
    def _get_bot_instance(self, user_id: int, session: Dict[str, Any]):
        """Foydalanuvchi uchun TronBot instansiyasini olish"""
        if user_id not in self.bot_instances:
            bot = TronBot()
            bot.cookie = session.get("cookie")
            bot.uagent = session.get("user_agent")
            
            # API ma'lumotlarini o'rnatish
            api = get_user_api(user_id)
            if api:
                provider = api.get('provider', '').lower()
                api_key = api.get('api_key')
                
                if provider == 'multibot':
                    bot.captcha = Captcha()
                    bot.captcha.provider = 'Multibot'
                    bot.captcha.key = api_key
                elif provider == 'xevil':
                    bot.captcha = Captcha()
                    bot.captcha.provider = 'Xevil'
                    bot.captcha.key = api_key + "|SOFTID1204538927"
                elif provider == 'iewil':
                    bot.iewil = Iewil(api_key)
                elif provider in ['2captcha', 'capsolver', 'anticaptcha']:
                    # Boshqa API'lar uchun Captcha klassini sozlash
                    bot.captcha = Captcha()
                    bot.captcha.provider = provider
                    bot.captcha.key = api_key
                    
            self.bot_instances[user_id] = bot
        return self.bot_instances[user_id]
        
    def _send_message(self, user_id: int, text: str, **kwargs):
        """Foydalanuvchiga xabar yuborish"""
        try:
            self.application.bot.send_message(
                chat_id=user_id,
                text=text,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Xabar yuborishda xatolik: {e}")
            
    async def _settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sozlamalar menyusi"""
        user_id = update.effective_user.id
        session = get_user_session(user_id)
        api = get_user_api(user_id)
        
        settings_text = f"""
⚙️ *Sozlamalar*

📌 *Cookie:* {'✅ Mavjud' if session else '❌ Yo\'q'}
🔑 *API:* {'✅ Sozlangan' if api else '❌ Sozlanmagan'}
📌 *Provider:* {api.get('provider', 'N/A') if api else 'N/A'}

🔧 *Mavjud sozlamalar:*
• /login - Hisobga kirish
• /logout - Hisobdan chiqish
• /setapi - API sozlash
• /status - Bot holati

💡 *Maslahat:*
1. Avval /login orqali hisobga kiring
2. Keyin /setapi orqali API ni sozlang
        """
        
        keyboard = [
            [InlineKeyboardButton("🔑 Kirish", callback_data="login")],
            [InlineKeyboardButton("🚪 Chiqish", callback_data="logout")],
            [InlineKeyboardButton("🔑 API Sozlamalari", callback_data="api_settings")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    async def _api_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """API sozlamalari menyusi"""
        user_id = update.effective_user.id
        api = get_user_api(user_id)
        
        keyboard = []
        for provider, info in API_TYPES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{'✅ ' if api and api.get('provider', '').lower() == provider else ''}{info['name']}",
                    callback_data=f"api_select_{provider}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("📊 API Holati", callback_data="apistatus")])
        keyboard.append([InlineKeyboardButton("💰 API Balans", callback_data="apibalance")])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="settings")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔑 *API Sozlamalari*\n\n"
            f"Joriy API: {api.get('provider', 'Sozlanmagan') if api else 'Sozlanmagan'}\n\n"
            "Quyidagi API'lardan birini tanlang:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    # ==================== ERROR HANDLER ====================
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xatoliklarni boshqarish"""
        logger.error(f"Xatolik: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ *Xatolik yuz berdi!*\n"
                "Iltimos, qayta urinib ko'ring yoki /start bosing.\n\n"
                f"Xatolik: {str(context.error)[:100]}",
                parse_mode="Markdown"
            )

# ==========================================================
#                       ASOSIY QISM
# ==========================================================
def main():
    """Asosiy funksiya"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Iltimos, BOT_TOKEN ni o'zgartiring!")
        print("📝 bot.py faylida BOT_TOKEN = 'YOUR_TOKEN' qatorini o'zgartiring.")
        sys.exit(1)
        
    bot = TelegramBot(BOT_TOKEN)
    bot.setup()
    
    bot.application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler)
    )
    
    print(f"""
╔════════════════════════════════════════╗
║                                        ║
║     🤖 TRONPICK TELEGRAM BOT v{versi}     ║
║                                        ║
║     Bot ishga tushdi!                  ║
║     @{bot.application.bot.username}          ║
║                                        ║
║     📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}        ║
║                                        ║
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
