import os
import json
import datetime
import asyncio
import sqlite3
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ============ KONFIG ============
API_TOKEN = '8954102314:AAEVx-GpYc32S8HQWOrj-5A0R3iup09Cn68'          # O'z tokeningiz
ADMIN_ID = 8758410535            # O'z ID'ngiz (integer)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# ============ BAZA YARATISH ============
DB_PATH = 'bot.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar
        await db.execute('''
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
        # Sozlamalar
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Majburiy kanallar
        await db.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        ''')
        # To'lov tizimlari
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pay_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')
        # Matnlar (sozlamalar)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS texts (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Tugmalar (sozlamalar)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS buttons (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Statistika (azo.dat o'rniga)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        # Standart qiymatlarni kiritish (agar mavjud bo'lmasa)
        default_settings = {
            'taklif': '250',
            'valyuta': "so'm",
            'narx': '3000',
            'vazifa': 'Kiritilmagan',
            'admin_user': 'Kiritilmagan'
        }
        for k, v in default_settings.items():
            await db.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))
        
        # Standart tugmalar
        default_buttons = {
            'earn': 'earn', 'solve': 'solve', 'cabinet': 'cabinet',
            'tolov': 'tolov', 'support': 'support', 'manual': 'manual',
            'back': 'back', 'getPhone': 'getPhone', 'check': 'check',
            'contiune': 'contiune', 'share': 'share', 'cancellation': 'cancellation',
            'confirm': 'confirm', 'transition': 'transition'
        }
        for k, v in default_buttons.items():
            await db.execute('INSERT OR IGNORE INTO buttons (key, value) VALUES (?, ?)', (k, v))
        
        # Standart matnlar
        default_texts = {
            'welcome': 'welcome', 'subChannels': 'subChannels', 'tolovtext': 'tolovtext',
            'newRef': 'newRef', 'checkRef': 'checkRef', 'backHome': 'backHome',
            'textPhone': 'textPhone', 'conPhone': 'conPhone', 'noPhone': 'noPhone',
            'earnRef': 'earnRef', 'cabinet': 'cabinet', 'selectPayType': 'selectPayType',
            'minimum': 'minimum', 'noChannel': 'noChannel', 'sendCard': 'sendCard',
            'accpeted': 'accpeted', 'solveMoney': 'solveMoney', 'solveMinimum': 'solveMinimum',
            'lowBalance': 'lowBalance', 'accped': 'accped', 'canceled': 'canceled',
            'hasBeenPaid': 'hasBeenPaid', 'wasNotPaid': 'wasNotPaid', 'block': 'block',
            'BeenPaid': 'BeenPaid', 'manuals': 'manuals', 'advertising': 'advertising',
            'sendSuppMsg': 'sendSuppMsg', 'SuppSend': 'SuppSend'
        }
        for k, v in default_texts.items():
            await db.execute('INSERT OR IGNORE INTO texts (key, value) VALUES (?, ?)', (k, v))
        
        await db.commit()

# ============ YORDAMCHI FUNKSIYALAR ============
async def get_setting(key, default=''):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = await cursor.fetchone()
        return row[0] if row else default

async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = await cursor.fetchone()
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

async def create_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO users (id, balance, solved, ref_count, ban) VALUES (?, 0, 0, 0, 0)', (user_id,))
        await db.commit()

async def set_user_step(user_id, step):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET step = ? WHERE id = ?', (step, user_id))
        await db.commit()

async def set_user_temp(user_id, data):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET temp_data = ? WHERE id = ?', (data, user_id))
        await db.commit()

async def get_user_step(user_id):
    user = await get_user(user_id)
    return user['step'] if user else None

async def add_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
        await db.commit()

async def sub_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
        await db.commit()

async def add_solved(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET solved = solved + ? WHERE id = ?', (amount, user_id))
        await db.commit()

async def inc_ref(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET ref_count = ref_count + 1 WHERE id = ?', (user_id,))
        await db.commit()

async def set_phone(user_id, phone):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
        await db.commit()

async def set_ban(user_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET ban = ? WHERE id = ?', (1 if status else 0, user_id))
        await db.commit()

async def add_stat(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO stats (user_id) VALUES (?)', (user_id,))
        await db.commit()

async def get_stat_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM stats')
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT user_id FROM stats')
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

# Kanallar
async def add_channel(url):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO channels (url) VALUES (?)', (url,))
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT url FROM channels')
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def clear_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM channels')
        await db.commit()

# To'lov tizimlari
async def add_pay_type(name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO pay_types (name) VALUES (?)', (name,))
        await db.commit()

async def get_pay_types():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT name FROM pay_types')
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def del_pay_type(name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM pay_types WHERE name = ?', (name,))
        await db.commit()

# Tugma va matnlar
async def get_button(key):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT value FROM buttons WHERE key = ?', (key,))
        row = await cursor.fetchone()
        return row[0] if row else key

async def set_button(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO buttons (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

async def get_text(key, replacements=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT value FROM texts WHERE key = ?', (key,))
        row = await cursor.fetchone()
        text = row[0] if row else key
    if replacements:
        for k, v in replacements.items():
            text = text.replace(f'%{k}%', str(v))
    return text

async def set_text(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO texts (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

# ============ KANAL TEKSHIRISH ============
async def joinchat(user_id):
    channels = await get_channels()
    if not channels:
        return True
    keyboard = []
    uns = False
    for url in channels:
        if '@' in url:
            clean = url.split('@')[1]
            try:
                member = await bot.get_chat_member(chat_id=f'@{clean}', user_id=user_id)
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
        await bot.send_message(
            user_id,
            "<b>⚠️ Botdan to'liq foydalanish uchun quyidagi kanallarimizga obuna bo'ling!</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return False
    return True

# ============ TELEFON RAQAM SO'RASH ============
async def number_check(user_id, first_name, last_name):
    user = await get_user(user_id)
    if user and user['phone']:
        return True
    await set_user_step(user_id, 'request_contact')
    getPhone = await get_button('getPhone')
    text = await get_text('textPhone', {
        'first': first_name,
        'last': last_name,
        'id': user_id,
        'hour': datetime.datetime.now().strftime('%H:%M'),
        'date': datetime.datetime.now().strftime('%d.%m.%Y')
    })
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(getPhone, request_contact=True))
    await bot.send_message(user_id, text, parse_mode='HTML', reply_markup=keyboard)
    return False

# ============ MENU YARATISH ============
async def get_main_menu(user_id):
    earn = await get_button('earn')
    solve = await get_button('solve')
    cabinet = await get_button('cabinet')
    tolov = await get_button('tolov')
    support = await get_button('support')
    manual = await get_button('manual')
    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton(earn)],
            [KeyboardButton(cabinet), KeyboardButton(solve)],
            [KeyboardButton(tolov)],
            [KeyboardButton(support), KeyboardButton(manual)],
            [KeyboardButton("🗄 Boshqarish")]
        ]
    else:
        keyboard = [
            [KeyboardButton(earn)],
            [KeyboardButton(cabinet), KeyboardButton(solve)],
            [KeyboardButton(tolov)],
            [KeyboardButton(support), KeyboardButton(manual)]
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def get_back_menu():
    orqa = await get_button('back')
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(orqa)]],
        resize_keyboard=True
    )

async def get_panel_menu():
    orqa = await get_button('back')
    keyboard = [
        [KeyboardButton("⚙ Asosiy sozlamalar")],
        [KeyboardButton("📢 Kanallar"), KeyboardButton("📊 Statistika")],
        [KeyboardButton("🔎 Foydalanuvchini boshqarish")],
        [KeyboardButton("🎛 Tugmalar"), KeyboardButton("📃 Matnlar")],
        [KeyboardButton("💳 To'lov tizimi")],
        [KeyboardButton("📨 Xabarnoma"), KeyboardButton(orqa)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def get_boshqarish():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("🗄 Boshqarish")]],
        resize_keyboard=True
    )

# ============ START ============
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ''
    await create_user(user_id)
    await add_stat(user_id)

    if not await number_check(user_id, first_name, last_name):
        return

    # Referal
    text = message.text
    if ' ' in text:
        ref_id = text.split(' ')[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            ref_id = int(ref_id)
            user = await get_user(ref_id)
            if user and str(user_id) not in await get_all_users():
                taklif = int(await get_setting('taklif', '250'))
                await add_balance(ref_id, taklif)
                await inc_ref(ref_id)
                newRef = await get_text('newRef', {
                    'reffirst': first_name,
                    'reflast': last_name,
                    'refid': user_id,
                    'refpay': taklif,
                    'currency': await get_setting('valyuta', "so'm")
                })
                await bot.send_message(ref_id, newRef, parse_mode='HTML')
                checkRef = await get_text('checkRef', {
                    'reffirst': first_name,
                    'reflast': last_name,
                    'refid': user_id,
                    'refpay': taklif,
                    'currency': await get_setting('valyuta', "so'm")
                })
                await bot.send_message(ref_id, checkRef, parse_mode='HTML')

    if not await joinchat(user_id):
        return

    welcome = await get_text('welcome', {
        'first': first_name,
        'last': last_name,
        'id': user_id,
        'hour': datetime.datetime.now().strftime('%H:%M'),
        'date': datetime.datetime.now().strftime('%d.%m.%Y')
    })
    await bot.send_message(user_id, welcome, parse_mode='HTML', reply_markup=await get_main_menu(user_id))

# ============ KONTAKT ============
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):
    user_id = message.from_user.id
    contact = message.contact
    if contact.user_id != user_id:
        return
    phone = contact.phone_number.replace('+', '')
    if len(phone) == 12 and phone.startswith('998'):
        await set_phone(user_id, phone)
        await set_user_step(user_id, '')
        conPhone = await get_text('conPhone', {
            'first': message.from_user.first_name,
            'last': message.from_user.last_name or '',
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y'),
            'phone': phone
        })
        contiune = await get_button('contiune')
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(contiune, callback_data='davom'))
        await bot.send_message(user_id, conPhone, parse_mode='HTML', reply_markup=keyboard)
    else:
        noPhone = await get_text('noPhone', {
            'first': message.from_user.first_name,
            'last': message.from_user.last_name or '',
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await set_ban(user_id, 1)
        await set_user_step(user_id, '')
        await bot.send_message(user_id, noPhone, parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())

# ============ "davom" ============
@dp.callback_query_handler(lambda c: c.data == 'davom')
async def davom_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await bot.delete_message(user_id, callback.message.message_id)
    welcome = await get_text('welcome', {
        'first': callback.from_user.first_name,
        'last': callback.from_user.last_name or '',
        'id': user_id,
        'hour': datetime.datetime.now().strftime('%H:%M'),
        'date': datetime.datetime.now().strftime('%d.%m.%Y')
    })
    await bot.send_message(user_id, welcome, parse_mode='HTML', reply_markup=await get_main_menu(user_id))

# ============ "check" ============
@dp.callback_query_handler(lambda c: c.data == 'check')
async def check_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await bot.delete_message(user_id, callback.message.message_id)
    if await joinchat(user_id):
        ref_id = await get_user_temp(user_id)  # temp_data da saqlaymiz
        if ref_id and ref_id.isdigit():
            ref_id = int(ref_id)
            if ref_id != user_id:
                taklif = int(await get_setting('taklif', '250'))
                await add_balance(ref_id, taklif)
                await inc_ref(ref_id)
                checkRef = await get_text('checkRef', {
                    'reffirst': callback.from_user.first_name,
                    'reflast': callback.from_user.last_name or '',
                    'refid': user_id,
                    'refpay': taklif,
                    'currency': await get_setting('valyuta', "so'm")
                })
                await bot.send_message(ref_id, checkRef, parse_mode='HTML')
                await set_user_temp(user_id, '')
        welcome = await get_text('welcome', {
            'first': callback.from_user.first_name,
            'last': callback.from_user.last_name or '',
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.send_message(user_id, welcome, parse_mode='HTML', reply_markup=await get_main_menu(user_id))

# ============ ASOSIY TEXT HANDLER ============
@dp.message_handler(content_types=types.ContentType.TEXT)
async def text_handler(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ''
    username = message.from_user.username or ''

    user = await get_user(user_id)
    if not user:
        await create_user(user_id)
        user = await get_user(user_id)

    if user['ban'] and user_id != ADMIN_ID:
        return

    if not await number_check(user_id, first_name, last_name):
        return

    if not await joinchat(user_id):
        return

    step = user['step'] if user else ''

    # ===== ORQA =====
    orqa = await get_button('back')
    if text == orqa:
        await set_user_step(user_id, '')
        welcome = await get_text('backHome', {
            'first': first_name,
            'last': last_name,
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.send_message(user_id, welcome, parse_mode='HTML', reply_markup=await get_main_menu(user_id))
        return

    # ===== EARN =====
    earn = await get_button('earn')
    if text == earn:
        ref_pay = await get_setting('taklif', '250')
        valyuta = await get_setting('valyuta', "so'm")
        reflink = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
        caption = await get_text('earnRef', {
            'first': first_name,
            'last': last_name,
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y'),
            'reflink': reflink,
            'refpay': ref_pay,
            'refcount': user['ref_count'],
            'balance': user['balance'],
            'currency': valyuta
        })
        share = await get_button('share')
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(share, url=f"https://t.me/share/url?url={reflink}"))
        await bot.send_message(user_id, caption, parse_mode='HTML', reply_markup=keyboard)
        return

    # ===== CABINET =====
    cabinet = await get_button('cabinet')
    if text == cabinet:
        text_cab = await get_text('cabinet', {
            'first': first_name,
            'last': last_name,
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y'),
            'balance': user['balance'],
            'solve': user['solved'],
            'refcount': user['ref_count'],
            'currency': await get_setting('valyuta', "so'm")
        })
        solve_txt = await get_button('solve')
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(solve_txt, callback_data='yechish'))
        await bot.send_message(user_id, text_cab, parse_mode='HTML', reply_markup=keyboard)
        return

    # ===== SOLVE =====
    solve_txt = await get_button('solve')
    if text == solve_txt:
        pay_types = await get_pay_types()
        if pay_types:
            keyboard = []
            for p in pay_types:
                keyboard.append([InlineKeyboardButton(p, callback_data=f'pay-{p}')])
            select = await get_text('selectPayType', {
                'first': first_name,
                'last': last_name,
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            })
            await bot.send_message(user_id, select, parse_mode='HTML',
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        else:
            await bot.send_message(user_id, "<b>To'lov tizimlari topilmadi!</b>", parse_mode='HTML')
        return

    # ===== TOLOV =====
    tolov_txt = await get_button('tolov')
    if text == tolov_txt:
        vazifa = await get_setting('vazifa')
        if vazifa and vazifa != 'Kiritilmagan':
            kanal = vazifa.replace('@', '')
            tolovtext = await get_text('tolovtext', {
                'first': first_name,
                'last': last_name,
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            })
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(tolov_txt, url=f"https://t.me/{kanal}"))
            await bot.send_message(user_id, tolovtext, parse_mode='HTML', reply_markup=keyboard)
        else:
            await bot.send_message(user_id, "<b>To'lovlar kanali kiritilmagan!</b>", parse_mode='HTML')
        return

    # ===== MANUAL =====
    manual_txt = await get_button('manual')
    if text == manual_txt:
        manuals = await get_text('manuals', {
            'first': first_name,
            'last': last_name,
            'id': user_id,
            'username': username,
            'botname': (await bot.get_me()).username,
            'user': await get_setting('admin_user', 'Kiritilmagan'),
            'balance': user['balance'],
            'refcount': user['ref_count'],
            'currency': await get_setting('valyuta', "so'm"),
            'solve': user['solved'],
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.send_message(user_id, manuals, parse_mode='HTML', disable_web_page_preview=True)
        return

    # ===== SUPPORT =====
    support_txt = await get_button('support')
    if text == support_txt:
        sendSuppMsg = await get_text('sendSuppMsg', {
            'first': first_name,
            'last': last_name,
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.send_message(user_id, sendSuppMsg, parse_mode='HTML', reply_markup=await get_back_menu())
        await set_user_step(user_id, 'yordam')
        return

    # ===== YORDAM =====
    if step == 'yordam':
        SuppSend = await get_text('SuppSend', {
            'first': first_name,
            'last': last_name,
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.send_message(ADMIN_ID, f"<a href='tg://user?id={user_id}'>{user_id}</a> <b>dan yangi xabar:</b> {text}",
                               parse_mode='HTML', disable_web_page_preview=True)
        await bot.send_message(user_id, SuppSend, parse_mode='HTML', reply_markup=await get_main_menu(user_id))
        await set_user_step(user_id, '')
        return

    # ===== ADMIN PANEL =====
    if user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await bot.send_message(user_id, "<b>Boshqaruv panelidasiz.</b>", parse_mode='HTML',
                                   reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
            return

        if text == "⚙ Asosiy sozlamalar":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📑 Hozirgi holat", callback_data='holat')],
                [InlineKeyboardButton("🔗 Taklif narxi", callback_data='taklif'), InlineKeyboardButton("💶 Valyuta", callback_data='valyuta')],
                [InlineKeyboardButton("💵 Minimal pul yechish narxi", callback_data='narx')],
                [InlineKeyboardButton("📎 Admin useri", callback_data='admin'), InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await bot.send_message(user_id, "<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return

        if text == "📢 Kanallar":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🔐 Majburiy obunalar", callback_data='majburiy')],
                [InlineKeyboardButton("*⃣ Qo'shimcha kanallar", callback_data='qoshimcha')],
                [InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await bot.send_message(user_id, "<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return

        if text == "📊 Statistika":
            count = await get_stat_count()
            await bot.send_message(user_id, f"<b>👥 Foydalanuvchilar: {count} ta</b>", parse_mode='HTML',
                                   reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Yopish", callback_data='yopish')))
            return

        if text == "🔎 Foydalanuvchini boshqarish":
            await bot.send_message(user_id, "<b>Kerakli foydalanuvchining ID raqamini kiriting:</b>",
                                   parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'iD')
            return

        if text == "🎛 Tugmalar":
            await bot.send_message(user_id, "<b>Tugma kodini kiriting:</b>", parse_mode='HTML',
                                   reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'tugma-kodi')
            return

        if text == "📃 Matnlar":
            await bot.send_message(user_id, "<b>Matn kodini kiriting:</b>", parse_mode='HTML',
                                   reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'matn-kodi')
            return

        if text == "💳 To'lov tizimi":
            pay_types = await get_pay_types()
            if pay_types:
                keyboard = []
                for p in pay_types:
                    keyboard.append([InlineKeyboardButton(f"{p} - ni o'chirish", callback_data=f'del-{p}')])
                keyboard.append([InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')])
                await bot.send_message(user_id, "<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML',
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            else:
                keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new'))
                await bot.send_message(user_id, "<b>Quyidagilardan birini tanlang:</b>", parse_mode='HTML', reply_markup=keyboard)
            return

        if text == "📨 Xabarnoma":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Oddiy xabar", callback_data='send'), InlineKeyboardButton("Forward xabar", callback_data='forsend')],
                [InlineKeyboardButton("Foydalanuvchiga xabar", callback_data='user')]
            ])
            await bot.send_message(user_id, "<b>Yuboriladigan xabar turini tanlang;</b>", parse_mode='HTML', reply_markup=keyboard)
            return

    # ===== STEP BO'YICHA QAYTA ISHLASH =====
    # iD
    if step == 'iD' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        target = await get_user(int(text))
        if target:
            await set_user_temp(user_id, text)
            bans = "🔕 Bandan olish" if target['ban'] else "🔔 Banlash"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(bans, callback_data='ban')],
                [InlineKeyboardButton("➕ Pul qo'shish", callback_data='plus'), InlineKeyboardButton("➖ Pul ayirish", callback_data='minus')]
            ])
            await bot.send_message(user_id, f"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id={text}'>{text}</a>\n<b>Balans: {target['balance']} {await get_setting('valyuta', 'so\'m')}\nTakliflar: {target['ref_count']} ta</b>",
                                   parse_mode='HTML', reply_markup=keyboard)
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Foydalanuvchi topilmadi.\n\nQayta urinib ko'ring:</b>", parse_mode='HTML')
        return

    # tugma-kodi
    if step == 'tugma-kodi' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        # Check if key exists in buttons (we can just allow any key)
        await set_user_temp(user_id, text)
        await bot.send_message(user_id, f"<pre>{text}</pre> <b>qabul qilindi.</b>\n\n<i>Ushbu kod uchun qiymatni kiriting:</i>",
                               parse_mode='HTML')
        await set_user_step(user_id, 'tugma-qiymat')
        return

    if step == 'tugma-qiymat' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        key = await get_user_temp(user_id)
        if key:
            await set_button(key, text)
            await bot.send_message(user_id, "<b>O'zgartirish yakunlandi!</b>", parse_mode='HTML',
                                   reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        return

    # matn-kodi
    if step == 'matn-kodi' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await set_user_temp(user_id, text)
        await bot.send_message(user_id, f"<pre>{text}</pre> <b>qabul qilindi.</b>\n\n<i>Ushbu kod uchun qiymatni kiriting:</i>",
                               parse_mode='HTML')
        await set_user_step(user_id, 'matn-qiymat')
        return

    if step == 'matn-qiymat' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        key = await get_user_temp(user_id)
        if key:
            await set_text(key, text)
            await bot.send_message(user_id, "<b>O'zgartirish yakunlandi!</b>", parse_mode='HTML',
                                   reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        return

    # qo'shish (majburiy kanal)
    if step == "qo'shish" and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if '@' in text:
            await add_channel(text)
            await bot.send_message(user_id, f"<b>{text} - kanal qo'shildi!</b>", parse_mode='HTML',
                                   reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Kanalingiz useri yuboring:\n\nNamuna:</b> @ORGBuilder", parse_mode='HTML')
        return

    # vazifa (to'lov kanali)
    if step == 'vazifa' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if '@' in text:
            try:
                chat = await bot.get_chat(text)
                if chat.type in ['channel', 'group', 'supergroup']:
                    await set_setting('vazifa', text)
                    await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML',
                                           reply_markup=await get_panel_menu())
                    await set_user_step(user_id, '')
                else:
                    await bot.send_message(user_id, "<b>Bot ushbu kanalda admin emas yoki noto'g'ri kanal manzili yuborildi!</b>", parse_mode='HTML')
            except:
                await bot.send_message(user_id, "<b>Bot ushbu kanalda admin emas yoki noto'g'ri kanal manzili yuborildi!</b>", parse_mode='HTML')
        else:
            await bot.send_message(user_id, "⚠️ <b>Kanal manzili kiritishda xatolik!\n\nQayta urinib ko'ring:</b>", parse_mode='HTML')
        return

    # turi (to'lov tizimi qo'shish)
    if step == 'turi' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await add_pay_type(text)
        await bot.send_message(user_id, "<b>Yangi to'lov tizimi qo'shildi!</b>", parse_mode='HTML',
                               reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')
        return

    # taklifpul, valyuta, narx, admin-user
    if step == 'taklifpul' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_setting('taklif', text)
            await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML',
                                   reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Faqat raqam kiriting!</b>", parse_mode='HTML')
        return

    if step == 'valyuta' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await set_setting('valyuta', text)
        await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML',
                               reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')
        return

    if step == 'narx' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_setting('narx', text)
            await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML',
                                   reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Faqat raqam kiriting!</b>", parse_mode='HTML')
        return

    if step == 'admin-user' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await set_setting('admin_user', text)
        await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML',
                               reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')
        return

    # plus/minus
    if step == 'plus' and user_id == ADMIN_ID:
        if text.isdigit():
            target_id = int(await get_user_temp(user_id))
            await add_balance(target_id, int(text))
            await bot.send_message(target_id, f"<b>Adminlar tomonidan hisobingiz {text} {await get_setting('valyuta', 'so\'m')} to'ldirildi</b>", parse_mode='HTML')
            await bot.send_message(user_id, f"<b>Foydalanuvchi hisobiga {text} {await get_setting('valyuta', 'so\'m')} qo'shildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Faqat raqamlardan foydalaning!</b>", parse_mode='HTML')
        return

    if step == 'minus' and user_id == ADMIN_ID:
        if text.isdigit():
            target_id = int(await get_user_temp(user_id))
            await sub_balance(target_id, int(text))
            await bot.send_message(target_id, f"<b>Adminlar tomonidan hisobingizdan {text} {await get_setting('valyuta', 'so\'m')} olib tashlandi</b>", parse_mode='HTML')
            await bot.send_message(user_id, f"<b>Foydalanuvchi hisobidan {text} {await get_setting('valyuta', 'so\'m')} olib tashlandi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Faqat raqamlardan foydalaning!</b>", parse_mode='HTML')
        return

    # user (foydalanuvchiga xabar)
    if step == 'user' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_user_temp(user_id, text)
            await bot.send_message(user_id, "<b>Xabaringizni kiriting:</b>", parse_mode='HTML')
            await set_user_step(user_id, 'xabar')
        else:
            await bot.send_message(user_id, "<b>Faqat raqamlardan foydalaning!</b>", parse_mode='HTML')
        return

    if step == 'xabar' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        target_id = await get_user_temp(user_id)
        if target_id:
            await bot.send_message(int(target_id), text, parse_mode='HTML')
            await bot.send_message(user_id, "<b>Xabaringiz yuborildi ✅</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        return

    # users (oddiy xabar barchaga)
    if step == 'users' and user_id == ADMIN_ID:
        users = await get_all_users()
        count = 0
        for uid in users:
            try:
                await bot.send_message(uid, text, parse_mode='HTML')
                count += 1
            except:
                pass
        await bot.send_message(user_id, f"<b>Hammaga yuborildi ✅ ({count} ta)</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')
        return

    # wallet va miqdor step lari (pul yechish)
    if step and step.startswith('wallet-'):
        wallet = step.split('-')[1]
        if text == await get_button('back'):
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_user_temp(user_id, text)  # hamyon raqami
            await bot.send_message(user_id, await get_text('solveMoney', {
                'first': first_name,
                'last': last_name,
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            }), parse_mode='HTML',
                                   reply_markup=ReplyKeyboardMarkup(
                                       keyboard=[[KeyboardButton(str(user['balance']))], [KeyboardButton(await get_button('back'))]],
                                       resize_keyboard=True
                                   ))
            await set_user_step(user_id, f'miqdor-{wallet}')
        else:
            await bot.send_message(user_id, await get_text('sendCard', {
                'first': first_name,
                'last': last_name,
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            }), parse_mode='HTML')
        return

    if step and step.startswith('miqdor-'):
        wallet = step.split('-')[1]
        if text == await get_button('back'):
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            miqdor = int(text)
            narx = int(await get_setting('narx', '3000'))
            if miqdor >= narx:
                if user['balance'] >= miqdor:
                    num = await get_user_temp(user_id)
                    accpeted = await get_text('accpeted', {
                        'first': first_name,
                        'last': last_name,
                        'id': user_id,
                        'hour': datetime.datetime.now().strftime('%H:%M'),
                        'date': datetime.datetime.now().strftime('%d.%m.%Y'),
                        'phone': num,
                        'wallet': wallet,
                        'amount': miqdor
                    })
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(await get_button('confirm'), callback_data=f'tasdiq-{wallet}-{num}-{miqdor}')],
                        [InlineKeyboardButton(await get_button('cancellation'), callback_data='bekor')]
                    ])
                    await bot.send_message(user_id, accpeted, parse_mode='HTML', reply_markup=keyboard)
                    await set_user_step(user_id, '')
                else:
                    await bot.send_message(user_id, await get_text('lowBalance', {
                        'first': first_name,
                        'last': last_name,
                        'id': user_id,
                        'hour': datetime.datetime.now().strftime('%H:%M'),
                        'date': datetime.datetime.now().strftime('%d.%m.%Y')
                    }), parse_mode='HTML')
            else:
                await bot.send_message(user_id, await get_text('solveMinimum', {
                    'first': first_name,
                    'last': last_name,
                    'id': user_id,
                    'hour': datetime.datetime.now().strftime('%H:%M'),
                    'date': datetime.datetime.now().strftime('%d.%m.%Y'),
                    'minimum': narx,
                    'currency': await get_setting('valyuta', "so'm")
                }), parse_mode='HTML')
        else:
            await bot.send_message(user_id, await get_text('solveMoney', {
                'first': first_name,
                'last': last_name,
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            }), parse_mode='HTML')
        return

# ============ FORWARD HANDLER ============
@dp.message_handler(content_types=types.ContentType.ANY, is_forwarded=True)
async def forward_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    step = await get_user_step(user_id)
    if step == 'forusers':
        users = await get_all_users()
        count = 0
        for uid in users:
            try:
                await bot.forward_message(uid, user_id, message.message_id)
                count += 1
            except:
                pass
        await bot.send_message(user_id, f"<b>Hammaga yuborildi ✅ ({count} ta)</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')

# ============ CALLBACK HANDLER ============
@dp.callback_query_handler(lambda c: True)
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    message_id = callback.message.message_id

    if data == 'yopish':
        await bot.delete_message(user_id, message_id)
        return

    if user_id == ADMIN_ID:
        # Holat
        if data == 'holat':
            valyuta = await get_setting('valyuta', "so'm")
            taklif = await get_setting('taklif', '250')
            narx = await get_setting('narx', '3000')
            admin_user = await get_setting('admin_user', 'Kiritilmagan')
            text = f"<b>Hozirgi holat:\n\n1. Valyuta:</b> {valyuta}\n<b>2. Taklif narxi:</b> {taklif} {valyuta}\n<b>3. Pul yechish narxi:</b> {narx} {valyuta}\n<b>4. Admin useri:</b> {admin_user}"
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='asosiy'))
            await bot.edit_message_text(text, user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'asosiy':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📑 Hozirgi holat", callback_data='holat')],
                [InlineKeyboardButton("🔗 Taklif narxi", callback_data='taklif'), InlineKeyboardButton("💶 Valyuta", callback_data='valyuta')],
                [InlineKeyboardButton("💵 Minimal pul yechish narxi", callback_data='narx')],
                [InlineKeyboardButton("📎 Admin useri", callback_data='admin'), InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await bot.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'taklif':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Taklif narxini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'taklifpul')
            return
        if data == 'valyuta':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Pul birligini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'valyuta')
            return
        if data == 'narx':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Minimal pul yechish narxini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'narx')
            return
        if data == 'admin':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Admin userini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'admin-user')
            return

        # Kanallar
        if data == 'majburiy':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("➕ Qo'shish", callback_data='qoshish')],
                [InlineKeyboardButton("📑 Ro'yxat", callback_data='royxat'), InlineKeyboardButton("🗑 O'chirish", callback_data='ochirish')],
                [InlineKeyboardButton("◀️ Orqaga", callback_data='kanallar')]
            ])
            await bot.edit_message_text("<b>Majburiy obunalarni sozlash bo'limidasiz:</b>", user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'qoshish':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Kanalingiz userini kiriting:\n\nNamuna:</b> @ORGBuilder", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, "qo'shish")
            return

        if data == 'ochirish':
            await clear_channels()
            await bot.edit_message_text("<b>Kanallar o'chirildi</b>", user_id, message_id, parse_mode='HTML')
            return

        if data == 'royxat':
            channels = await get_channels()
            if channels:
                soni = len(channels)
                text = "<b>📢 Kanallar ro'yxati:</b>\n\n" + "\n".join(channels) + f"\n\n<b>Ulangan kanallar soni:</b> {soni} ta"
            else:
                text = "📂 <b>Kanallar ro'yxati bo'sh!</b>"
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='majburiy'))
            await bot.edit_message_text(text, user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'kanallar':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🔐 Majburiy obunalar", callback_data='majburiy')],
                [InlineKeyboardButton("*⃣ Qo'shimcha kanallar", callback_data='qoshimcha')],
                [InlineKeyboardButton("Yopish", callback_data='yopish')]
            ])
            await bot.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'qoshimcha':
            vazifa = await get_setting('vazifa', 'Kiritilmagan')
            text = f"<b>Quyidagilardan birini tanlang:\n\nHozirgi holat:\nTo'lovlar uchun kanal:</b> {vazifa}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🆕️ To'lovlar uchun", callback_data='vazifa')],
                [InlineKeyboardButton("◀️ Orqaga", callback_data='kanallar')]
            ])
            await bot.edit_message_text(text, user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'vazifa':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Kanalingiz userini kiriting:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'vazifa')
            return

        # To'lov tizimi
        if data == 'new':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Yangi to'lov tizimi nomini yuboring:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'turi')
            return

        if data.startswith('del-'):
            name = data.split('-')[1]
            await del_pay_type(name)
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='hamyon'))
            await bot.edit_message_text(f"{name} - <b>To'lov tizimi olib tashlandi.</b>", user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        if data == 'hamyon':
            pay_types = await get_pay_types()
            if pay_types:
                keyboard = []
                for p in pay_types:
                    keyboard.append([InlineKeyboardButton(f"{p} - ni o'chirish", callback_data=f'del-{p}')])
                keyboard.append([InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')])
                await bot.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", user_id, message_id, parse_mode='HTML',
                                            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
            else:
                keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new'))
                await bot.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

        # Xabarnoma
        if data == 'send':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "*Xabaringizni kiriting:*", parse_mode='Markdown', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'users')
            return

        if data == 'forsend':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "*Xabaringizni yuboring (forward):*", parse_mode='Markdown', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'forusers')
            return

        if data == 'user':
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, "<b>Foydalanuvchi iD raqamini kiriting:</b>", parse_mode='HTML', reply_markup=await get_boshqarish())
            await set_user_step(user_id, 'user')
            return

        # Foydalanuvchini boshqarish
        if data == 'plus':
            target_id = await get_user_temp(user_id)
            if target_id:
                await bot.edit_message_text(f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobiga qancha pul qo'shmoqchisiz?</b>",
                                            user_id, message_id, parse_mode='HTML',
                                            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi')))
                await set_user_step(user_id, 'plus')
            return

        if data == 'minus':
            target_id = await get_user_temp(user_id)
            if target_id:
                await bot.edit_message_text(f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobidan qancha pul ayirmoqchisiz?</b>",
                                            user_id, message_id, parse_mode='HTML',
                                            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi')))
                await set_user_step(user_id, 'minus')
            return

        if data == 'ban':
            target_id = await get_user_temp(user_id)
            if target_id and int(target_id) != ADMIN_ID:
                user = await get_user(int(target_id))
                if user:
                    await set_ban(int(target_id), 0 if user['ban'] else 1)
                    status = "bandan olindi!" if user['ban'] else "banlandi!"
                    await bot.edit_message_text(f"<b>Foydalanuvchi ({target_id}) {status}</b>", user_id, message_id, parse_mode='HTML',
                                                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi')))
            else:
                await bot.answer_callback_query(callback.id, "Asosiy adminlarni blocklash mumkin emas!", show_alert=True)
            return

        if data == 'foydalanuvchi':
            target_id = await get_user_temp(user_id)
            if target_id:
                user = await get_user(int(target_id))
                if user:
                    bans = "🔕 Bandan olish" if user['ban'] else "🔔 Banlash"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(bans, callback_data='ban')],
                        [InlineKeyboardButton("➕ Pul qo'shish", callback_data='plus'), InlineKeyboardButton("➖ Pul ayirish", callback_data='minus')]
                    ])
                    await bot.edit_message_text(f"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id={target_id}'>{target_id}</a>\n<b>Balans: {user['balance']} {await get_setting('valyuta', 'so\'m')}\nTakliflar: {user['ref_count']} ta</b>",
                                                user_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            return

    # ===== ODDIY FOYDALANUVCHI CALLBACK =====
    if data == 'yechish':
        pay_types = await get_pay_types()
        if pay_types:
            keyboard = []
            for p in pay_types:
                keyboard.append([InlineKeyboardButton(p, callback_data=f'pay-{p}')])
            select = await get_text('selectPayType', {
                'first': callback.from_user.first_name,
                'last': callback.from_user.last_name or '',
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            })
            await bot.edit_message_text(select, user_id, message_id, parse_mode='HTML',
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        else:
            await bot.answer_callback_query(callback.id, "To'lov tizimlari topilmadi!", show_alert=True)
        return

    if data.startswith('pay-'):
        wallet = data.split('-')[1]
        vazifa = await get_setting('vazifa')
        if vazifa and vazifa != 'Kiritilmagan':
            user = await get_user(user_id)
            narx = int(await get_setting('narx', '3000'))
            if user and user['balance'] >= narx:
                await bot.delete_message(user_id, message_id)
                sendCard = await get_text('sendCard', {
                    'first': callback.from_user.first_name,
                    'last': callback.from_user.last_name or '',
                    'id': user_id,
                    'hour': datetime.datetime.now().strftime('%H:%M'),
                    'date': datetime.datetime.now().strftime('%d.%m.%Y')
                })
                await bot.send_message(user_id, sendCard, parse_mode='HTML', reply_markup=await get_back_menu())
                await set_user_step(user_id, f'wallet-{wallet}')
            else:
                minimum = await get_text('minimum', {
                    'first': callback.from_user.first_name,
                    'last': callback.from_user.last_name or '',
                    'id': user_id,
                    'hour': datetime.datetime.now().strftime('%H:%M'),
                    'date': datetime.datetime.now().strftime('%d.%m.%Y'),
                    'balance': user['balance'] if user else 0,
                    'minimum': narx,
                    'currency': await get_setting('valyuta', "so'm")
                })
                await bot.answer_callback_query(callback.id, minimum, show_alert=True)
        else:
            await bot.answer_callback_query(callback.id, "To'lovlar kanali ulanmagan!", show_alert=True)
        return

    if data == 'bekor':
        await bot.delete_message(user_id, message_id)
        await bot.send_message(user_id, await get_text('canceled', {
            'first': callback.from_user.first_name,
            'last': callback.from_user.last_name or '',
            'id': user_id,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        }), parse_mode='HTML', reply_markup=await get_main_menu(user_id))
        return

    if data.startswith('tasdiq-'):
        parts = data.split('-')
        wallet = parts[1]
        number = parts[2]
        miqdor = int(parts[3])
        user = await get_user(user_id)
        if user and user['balance'] >= miqdor:
            await sub_balance(user_id, miqdor)
            await add_solved(user_id, miqdor)
            await bot.delete_message(user_id, message_id)
            await bot.send_message(user_id, await get_text('accped', {
                'first': callback.from_user.first_name,
                'last': callback.from_user.last_name or '',
                'id': user_id,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            }), parse_mode='HTML', reply_markup=await get_main_menu(user_id))
            # Adminga
            admin_text = f"💵 <a href='tg://user?id={user_id}'>{user_id}</a> <b>pul yechib olmoqchi!</b>\n\n• <b>To'lov turi:</b> {wallet}\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqami:</b> {number}\n\nFoydalanuvchi pulini to'lab bermoqchi bo'lsangiz ✅ <b>To'landi</b> tugmasini bosing!"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🔔 Banlash", callback_data=f'block-{user_id}-{callback.from_user.first_name}')],
                [InlineKeyboardButton("✅ To'landi", callback_data=f'tolandi-{user_id}-{callback.from_user.first_name}-{number}-{miqdor}'),
                 InlineKeyboardButton("❌ To'lanmadi", callback_data=f'tolanmadi-{user_id}-{callback.from_user.first_name}-{miqdor}')]
            ])
            await bot.send_message(ADMIN_ID, admin_text, parse_mode='HTML', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await bot.answer_callback_query(callback.id, "Hisobingizda yetarli mablag' yo'q!", show_alert=True)
        return

    # Admin tomonidan to'landi, to'lanmadi, block
    if data.startswith('tolandi-'):
        parts = data.split('-')
        uid = int(parts[1])
        ism = parts[2]
        number = parts[3]
        miqdor = int(parts[4])
        advertising = await get_text('advertising', {
            'first': ism,
            'last': '',
            'id': uid,
            'username': '',
            'botname': (await bot.get_me()).username,
            'user': await get_setting('admin_user', 'Kiritilmagan'),
            'balance': (await get_user(uid))['balance'] if await get_user(uid) else 0,
            'refcount': (await get_user(uid))['ref_count'] if await get_user(uid) else 0,
            'currency': await get_setting('valyuta', "so'm"),
            'solve': (await get_user(uid))['solved'] if await get_user(uid) else 0,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        BeenPaid = await get_text('BeenPaid', {
            'first': ism,
            'id': uid,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y'),
            'phone': number,
            'amount': miqdor,
            'advertising': advertising
        })
        await bot.delete_message(user_id, message_id)
        await bot.send_message(ADMIN_ID, f"<a href='tg://user?id={uid}'>{ism}</a> <b>pullarini yechib olish haqidagi arizasi qabul qilindi.</b>", parse_mode='HTML')
        vazifa = await get_setting('vazifa')
        if vazifa and vazifa != 'Kiritilmagan':
            msg = await bot.send_message(vazifa, BeenPaid, parse_mode='HTML',
                                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🤖 Botga o'tish", url=f"https://t.me/{(await bot.get_me()).username}")))
            hasBeenPaid = await get_text('hasBeenPaid', {
                'first': ism,
                'id': uid,
                'hour': datetime.datetime.now().strftime('%H:%M'),
                'date': datetime.datetime.now().strftime('%d.%m.%Y')
            })
            kanal = vazifa.replace('@', '')
            await bot.send_message(uid, hasBeenPaid, parse_mode='HTML',
                                   reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📢 To'lovlar kanali", url=f"https://t.me/{kanal}/{msg.message_id}")))
        return

    if data.startswith('tolanmadi-'):
        parts = data.split('-')
        uid = int(parts[1])
        ism = parts[2]
        miqdor = int(parts[3])
        await add_balance(uid, miqdor)
        # solved dan ayirish kerak, lekin biz solved ni kamaytirmaymiz, chunki u faqat yig'indini ko'rsatadi
        await bot.delete_message(user_id, message_id)
        await bot.send_message(ADMIN_ID, f"<a href='tg://user?id={uid}'>{ism}</a> <b>pullarini yechib olish haqidagi arizasi qabul qilinmadi.</b>", parse_mode='HTML')
        wasNotPaid = await get_text('wasNotPaid', {
            'first': ism,
            'id': uid,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.send_message(uid, wasNotPaid, parse_mode='HTML')
        return

    if data.startswith('block-'):
        parts = data.split('-')
        uid = int(parts[1])
        ism = parts[2]
        block = await get_text('block', {
            'first': ism,
            'id': uid,
            'hour': datetime.datetime.now().strftime('%H:%M'),
            'date': datetime.datetime.now().strftime('%d.%m.%Y')
        })
        await bot.delete_message(user_id, message_id)
        await bot.send_message(ADMIN_ID, f"<a href='tg://user?id={uid}'>{ism}</a> <b>pullarini yechib olish haqidagi arizasi qabul qilinmadi va botdan blocklandi.</b>", parse_mode='HTML')
        await set_ban(uid, 1)
        await bot.send_message(uid, block, parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
        return

# ============ ISHGA TUSHIRISH ============
async def on_startup(dp):
    await init_db()
    print("Bot ishga tushdi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
