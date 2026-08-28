import os
import datetime
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import asyncio

# ============ KONFIG ============
TOKEN = '8954102314:AAEUrvXh5uDn7AnYC8Qgx0ecg_Jg-SNJFIc'
ADMIN_ID = 8758410535

DB_PATH = 'pulbot.db'

# ============ BAZA ============
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            solved INTEGER DEFAULT 0,
            ref_count INTEGER DEFAULT 0,
            phone TEXT,
            ban INTEGER DEFAULT 0,
            step TEXT,
            temp_data TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pay_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    defaults = [
        ('taklif', '250'),
        ('valyuta', "so'm"),
        ('narx', '3000'),
        ('vazifa', 'Kiritilmagan'),
        ('admin_user', 'Kiritilmagan')
    ]
    for key, value in defaults:
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

# ============ YORDAMCHI FUNKSIYALAR ============
def get_setting(key, default=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'balance': row[1],
            'solved': row[2],
            'ref_count': row[3],
            'phone': row[4],
            'ban': row[5],
            'step': row[6],
            'temp_data': row[7]
        }
    return None

def create_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (id, balance, solved, ref_count, ban) VALUES (?, 0, 0, 0, 0)', (user_id,))
    conn.commit()
    conn.close()

def set_user_step(user_id, step):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET step = ? WHERE id = ?', (step, user_id))
    conn.commit()
    conn.close()

def set_user_temp(user_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET temp_data = ? WHERE id = ?', (data, user_id))
    conn.commit()
    conn.close()

def get_user_temp(user_id):
    user = get_user(user_id)
    return user['temp_data'] if user else None

def add_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def sub_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def add_solved(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET solved = solved + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def inc_ref(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET ref_count = ref_count + 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_phone(user_id, phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
    conn.commit()
    conn.close()

def set_ban(user_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET ban = ? WHERE id = ?', (1 if status else 0, user_id))
    conn.commit()
    conn.close()

def add_stat(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO stats (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_stat_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM stats')
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id FROM stats')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_channel(url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO channels (url) VALUES (?)', (url,))
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT url FROM channels')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def clear_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM channels')
    conn.commit()
    conn.close()

def add_pay_type(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO pay_types (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

def get_pay_types():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name FROM pay_types')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def del_pay_type(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM pay_types WHERE name = ?', (name,))
    conn.commit()
    conn.close()

# ============ MENU ============
async def get_main_menu(user_id):
    keyboard = [
        [KeyboardButton("💵 Pul ishlash")],
        [KeyboardButton("🏦 Pul yechish"), KeyboardButton("💰 Hisobim")],
        [KeyboardButton("📨 Murojaat"), KeyboardButton("🧾 To'lovlar tarixi")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("🗄 Boshqarish")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def get_back_menu():
    return ReplyKeyboardMarkup([[KeyboardButton("◀️ Orqaga")]], resize_keyboard=True)

async def get_panel_menu():
    keyboard = [
        [KeyboardButton("⚙ Asosiy sozlamalar")],
        [KeyboardButton("📢 Kanallar"), KeyboardButton("📊 Statistika")],
        [KeyboardButton("🔎 Foydalanuvchini boshqarish")],
        [KeyboardButton("🎛 Tugmalar"), KeyboardButton("📃 Matnlar")],
        [KeyboardButton("💳 To'lov tizimi")],
        [KeyboardButton("📨 Xabarnoma"), KeyboardButton("◀️ Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def get_boshqarish():
    return ReplyKeyboardMarkup([[KeyboardButton("🗄 Boshqarish")]], resize_keyboard=True)

# ============ KANAL TEKSHIRISH ============
async def joinchat(context, user_id):
    channels = get_channels()
    if not channels:
        return True
    keyboard = []
    uns = False
    for url in channels:
        if '@' in url:
            clean = url.split('@')[1]
            try:
                member = await context.bot.get_chat_member(chat_id=f'@{clean}', user_id=user_id)
                status = member.status
                if status in ['creator', 'administrator', 'member']:
                    text = f"✅ {clean}"
                else:
                    text = f"❌ {clean}"
                    uns = True
            except:
                text = f"❌ {clean}"
                uns = True
            keyboard.append([InlineKeyboardButton(text, url=f'https://t.me/{clean}')])
    if uns:
        keyboard.append([InlineKeyboardButton("🔄 Tekshirish", callback_data='check')])
        await context.bot.send_message(
            user_id,
            "<b>⚠️ Botdan to'liq foydalanish uchun quyidagi kanallarimizga obuna bo'ling!</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return False
    return True

# ============ TELEFON RAQAM ============
async def number_check(context, user_id, first_name, last_name):
    user = get_user(user_id)
    if user and user['phone']:
        return True
    set_user_step(user_id, 'request_contact')
    text = "<b>📲 Botdan ro'yxatdan o'tish uchun quyidagi tugma orqali telefon raqamingizni yuboring:</b>"
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(user_id, text, parse_mode='HTML', reply_markup=keyboard)
    return False

# ============ /start ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ''
    
    create_user(user_id)
    add_stat(user_id)
    
    if not await number_check(context, user_id, first_name, last_name):
        return
    
    if context.args:
        ref_id = context.args[0]
        if ref_id.isdigit() and int(ref_id) != user_id:
            ref_id = int(ref_id)
            taklif = int(get_setting('taklif', '250'))
            add_balance(ref_id, taklif)
            inc_ref(ref_id)
            await context.bot.send_message(ref_id, "<b>📳 Sizda yangi taklif mavjud!</b>", parse_mode='HTML')
    
    if not await joinchat(context, user_id):
        return
    
    await update.message.reply_text(
        "<b>🖥 Asosiy menyudasiz.</b>",
        parse_mode='HTML',
        reply_markup=await get_main_menu(user_id)
    )

# ============ KONTAKT ============
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    contact = update.message.contact
    if contact.user_id != user_id:
        return
    phone = contact.phone_number.replace('+', '')
    if len(phone) == 12 and phone.startswith('998'):
        set_phone(user_id, phone)
        set_user_step(user_id, '')
        await update.message.reply_text(
            f"<b>✅ Telefon raqamingiz qabul qilindi:</b> {phone}\n\n<i>Botdan foydalanish boshlash uchun quyidagi tugmani bosing:</i>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Davom etish", callback_data='davom')]])
        )
    else:
        set_ban(user_id, 1)
        set_user_step(user_id, '')
        await update.message.reply_text(
            "<b>Kechirasiz, Botdan faqat O'zbekiston fuqarolari foydalanishi mumkin.</b>",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )

# ============ CALLBACK ============
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == 'davom':
        await query.message.delete()
        await context.bot.send_message(
            user_id,
            "<b>🖥 Asosiy menyudasiz.</b>",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )
        return
    
    if data == 'check':
        await query.message.delete()
        if await joinchat(context, user_id):
            await context.bot.send_message(
                user_id,
                "<b>🖥 Asosiy menyudasiz.</b>",
                parse_mode='HTML',
                reply_markup=await get_main_menu(user_id)
            )
        return
    
    if data == 'yopish':
        await query.message.delete()
        return
    
    # ===== ADMIN =====
    if user_id == ADMIN_ID:
        if data == 'holat':
            valyuta = get_setting('valyuta', "so'm")
            taklif = get_setting('taklif', '250')
            narx = get_setting('narx', '3000')
            admin_user = get_setting('admin_user', 'Kiritilmagan')
            text = f"<b>Hozirgi holat:\n\n1. Valyuta:</b> {valyuta}\n<b>2. Taklif narxi:</b> {taklif} {valyuta}\n<b>3. Pul yechish narxi:</b> {narx} {valyuta}\n<b>4. Admin useri:</b> {admin_user}"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data='asosiy')]])
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'asosiy':
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📑 Hozirgi holat", callback_data='holat')],
                [InlineKeyboardButton("🔗 Taklif narxi", callback_data='taklif'), InlineKeyboardButton("💶 Valyuta", callback_data='valyuta')],
                [InlineKeyboardButton("💵 Minimal pul yechish narxi", callback_data='narx')],
                [InlineKeyboardButton("📎 Admin useri", callback_data='admin'), InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await query.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'taklif':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Taklif narxini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'taklifpul')
            return
        
        if data == 'valyuta':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Pul birligini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'valyuta')
            return
        
        if data == 'narx':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Minimal pul yechish narxini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'narx')
            return
        
        if data == 'admin':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Admin userini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'admin-user')
            return
        
        # Kanallar
        if data == 'majburiy':
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Qo'shish", callback_data='qoshish')],
                [InlineKeyboardButton("📑 Ro'yxat", callback_data='royxat'), InlineKeyboardButton("🗑 O'chirish", callback_data='ochirish')],
                [InlineKeyboardButton("◀️ Orqaga", callback_data='kanallar')]
            ])
            await query.edit_message_text("<b>Majburiy obunalarni sozlash bo'limidasiz:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'qoshish':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Kanalingiz userini kiriting:\n\nNamuna:</b> @ORGBuilder", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, "qo'shish")
            return
        
        if data == 'ochirish':
            clear_channels()
            await query.edit_message_text("<b>Kanallar o'chirildi</b>", parse_mode='HTML')
            return
        
        if data == 'royxat':
            channels = get_channels()
            if channels:
                text = "<b>📢 Kanallar ro'yxati:</b>\n\n" + "\n".join(channels) + f"\n\n<b>Ulangan kanallar soni:</b> {len(channels)} ta"
            else:
                text = "📂 <b>Kanallar ro'yxati bo'sh!</b>"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data='majburiy')]])
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'kanallar':
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Majburiy obunalar", callback_data='majburiy')],
                [InlineKeyboardButton("*⃣ Qo'shimcha kanallar", callback_data='qoshimcha')],
                [InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await query.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'qoshimcha':
            vazifa = get_setting('vazifa', 'Kiritilmagan')
            text = f"<b>Quyidagilardan birini tanlang:\n\nHozirgi holat:\nTo'lovlar uchun kanal:</b> {vazifa}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🆕️ To'lovlar uchun", callback_data='vazifa')],
                [InlineKeyboardButton("◀️ Orqaga", callback_data='kanallar')]
            ])
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'vazifa':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Kanalingiz userini kiriting:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'vazifa')
            return
        
        # To'lov tizimi
        if data == 'new':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Yangi to'lov tizimi nomini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'turi')
            return
        
        if data.startswith('del-'):
            name = data.split('-')[1]
            del_pay_type(name)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data='hamyon')]])
            await query.edit_message_text(f"{name} - <b>To'lov tizimi olib tashlandi.</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if data == 'hamyon':
            pay_types = get_pay_types()
            if pay_types:
                keyboard = []
                for p in pay_types:
                    keyboard.append([InlineKeyboardButton(f"{p} - ni o'chirish", callback_data=f'del-{p}')])
                keyboard.append([InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')])
                await query.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')]])
                await query.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        # Xabarnoma
        if data == 'send':
            await query.message.delete()
            await context.bot.send_message(user_id, "*Xabaringizni kiriting:*", parse_mode='Markdown', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'users')
            return
        
        if data == 'forsend':
            await query.message.delete()
            await context.bot.send_message(user_id, "*Xabaringizni yuboring (forward):*", parse_mode='Markdown', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'forusers')
            return
        
        if data == 'user':
            await query.message.delete()
            await context.bot.send_message(user_id, "<b>Foydalanuvchi iD raqamini kiriting:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            set_user_step(user_id, 'user')
            return
        
        # Foydalanuvchi boshqarish
        if data == 'plus':
            target_id = get_user_temp(user_id)
            if target_id:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi')]])
                await query.edit_message_text(
                    f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobiga qancha pul qo'shmoqchisiz?</b>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                set_user_step(user_id, 'plus')
            return
        
        if data == 'minus':
            target_id = get_user_temp(user_id)
            if target_id:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi')]])
                await query.edit_message_text(
                    f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobidan qancha pul ayirmoqchisiz?</b>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                set_user_step(user_id, 'minus')
            return
        
        if data == 'ban':
            target_id = get_user_temp(user_id)
            if target_id and int(target_id) != ADMIN_ID:
                user = get_user(int(target_id))
                if user:
                    set_ban(int(target_id), 0 if user['ban'] else 1)
                    status = "bandan olindi!" if user['ban'] else "banlandi!"
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi')]])
                    await query.edit_message_text(
                        f"<b>Foydalanuvchi ({target_id}) {status}</b>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                await query.answer("Asosiy adminlarni blocklash mumkin emas!", show_alert=True)
            return
        
        if data == 'foydalanuvchi':
            target_id = get_user_temp(user_id)
            if target_id:
                user = get_user(int(target_id))
                if user:
                    bans = "🔕 Bandan olish" if user['ban'] else "🔔 Banlash"
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(bans, callback_data='ban')],
                        [InlineKeyboardButton("➕ Pul qo'shish", callback_data='plus'), InlineKeyboardButton("➖ Pul ayirish", callback_data='minus')]
                    ])
                    await query.edit_message_text(
                        f"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id={target_id}'>{target_id}</a>\n<b>Balans: {user['balance']} {get_setting('valyuta', 'so\'m')}\nTakliflar: {user['ref_count']} ta</b>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            return
    
    # ===== ODDIY FOYDALANUVCHI =====
    if data == 'yechish':
        pay_types = get_pay_types()
        if pay_types:
            keyboard = []
            for p in pay_types:
                keyboard.append([InlineKeyboardButton(p, callback_data=f'pay-{p}')])
            await query.edit_message_text(
                "👇 <b>Quyidagi to'lov tizimlaridan birini tanlang:</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.answer("To'lov tizimlari topilmadi!", show_alert=True)
        return
    
    if data.startswith('pay-'):
        wallet = data.split('-')[1]
        vazifa = get_setting('vazifa')
        if vazifa and vazifa != 'Kiritilmagan':
            user = get_user(user_id)
            narx = int(get_setting('narx', '3000'))
            if user and user['balance'] >= narx:
                await query.message.delete()
                await context.bot.send_message(
                    user_id,
                    "<b>Hamyoningiz raqamini yuboring:</b>",
                    parse_mode='HTML',
                    reply_markup=await get_back_menu()
                )
                set_user_step(user_id, f'wallet-{wallet}')
            else:
                await query.answer(
                    f"⛔ Jarayonni davom ettira olmaysiz!\n\nMinimal yechib olish miqdori: {narx} {get_setting('valyuta', 'so\'m')}",
                    show_alert=True
                )
        else:
            await query.answer("To'lovlar tarixi kanali ulanmagan!", show_alert=True)
        return
    
    if data == 'bekor':
        await query.message.delete()
        await context.bot.send_message(
            user_id,
            "⛔ <b>Bekor qilindi.</b>",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )
        return
    
    if data.startswith('tasdiq-'):
        parts = data.split('-')
        wallet = parts[1]
        number = parts[2]
        miqdor = int(parts[3])
        user = get_user(user_id)
        if user and user['balance'] >= miqdor:
            sub_balance(user_id, miqdor)
            add_solved(user_id, miqdor)
            await query.message.delete()
            await context.bot.send_message(
                user_id,
                "✅ <b>Qabul qilindi.</b>",
                parse_mode='HTML',
                reply_markup=await get_main_menu(user_id)
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Banlash", callback_data=f'block-{user_id}')],
                [InlineKeyboardButton("✅ To'landi", callback_data=f'tolandi-{user_id}-{number}-{miqdor}'),
                 InlineKeyboardButton("❌ To'lanmadi", callback_data=f'tolanmadi-{user_id}-{miqdor}')]
            ])
            await context.bot.send_message(
                ADMIN_ID,
                f"💵 <a href='tg://user?id={user_id}'>{user_id}</a> <b>pul yechib olmoqchi!</b>\n\n• <b>To'lov turi:</b> {wallet}\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqami:</b> {number}",
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
        else:
            await query.answer("Hisobingizda yetarli mablag' yo'q!", show_alert=True)
        return
    
    if data.startswith('tolandi-'):
        parts = data.split('-')
        uid = int(parts[1])
        number = parts[2]
        miqdor = int(parts[3])
        await query.message.delete()
        await context.bot.send_message(
            uid,
            f"<b>Hurmatli foydalanuvchi!\n\nPullaringizni yechib olish haqidagi arizangiz qabul qilindi.</b>",
            parse_mode='HTML'
        )
        await context.bot.send_message(
            ADMIN_ID,
            f"<b>✅ Foydalanuvchi puli to'lab berildi.</b>\n\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqami:</b> {number}",
            parse_mode='HTML'
        )
        return
    
    if data.startswith('tolanmadi-'):
        parts = data.split('-')
        uid = int(parts[1])
        miqdor = int(parts[2])
        add_balance(uid, miqdor)
        await query.message.delete()
        await context.bot.send_message(
            uid,
            f"<b>Hurmatli foydalanuvchi!\n\nPullaringizni yechib olish haqidagi arizangiz qabul qilinmadi.</b>",
            parse_mode='HTML'
        )
        await context.bot.send_message(
            ADMIN_ID,
            f"<b>❌ Foydalanuvchi arizasi bekor qilindi.</b>",
            parse_mode='HTML'
        )
        return
    
    if data.startswith('block-'):
        uid = int(data.split('-')[1])
        set_ban(uid, 1)
        await query.message.delete()
        await context.bot.send_message(
            uid,
            f"<b>Hurmatli foydalanuvchi!\n\nPullaringizni yechib olish haqidagi arizangiz qabul qilinmadi va botdan blocklandingiz.</b>",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        await context.bot.send_message(
            ADMIN_ID,
            f"<b>🔔 Foydalanuvchi blocklandi.</b>",
            parse_mode='HTML'
        )
        return

# ============ MATN HANDLER ============
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ''
    
    user = get_user(user_id)
    if not user:
        create_user(user_id)
        user = get_user(user_id)
    
    if user['ban'] and user_id != ADMIN_ID:
        return
    
    if not await number_check(context, user_id, first_name, last_name):
        return
    
    if not await joinchat(context, user_id):
        return
    
    step = user['step'] if user else ''
    
    if text == "◀️ Orqaga":
        set_user_step(user_id, '')
        await update.message.reply_text(
            "<b>🖥 Asosiy menyuga qaytdingiz.</b>",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )
        return
    
    if text == "💵 Pul ishlash":
        bot_info = await context.bot.get_me()
        reflink = f"https://t.me/{bot_info.username}?start={user_id}"
        caption = f"<b>🔗 Sizning taklif havolangiz:</b>\n\n{reflink}\n\n<i>Yuqoridagi taklif havolangizni do'stlaringizga tarqating va har bir to'liq ro'yxatdan o'tgan taklifingiz uchun 250 so'm hisobingizga qo'shiladi.</i>"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("↗️ Ulashish", url=f"https://t.me/share/url?url={reflink}")]])
        await update.message.reply_text(caption, parse_mode='HTML', reply_markup=keyboard)
        return
    
    if text == "💰 Hisobim":
        valyuta = get_setting('valyuta', "so'm")
        text_cab = f"<b>🔑 Sizning ID raqamingiz:</b> <pre>{user_id}</pre>\n\n💵 <b>Asosiy balansingiz:</b> {user['balance']} {valyuta}\n👤 <b>Takliflaringiz soni:</b> {user['ref_count']} ta\n\n💳 <b>Yechib olgan pullaringiz:</b> {user['solved']} {valyuta}"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏦 Pul yechish", callback_data='yechish')]])
        await update.message.reply_text(text_cab, parse_mode='HTML', reply_markup=keyboard)
        return
    
    if text == "🏦 Pul yechish":
        pay_types = get_pay_types()
        if pay_types:
            keyboard = []
            for p in pay_types:
                keyboard.append([InlineKeyboardButton(p, callback_data=f'pay-{p}')])
            await update.message.reply_text(
                "👇 <b>Quyidagi to'lov tizimlaridan birini tanlang:</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("<b>To'lov tizimlari topilmadi!</b>", parse_mode='HTML')
        return
    
    if text == "🧾 To'lovlar tarixi":
        vazifa = get_setting('vazifa')
        if vazifa and vazifa != 'Kiritilmagan':
            kanal = vazifa.replace('@', '')
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{kanal}")]])
            await update.message.reply_text(
                "<b>🧾 To'lovlar tarixi kanali:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text("<b>To'lovlar tarixi kanali kiritilmagan!</b>", parse_mode='HTML')
        return
    
    if text == "📨 Murojaat":
        await update.message.reply_text(
            "📝 <b>Murojaat matnini yuboring:</b>",
            parse_mode='HTML',
            reply_markup=await get_back_menu()
        )
        set_user_step(user_id, 'yordam')
        return
    
    if step == 'yordam':
        await context.bot.send_message(
            ADMIN_ID,
            f"<a href='tg://user?id={user_id}'>{user_id}</a> <b>dan yangi xabar:</b> {text}",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        await update.message.reply_text(
            "✅ <b>Murojaatingiz yuborildi.</b>\n\nTez orada javob qaytaramiz!",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )
        set_user_step(user_id, '')
        return
    
    # ===== ADMIN PANEL =====
    if user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await update.message.reply_text(
                "<b>Boshqaruv panelidasiz.</b>",
                parse_mode='HTML',
                reply_markup=await get_panel_menu()
            )
            set_user_step(user_id, '')
            return
        
        if text == "⚙ Asosiy sozlamalar":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📑 Hozirgi holat", callback_data='holat')],
                [InlineKeyboardButton("🔗 Taklif narxi", callback_data='taklif'), InlineKeyboardButton("💶 Valyuta", callback_data='valyuta')],
                [InlineKeyboardButton("💵 Minimal pul yechish narxi", callback_data='narx')],
                [InlineKeyboardButton("📎 Admin useri", callback_data='admin'), InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await update.message.reply_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if text == "📢 Kanallar":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Majburiy obunalar", callback_data='majburiy')],
                [InlineKeyboardButton("*⃣ Qo'shimcha kanallar", callback_data='qoshimcha')],
                [InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await update.message.reply_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if text == "📊 Statistika":
            count = get_stat_count()
            await update.message.reply_text(
                f"<b>👥 Foydalanuvchilar: {count} ta</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Yopish", callback_data='yopish')]])
            )
            return
        
        if text == "🔎 Foydalanuvchini boshqarish":
            await update.message.reply_text(
                "<b>Kerakli foydalanuvchining ID raqamini kiriting:</b>",
                parse_mode='HTML',
                reply_markup=await get_boshqarish()
            )
            set_user_step(user_id, 'iD')
            return
        
        if text == "🎛 Tugmalar":
            await update.message.reply_text("<b>Tugmalar sozlamasi mavjud emas!</b>", parse_mode='HTML')
            return
        
        if text == "📃 Matnlar":
            await update.message.reply_text("<b>Matnlar sozlamasi mavjud emas!</b>", parse_mode='HTML')
            return
        
        if text == "💳 To'lov tizimi":
            pay_types = get_pay_types()
            if pay_types:
                keyboard = []
                for p in pay_types:
                    keyboard.append([InlineKeyboardButton(f"{p} - ni o'chirish", callback_data=f'del-{p}')])
                keyboard.append([InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')])
                await update.message.reply_text(
                    "<b>Quyidagilardan birini tanlang:</b>",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')]])
                await update.message.reply_text("<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return
        
        if text == "📨 Xabarnoma":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Oddiy xabar", callback_data='send'), InlineKeyboardButton("Forward xabar", callback_data='forsend')],
                [InlineKeyboardButton("Foydalanuvchiga xabar", callback_data='user')]
            ])
            await update.message.reply_text("<b>Yuboriladigan xabar turini tanlang;</b>", parse_mode='HTML', reply_markup=keyboard)
            return
    
    # ===== STEP =====
    if step == 'iD' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        target = get_user(int(text))
        if target:
            set_user_temp(user_id, text)
            bans = "🔕 Bandan olish" if target['ban'] else "🔔 Banlash"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(bans, callback_data='ban')],
                [InlineKeyboardButton("➕ Pul qo'shish", callback_data='plus'), InlineKeyboardButton("➖ Pul ayirish", callback_data='minus')]
            ])
            await update.message.reply_text(
                f"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id={text}'>{text}</a>\n<b>Balans: {target['balance']} {get_setting('valyuta', 'so\'m')}\nTakliflar: {target['ref_count']} ta</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("<b>Foydalanuvchi topilmadi.\n\nQayta urinib ko'ring:</b>", parse_mode='HTML')
        return
    
    if step == "qo'shish" and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        if '@' in text:
            add_channel(text)
            await update.message.reply_text(f"<b>{text} - kanal qo'shildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("<b>Kanalingiz useri yuboring:\n\nNamuna:</b> @ORGBuilder", parse_mode='HTML')
        return
    
    if step == 'vazifa' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        if '@' in text:
            set_setting('vazifa', text)
            await update.message.reply_text("<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("⚠️ <b>Kanal manzili kiritishda xatolik!\n\nQayta urinib ko'ring:</b>", parse_mode='HTML')
        return
    
    if step == 'turi' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        add_pay_type(text)
        await update.message.reply_text("<b>Yangi to'lov tizimi qo'shildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        set_user_step(user_id, '')
        return
    
    if step == 'taklifpul' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        if text.isdigit():
            set_setting('taklif', text)
            await update.message.reply_text("<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("<b>Faqat raqam kiriting!</b>", parse_mode='HTML')
        return
    
    if step == 'valyuta' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        set_setting('valyuta', text)
        await update.message.reply_text("<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        set_user_step(user_id, '')
        return
    
    if step == 'narx' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        if text.isdigit():
            set_setting('narx', text)
            await update.message.reply_text("<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("<b>Faqat raqam kiriting!</b>", parse_mode='HTML')
        return
    
    if step == 'admin-user' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        set_setting('admin_user', text)
        await update.message.reply_text("<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        set_user_step(user_id, '')
        return
    
    if step == 'plus' and user_id == ADMIN_ID:
        if text.isdigit():
            target_id = int(get_user_temp(user_id))
            add_balance(target_id, int(text))
            await context.bot.send_message(target_id, f"<b>Adminlar tomonidan hisobingiz {text} {get_setting('valyuta', 'so\'m')} to'ldirildi</b>", parse_mode='HTML')
            await update.message.reply_text(f"<b>Foydalanuvchi hisobiga {text} {get_setting('valyuta', 'so\'m')} qo'shildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("<b>Faqat raqamlardan foydalaning!</b>", parse_mode='HTML')
        return
    
    if step == 'minus' and user_id == ADMIN_ID:
        if text.isdigit():
            target_id = int(get_user_temp(user_id))
            sub_balance(target_id, int(text))
            await context.bot.send_message(target_id, f"<b>Adminlar tomonidan hisobingizdan {text} {get_setting('valyuta', 'so\'m')} olib tashlandi</b>", parse_mode='HTML')
            await update.message.reply_text(f"<b>Foydalanuvchi hisobidan {text} {get_setting('valyuta', 'so\'m')} olib tashlandi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        else:
            await update.message.reply_text("<b>Faqat raqamlardan foydalaning!</b>", parse_mode='HTML')
        return
    
    if step == 'user' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        if text.isdigit():
            set_user_temp(user_id, text)
            await update.message.reply_text("<b>Xabaringizni kiriting:</b>", parse_mode='HTML')
            set_user_step(user_id, 'xabar')
        else:
            await update.message.reply_text("<b>Faqat raqamlardan foydalaning!</b>", parse_mode='HTML')
        return
    
    if step == 'xabar' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            set_user_step(user_id, '')
            return
        target_id = get_user_temp(user_id)
        if target_id:
            await context.bot.send_message(int(target_id), text, parse_mode='HTML')
            await update.message.reply_text("<b>Xabaringiz yuborildi ✅</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            set_user_step(user_id, '')
        return
    
    if step == 'users' and user_id == ADMIN_ID:
        users = get_all_users()
        count = 0
        for uid in users:
            try:
                await context.bot.send_message(uid, text, parse_mode='HTML')
                count += 1
            except:
                pass
        await update.message.reply_text(f"<b>Hammaga yuborildi ✅ ({count} ta)</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        set_user_step(user_id, '')
        return
    
    if step and step.startswith('wallet-'):
        wallet = step.split('-')[1]
        if text == "◀️ Orqaga":
            set_user_step(user_id, '')
            return
        if text.isdigit():
            set_user_temp(user_id, text)
            keyboard = ReplyKeyboardMarkup([[KeyboardButton(str(user['balance']))], [KeyboardButton("◀️ Orqaga")]], resize_keyboard=True)
            await update.message.reply_text(
                "<b>Qancha miqdorda pul yechib olmoqchisiz:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            set_user_step(user_id, f'miqdor-{wallet}')
        else:
            await update.message.reply_text("<b>Hamyoningiz raqamini yuboring:</b>", parse_mode='HTML')
        return
    
    if step and step.startswith('miqdor-'):
        wallet = step.split('-')[1]
        if text == "◀️ Orqaga":
            set_user_step(user_id, '')
            return
        if text.isdigit():
            miqdor = int(text)
            narx = int(get_setting('narx', '3000'))
            if miqdor >= narx:
                if user['balance'] >= miqdor:
                    num = get_user_temp(user_id)
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f'tasdiq-{wallet}-{num}-{miqdor}')],
                        [InlineKeyboardButton("🚫 Bekor qilish", callback_data='bekor')]
                    ])
                    await update.message.reply_text(
                        f"✅ <b>Qabul qilindi!</b>\n\n• <b>To'lov turi:</b> {wallet}\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqamingiz:</b> {num}\n\n<b>Ma'lumotlar to'g'ri ekanligiga ishonch hosil qilgan bo'lsangiz, ✅ Tasdiqlash tugmasini bosing!</b>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                    set_user_step(user_id, '')
                else:
                    await update.message.reply_text("<b>Hisobingizda yetarli mablag' mavjud emas!</b>\n\nQayta urunib ko'ring:", parse_mode='HTML')
            else:
                await update.message.reply_text(
                    f"<b>Minimal yechib olish miqdori:</b> {narx} {get_setting('valyuta', 'so\'m')}\n\nQayta urunib ko'ring:",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text("<b>Qancha miqdorda pul yechib olmoqchisiz:</b>", parse_mode='HTML')
        return

# ============ FORWARD ============
async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    step = get_user_step(user_id)
    if step == 'forusers':
        users = get_all_users()
        count = 0
        for uid in users:
            try:
                await update.message.forward(chat_id=uid)
                count += 1
            except:
                pass
        await update.message.reply_text(f"<b>Hammaga yuborildi ✅ ({count} ta)</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        set_user_step(user_id, '')

# ============ ISHGA TUSHIRISH ============
def main():
    init_db()
    print("✅ Bot ishga tushmoqda...")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.CONTACT, contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.FORWARDED, forward_handler))
    application.add_handler(CallbackQueryHandler(callback))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
