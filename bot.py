import os
import datetime
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ============ KONFIG ============
API_TOKEN = '8954102314:AAEVx-GpYc32S8HQWOrj-5A0R3iup09Cn68'  # Sizning tokeningiz
ADMIN_ID = 8758410535 # Sizning ID'ngiz

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

DB_PATH = 'pulbot.db'

# ============ BAZA YARATISH ============
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
        # Statistika
        await db.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        
        # Standart sozlamalar
        defaults = [
            ('taklif', '250'),
            ('valyuta', "so'm"),
            ('narx', '3000'),
            ('vazifa', 'Kiritilmagan'),
            ('admin_user', 'Kiritilmagan')
        ]
        for key, value in defaults:
            await db.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
        
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

async def get_user_temp(user_id):
    user = await get_user(user_id)
    return user['temp_data'] if user else None

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
    text = f"<b>📲 Botdan ro'yxatdan o'tish uchun quyidagi tugma orqali telefon raqamingizni yuboring:</b>"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    await bot.send_message(user_id, text, parse_mode='HTML', reply_markup=keyboard)
    return False

# ============ MENU YARATISH ============
async def get_main_menu(user_id):
    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton("💵 Pul ishlash")],
            [KeyboardButton("💰 Hisobim"), KeyboardButton("🏦 Pulni yechish")],
            [KeyboardButton("📢 To'lovlar kanali")],
            [KeyboardButton("📨 Murojaat"), KeyboardButton("📚 Qo'llanma")],
            [KeyboardButton("🗄 Boshqarish")]
        ]
    else:
        keyboard = [
            [KeyboardButton("💵 Pul ishlash")],
            [KeyboardButton("💰 Hisobim"), KeyboardButton("🏦 Pulni yechish")],
            [KeyboardButton("📢 To'lovlar kanali")],
            [KeyboardButton("📨 Murojaat"), KeyboardButton("📚 Qo'llanma")]
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def get_back_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("◀️ Orqaga")]],
        resize_keyboard=True
    )

async def get_panel_menu():
    orqa = "◀️ Orqaga"
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

# ============ /start HANDLER ============
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
            taklif = int(await get_setting('taklif', '250'))
            await add_balance(ref_id, taklif)
            await inc_ref(ref_id)
            await bot.send_message(ref_id, f"<b>📳 Sizda yangi taklif mavjud!</b>", parse_mode='HTML')
    
    if not await joinchat(user_id):
        return
    
    await bot.send_message(
        user_id,
        f"<b>🖥 Asosiy menyudasiz.</b>",
        parse_mode='HTML',
        reply_markup=await get_main_menu(user_id)
    )

# ============ KONTAKT HANDLER ============
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
        await bot.send_message(
            user_id,
            f"<b>✅ Telefon raqamingiz qabul qilindi:</b> {phone}\n\n<i>Botdan foydalanish boshlash uchun quyidagi tugmani bosing:</i>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Davom etish", callback_data='davom'))
        )
    else:
        await set_ban(user_id, 1)
        await set_user_step(user_id, '')
        await bot.send_message(
            user_id,
            "<b>Kechirasiz, Botdan faqat O'zbekiston fuqarolari foydalanishi mumkin.</b>",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )

# ============ "davom" CALLBACK ============
@dp.callback_query_handler(lambda c: c.data == 'davom')
async def davom_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await bot.delete_message(user_id, callback.message.message_id)
    await bot.send_message(
        user_id,
        "<b>🖥 Asosiy menyudasiz.</b>",
        parse_mode='HTML',
        reply_markup=await get_main_menu(user_id)
    )

# ============ "check" CALLBACK ============
@dp.callback_query_handler(lambda c: c.data == 'check')
async def check_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await bot.delete_message(user_id, callback.message.message_id)
    if await joinchat(user_id):
        await bot.send_message(
            user_id,
            "<b>🖥 Asosiy menyudasiz.</b>",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )

# ============ MATNLI XABAR HANDLER ============
@dp.message_handler(content_types=types.ContentType.TEXT)
async def text_handler(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ''
    
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
    if text == "◀️ Orqaga":
        await set_user_step(user_id, '')
        await bot.send_message(
            user_id,
            "<b>🖥 Asosiy menyuga qaytdingiz.</b>",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )
        return
    
    # ===== PUL ISHLASH =====
    if text == "💵 Pul ishlash":
        reflink = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
        caption = f"<b>🔗 Sizning taklif havolangiz:</b>\n\n{reflink}\n\n<i>Yuqoridagi taklif havolangizni do'stlaringizga tarqating va har bir to'liq ro'yxatdan o'tgan taklifingiz uchun 250 so'm hisobingizga qo'shiladi.</i>"
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("↗️ Ulashish", url=f"https://t.me/share/url?url={reflink}"))
        await bot.send_message(user_id, caption, parse_mode='HTML', reply_markup=keyboard)
        return
    
    # ===== HISOBIM =====
    if text == "💰 Hisobim":
        valyuta = await get_setting('valyuta', "so'm")
        text_cab = f"<b>🔑 Sizning ID raqamingiz:</b> <pre>{user_id}</pre>\n\n💵 <b>Asosiy balansingiz:</b> {user['balance']} {valyuta}\n👤 <b>Takliflaringiz soni:</b> {user['ref_count']} ta\n\n💳 <b>Yechib olgan pullaringiz:</b> {user['solved']} {valyuta}"
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🏦 Pulni yechish", callback_data='yechish'))
        await bot.send_message(user_id, text_cab, parse_mode='HTML', reply_markup=keyboard)
        return
    
    # ===== PULNI YECHISH =====
    if text == "🏦 Pulni yechish":
        pay_types = await get_pay_types()
        if pay_types:
            keyboard = []
            for p in pay_types:
                keyboard.append([InlineKeyboardButton(p, callback_data=f'pay-{p}')])
            await bot.send_message(
                user_id,
                "👇 <b>Quyidagi to'lov tizimlaridan birini tanlang:</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            await bot.send_message(user_id, "<b>To'lov tizimlari topilmadi!</b>", parse_mode='HTML')
        return
    
    # ===== TO'LOVLAR KANALI =====
    if text == "📢 To'lovlar kanali":
        vazifa = await get_setting('vazifa')
        if vazifa and vazifa != 'Kiritilmagan':
            kanal = vazifa.replace('@', '')
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 To'lovlar kanali", url=f"https://t.me/{kanal}"))
            await bot.send_message(
                user_id,
                "<b>⤵️ Quyidagi kanal orqali to'lovlarni kuzatib boring:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await bot.send_message(user_id, "<b>To'lovlar kanali kiritilmagan!</b>", parse_mode='HTML')
        return
    
    # ===== QO'LLANMA =====
    if text == "📚 Qo'llanma":
        await bot.send_message(
            user_id,
            "<b>📚 Qo'llanma mavjud emas!</b>",
            parse_mode='HTML'
        )
        return
    
    # ===== MUROJAAT =====
    if text == "📨 Murojaat":
        await bot.send_message(
            user_id,
            "📝 <b>Murojaat matnini yuboring:</b>",
            parse_mode='HTML',
            reply_markup=await get_back_menu()
        )
        await set_user_step(user_id, 'yordam')
        return
    
    # ===== MUROJAAT MATNI =====
    if step == 'yordam':
        await bot.send_message(
            ADMIN_ID,
            f"<a href='tg://user?id={user_id}'>{user_id}</a> <b>dan yangi xabar:</b> {text}",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        await bot.send_message(
            user_id,
            "✅ <b>Murojaatingiz yuborildi.</b>\n\nTez orada javob qaytaramiz!",
            parse_mode='HTML',
            reply_markup=await get_main_menu(user_id)
        )
        await set_user_step(user_id, '')
        return
    
    # ===== ADMIN PANEL =====
    if user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await bot.send_message(
                user_id,
                "<b>Boshqaruv panelidasiz.</b>",
                parse_mode='HTML',
                reply_markup=await get_panel_menu()
            )
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
            await bot.send_message(
                user_id,
                f"<b>👥 Foydalanuvchilar: {count} ta</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Yopish", callback_data='yopish'))
            )
            return
        
        if text == "🔎 Foydalanuvchini boshqarish":
            await bot.send_message(
                user_id,
                "<b>Kerakli foydalanuvchining ID raqamini kiriting:</b>",
                parse_mode='HTML',
                reply_markup=await get_boshqarish()
            )
            await set_user_step(user_id, 'iD')
            return
        
        if text == "🎛 Tugmalar":
            await bot.send_message(
                user_id,
                "<b>Tugmalar sozlamasi mavjud emas!</b>",
                parse_mode='HTML'
            )
            return
        
        if text == "📃 Matnlar":
            await bot.send_message(
                user_id,
                "<b>Matnlar sozlamasi mavjud emas!</b>",
                parse_mode='HTML'
            )
            return
        
        if text == "💳 To'lov tizimi":
            pay_types = await get_pay_types()
            if pay_types:
                keyboard = []
                for p in pay_types:
                    keyboard.append([InlineKeyboardButton(f"{p} - ni o'chirish", callback_data=f'del-{p}')])
                keyboard.append([InlineKeyboardButton("➕ To'lov tizimi qo'shish", callback_data='new')])
                await bot.send_message(
                    user_id,
                    "<b>Quyidagilardan birini tanlang:</b>",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
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
    
    # ===== STEP BO'YICHA =====
    # iD (foydalanuvchi qidirish)
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
            await bot.send_message(
                user_id,
                f"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id={text}'>{text}</a>\n<b>Balans: {target['balance']} {await get_setting('valyuta', 'so\'m')}\nTakliflar: {target['ref_count']} ta</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Foydalanuvchi topilmadi.\n\nQayta urinib ko'ring:</b>", parse_mode='HTML')
        return
    
    # qo'shish (majburiy kanal)
    if step == "qo'shish" and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if '@' in text:
            await add_channel(text)
            await bot.send_message(user_id, f"<b>{text} - kanal qo'shildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
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
            await set_setting('vazifa', text)
            await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "⚠️ <b>Kanal manzili kiritishda xatolik!\n\nQayta urinib ko'ring:</b>", parse_mode='HTML')
        return
    
    # turi (to'lov tizimi qo'shish)
    if step == 'turi' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await add_pay_type(text)
        await bot.send_message(user_id, "<b>Yangi to'lov tizimi qo'shildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')
        return
    
    # taklifpul, valyuta, narx, admin-user
    if step == 'taklifpul' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_setting('taklif', text)
            await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Faqat raqam kiriting!</b>", parse_mode='HTML')
        return
    
    if step == 'valyuta' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await set_setting('valyuta', text)
        await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
        await set_user_step(user_id, '')
        return
    
    if step == 'narx' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_setting('narx', text)
            await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
            await set_user_step(user_id, '')
        else:
            await bot.send_message(user_id, "<b>Faqat raqam kiriting!</b>", parse_mode='HTML')
        return
    
    if step == 'admin-user' and user_id == ADMIN_ID:
        if text == "🗄 Boshqarish":
            await set_user_step(user_id, '')
            return
        await set_setting('admin_user', text)
        await bot.send_message(user_id, "<b>Muvaffaqiyatli o'zgartirildi!</b>", parse_mode='HTML', reply_markup=await get_panel_menu())
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
    
    # wallet
    if step and step.startswith('wallet-'):
        wallet = step.split('-')[1]
        if text == "◀️ Orqaga":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            await set_user_temp(user_id, text)
            await bot.send_message(
                user_id,
                f"<b>Qancha miqdorda pul yechib olmoqchisiz:</b>",
                parse_mode='HTML',
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(str(user['balance']))], [KeyboardButton("◀️ Orqaga")]],
                    resize_keyboard=True
                )
            )
            await set_user_step(user_id, f'miqdor-{wallet}')
        else:
            await bot.send_message(
                user_id,
                "<b>Hamyoningiz raqamini yuboring:</b>",
                parse_mode='HTML'
            )
        return
    
    # miqdor
    if step and step.startswith('miqdor-'):
        wallet = step.split('-')[1]
        if text == "◀️ Orqaga":
            await set_user_step(user_id, '')
            return
        if text.isdigit():
            miqdor = int(text)
            narx = int(await get_setting('narx', '3000'))
            if miqdor >= narx:
                if user['balance'] >= miqdor:
                    num = await get_user_temp(user_id)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f'tasdiq-{wallet}-{num}-{miqdor}')],
                        [InlineKeyboardButton("🚫 Bekor qilish", callback_data='bekor')]
                    ])
                    await bot.send_message(
                        user_id,
                        f"✅ <b>Qabul qilindi!</b>\n\n• <b>To'lov turi:</b> {wallet}\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqamingiz:</b> {num}\n\n<b>Ma'lumotlar to'g'ri ekanligiga ishonch hosil qilgan bo'lsangiz, ✅ Tasdiqlash tugmasini bosing!</b>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                    await set_user_step(user_id, '')
                else:
                    await bot.send_message(
                        user_id,
                        "<b>Hisobingizda yetarli mablag' mavjud emas!</b>\n\nQayta urunib ko'ring:",
                        parse_mode='HTML'
                    )
            else:
                await bot.send_message(
                    user_id,
                    f"<b>Minimal yechib olish miqdori:</b> {narx} {await get_setting('valyuta', 'so\'m')}\n\nQayta urunib ko'ring:",
                    parse_mode='HTML'
                )
        else:
            await bot.send_message(
                user_id,
                f"<b>Qancha miqdorda pul yechib olmoqchisiz:</b>",
                parse_mode='HTML'
            )
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
    
    # ===== ADMIN CALLBACKLAR =====
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
                text = "<b>📢 Kanallar ro'yxati:</b>\n\n" + "\n".join(channels) + f"\n\n<b>Ulangan kanallar soni:</b> {len(channels)} ta"
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
                await bot.edit_message_text("<b>Quyidagilardan birini tanlang:</b>", user_id, message_id, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
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
        
        # Foydalanuvchi boshqarish
        if data == 'plus':
            target_id = await get_user_temp(user_id)
            if target_id:
                await bot.edit_message_text(
                    f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobiga qancha pul qo'shmoqchisiz?</b>",
                    user_id, message_id, parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi'))
                )
                await set_user_step(user_id, 'plus')
            return
        
        if data == 'minus':
            target_id = await get_user_temp(user_id)
            if target_id:
                await bot.edit_message_text(
                    f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobidan qancha pul ayirmoqchisiz?</b>",
                    user_id, message_id, parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi'))
                )
                await set_user_step(user_id, 'minus')
            return
        
        if data == 'ban':
            target_id = await get_user_temp(user_id)
            if target_id and int(target_id) != ADMIN_ID:
                user = await get_user(int(target_id))
                if user:
                    await set_ban(int(target_id), 0 if user['ban'] else 1)
                    status = "bandan olindi!" if user['ban'] else "banlandi!"
                    await bot.edit_message_text(
                        f"<b>Foydalanuvchi ({target_id}) {status}</b>",
                        user_id, message_id, parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Orqaga", callback_data='foydalanuvchi'))
                    )
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
                    await bot.edit_message_text(
                        f"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id={target_id}'>{target_id}</a>\n<b>Balans: {user['balance']} {await get_setting('valyuta', 'so\'m')}\nTakliflar: {user['ref_count']} ta</b>",
                        user_id, message_id, parse_mode='HTML', reply_markup=keyboard
                    )
            return
    
    # ===== ODDIY FOYDALANUVCHI CALLBACK =====
    if data == 'yechish':
        pay_types = await get_pay_types()
        if pay_types:
            keyboard = []
            for p in pay_types:
                keyboard.append([InlineKeyboardButton(p, callback_data=f'pay-{p}')])
            await bot.edit_message_text(
                "👇 <b>Quyidagi to'lov tizimlaridan birini tanlang:</b>",
                user_id, message_id, parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
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
                await bot.send_message(
                    user_id,
                    "<b>Hamyoningiz raqamini yuboring:</b>",
                    parse_mode='HTML',
                    reply_markup=await get_back_menu()
                )
                await set_user_step(user_id, f'wallet-{wallet}')
            else:
                await bot.answer_callback_query(
                    callback.id,
                    f"⛔ Jarayonni davom ettira olmaysiz!\n\nMinimal yechib olish miqdori: {narx} {await get_setting('valyuta', 'so\'m')}",
                    show_alert=True
                )
        else:
            await bot.answer_callback_query(callback.id, "To'lovlar kanali ulanmagan!", show_alert=True)
        return
    
    if data == 'bekor':
        await bot.delete_message(user_id, message_id)
        await bot.send_message(
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
        user = await get_user(user_id)
        if user and user['balance'] >= miqdor:
            await sub_balance(user_id, miqdor)
            await add_solved(user_id, miqdor)
            await bot.delete_message(user_id, message_id)
            await bot.send_message(
                user_id,
                "✅ <b>Qabul qilindi.</b>",
                parse_mode='HTML',
                reply_markup=await get_main_menu(user_id)
            )
            # Adminga xabar
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🔔 Banlash", callback_data=f'block-{user_id}')],
                [InlineKeyboardButton("✅ To'landi", callback_data=f'tolandi-{user_id}-{number}-{miqdor}'),
                 InlineKeyboardButton("❌ To'lanmadi", callback_data=f'tolanmadi-{user_id}-{miqdor}')]
            ])
            await bot.send_message(
                ADMIN_ID,
                f"💵 <a href='tg://user?id={user_id}'>{user_id}</a> <b>pul yechib olmoqchi!</b>\n\n• <b>To'lov turi:</b> {wallet}\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqami:</b> {number}",
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
        else:
            await bot.answer_callback_query(callback.id, "Hisobingizda yetarli mablag' yo'q!", show_alert=True)
        return
    
    # Admin tomonidan to'landi
    if data.startswith('tolandi-'):
        parts = data.split('-')
        uid = int(parts[1])
        number = parts[2]
        miqdor = int(parts[3])
        await bot.delete_message(user_id, message_id)
        await bot.send_message(
            uid,
            f"<b>Hurmatli foydalanuvchi!\n\nPullaringizni yechib olish haqidagi arizangiz qabul qilindi.</b>",
            parse_mode='HTML'
        )
        await bot.send_message(
            ADMIN_ID,
            f"<b>✅ Foydalanuvchi puli to'lab berildi.</b>\n\n• <b>Pul miqdori:</b> {miqdor}\n• <b>Hamyon raqami:</b> {number}",
            parse_mode='HTML'
        )
        return
    
    if data.startswith('tolanmadi-'):
        parts = data.split('-')
        uid = int(parts[1])
        miqdor = int(parts[2])
        await add_balance(uid, miqdor)
        await bot.delete_message(user_id, message_id)
        await bot.send_message(
            uid,
            f"<b>Hurmatli foydalanuvchi!\n\nPullaringizni yechib olish haqidagi arizangiz qabul qilinmadi.</b>",
            parse_mode='HTML'
        )
        await bot.send_message(
            ADMIN_ID,
            f"<b>❌ Foydalanuvchi arizasi bekor qilindi.</b>",
            parse_mode='HTML'
        )
        return
    
    if data.startswith('block-'):
        uid = int(data.split('-')[1])
        await set_ban(uid, 1)
        await bot.delete_message(user_id, message_id)
        await bot.send_message(
            uid,
            f"<b>Hurmatli foydalanuvchi!\n\nPullaringizni yechib olish haqidagi arizangiz qabul qilinmadi va botdan blocklandingiz.</b>",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )
        await bot.send_message(
            ADMIN_ID,
            f"<b>🔔 Foydalanuvchi blocklandi.</b>",
            parse_mode='HTML'
        )
        return

# ============ ISHGA TUSHIRISH ============
async def on_startup(dp):
    await init_db()
    print(f"✅ Bot ishga tushdi! @{(await bot.get_me()).username}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
