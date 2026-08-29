#!/usr/bin/env python3
import os
import io
import zipfile
import logging
import re
import unicodedata

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8245157509:AAGeQpYiyS-VWLRnJmI655TR6IDhkyFJpv8")
sessions: dict = {}


def parse_pack_name(text: str):
    for pat in [
        r"t\.me/addemoji/([A-Za-z0-9_]+)",
        r"t\.me/addstickers/([A-Za-z0-9_]+)",
        r"telegram\.me/addemoji/([A-Za-z0-9_]+)",
        r"telegram\.me/addstickers/([A-Za-z0-9_]+)",
    ]:
        m = re.search(pat, text.strip())
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_]+", text.strip()):
        return text.strip()
    return None


def emoji_to_name(ch: str) -> str:
    if not ch:
        return "emoji"
    try:
        name = unicodedata.name(ch[0], "").lower()
        return re.sub(r"[^a-z0-9]+", "_", name).strip("_")[:25] or "emoji"
    except Exception:
        return "_".join(f"u{ord(c):04x}" for c in ch[:2])


def make_keyboard(uid: int) -> InlineKeyboardMarkup:
    sess = sessions[uid]
    idx = sess["idx"]
    total = len(sess["stickers"])

    def btn(label, step):
        new_idx = idx + step
        if 0 <= new_idx < total:
            return InlineKeyboardButton(label, callback_data=f"nav:{uid}:{new_idx}")
        return InlineKeyboardButton("·", callback_data="noop")

    return InlineKeyboardMarkup([
        [btn("⬅️", -1), InlineKeyboardButton(f"#{idx+1} / {total}", callback_data="noop"), btn("➡️", +1)],
        [btn("2❯", +2), btn("4❯", +4), btn("6❯", +6), btn("8❯", +8), btn("10❯", +10)],
        [InlineKeyboardButton("🔢 Jump to #", callback_data=f"jump:{uid}", style="primary")],
        [InlineKeyboardButton("📥 Download this emoji", callback_data=f"dl1:{uid}:{idx}", style="success")],
        [InlineKeyboardButton("🆔 Get this emoji ID", callback_data=f"id1:{uid}:{idx}"), InlineKeyboardButton("📋 Get all IDs", callback_data=f"idall:{uid}")],
        [InlineKeyboardButton("📦 Download all as ZIP", callback_data=f"zip:{uid}", style="danger")],
    ])


async def send_preview(target, ctx, uid: int, edit_msg=None):
    sess = sessions[uid]
    sticker = sess["stickers"][sess["idx"]]
    ext = sess["ext"]

    tg_file = await ctx.bot.get_file(sticker.file_id)
    fb = bytes(await tg_file.download_as_bytearray())
    buf = io.BytesIO(fb)

    if ext == ".webm":
        buf.name = "emoji.webm"
        await target.reply_video(video=buf, reply_markup=make_keyboard(uid))
    elif ext == ".tgs":
        buf.name = "emoji.tgs"
        await target.reply_animation(animation=buf, reply_markup=make_keyboard(uid))
    else:
        buf.name = "emoji.webp"
        await target.reply_document(document=buf, filename="emoji.webp", reply_markup=make_keyboard(uid))

    if edit_msg:
        try:
            await edit_msg.delete()
        except Exception:
            pass


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Emoji Pack Downloader</b>\n\n"
        "📦 Send a pack link:\n"
        "<code>https://t.me/addemoji/PackName</code>\n"
        "<code>https://t.me/addstickers/PackName</code>",
        parse_mode="HTML",
    )


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = (msg.text or "").strip()
    uid = update.effective_user.id
    sess = sessions.get(uid)

    # Custom emoji ID
    custom = [e for e in (msg.entities or []) if e.type == "custom_emoji"]
    if custom:
        seen, lines = set(), []
        for e in custom:
            if e.custom_emoji_id not in seen:
                seen.add(e.custom_emoji_id)
                ch = text[e.offset:e.offset + e.length]
                lines.append(f"{ch}  <code>{e.custom_emoji_id}</code>")
        await msg.reply_text(f"✨ <b>Custom Emoji ID:</b>\n\n" + "\n".join(lines), parse_mode="HTML")
        return

    # Jump to number
    if sess and sess.get("awaiting_jump"):
        if not text.isdigit():
            await msg.reply_text("❌ Please send a number only.")
            return
        num = int(text)
        total = len(sess["stickers"])
        if not 1 <= num <= total:
            await msg.reply_text(f"❌ Enter a number between 1 and {total}.")
            return
        sess["awaiting_jump"] = False
        sess["idx"] = num - 1
        await send_preview(msg, ctx, uid)
        return

    # Pack link
    pack_name = parse_pack_name(text)
    if not pack_name:
        await msg.reply_text("❌ Invalid link.\nExample: <code>https://t.me/addemoji/PackName</code>", parse_mode="HTML")
        return

    wait = await msg.reply_text(f"🔍 Looking up <b>{pack_name}</b>...", parse_mode="HTML")
    try:
        sticker_set = await ctx.bot.get_sticker_set(pack_name)
    except Exception as e:
        logger.error(e)
        await wait.edit_text("❌ Pack not found. Check the link and try again.")
        return

    stickers = sticker_set.stickers
    s0 = stickers[0] if stickers else None
    ext = ".webm" if (s0 and s0.is_video) else ".tgs" if (s0 and s0.is_animated) else ".webp"

    sessions[uid] = {"pack_name": pack_name, "stickers": stickers, "title": sticker_set.title, "ext": ext, "idx": 0, "awaiting_jump": False}

    await wait.delete()
    await send_preview(update.message, ctx, uid)


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "noop":
        return

    if data.startswith("nav:"):
        _, uid, idx = data.split(":")
        uid, idx = int(uid), int(idx)
        if uid not in sessions:
            await query.message.reply_text("⚠️ Session expired. Send the pack link again.")
            return
        sessions[uid]["idx"] = idx
        await send_preview(query.message, ctx, uid)

    elif data.startswith("jump:"):
        _, uid = data.split(":")
        uid = int(uid)
        if uid not in sessions:
            await query.message.reply_text("⚠️ Session expired. Send the pack link again.")
            return
        sessions[uid]["awaiting_jump"] = True
        total = len(sessions[uid]["stickers"])
        await query.message.reply_text(f"🔢 Send a number from <b>1</b> to <b>{total}</b>:", parse_mode="HTML")

    elif data.startswith("dl1:"):
        _, uid, idx = data.split(":")
        uid, idx = int(uid), int(idx)
        if uid not in sessions:
            await query.message.reply_text("⚠️ Session expired.")
            return
        sess = sessions[uid]
        sticker = sess["stickers"][idx]
        wait = await query.message.reply_text("⏳ Downloading...")
        try:
            tg_file = await ctx.bot.get_file(sticker.file_id)
            fb = bytes(await tg_file.download_as_bytearray())
            buf = io.BytesIO(fb)
            buf.name = f"alpha{sess['ext']}"
            await query.message.reply_document(document=buf, filename=f"alpha{sess['ext']}")
            await wait.delete()
        except Exception as e:
            await wait.edit_text(f"❌ Error: {e}")

    elif data.startswith("zip:"):
        _, uid = data.split(":")
        uid = int(uid)
        if uid not in sessions:
            await query.message.reply_text("⚠️ Session expired. Send the pack link again.")
            return
        sess = sessions[uid]
        stickers, ext = sess["stickers"], sess["ext"]
        total = len(stickers)
        digits = len(str(total))
        msg = await query.message.reply_text(f"⏳ Building ZIP... 0/{total}")
        zip_buf = io.BytesIO()
        failed = 0
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_STORED) as zf:
            for i, s in enumerate(stickers, 1):
                try:
                    tg_file = await ctx.bot.get_file(s.file_id)
                    fb = bytes(await tg_file.download_as_bytearray())
                    zf.writestr(f"{str(i).zfill(digits)}_{emoji_to_name(s.emoji or '')}{ext}", fb)
                except Exception as e:
                    logger.warning("Sticker %d: %s", i, e)
                    failed += 1
                if i % 25 == 0 or i == total:
                    try:
                        await msg.edit_text(f"⏳ Building ZIP... {i}/{total}")
                    except Exception:
                        pass
        zip_buf.seek(0)
        size_mb = zip_buf.getbuffer().nbytes / 1_048_576
        if size_mb > 50:
            await msg.edit_text(f"❌ File too large ({size_mb:.1f} MB). Telegram limit is 50 MB.")
            return
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", sess["pack_name"])
        await msg.edit_text(f"📤 Sending ({size_mb:.1f} MB)...")
        await query.message.reply_document(
            document=zip_buf, filename=f"{safe}.zip",
            caption=f"✅ <b>{sess['title']}</b>\n📁 {total-failed}/{total} files  📦 {size_mb:.1f} MB",
            parse_mode="HTML",
        )
        await msg.delete()

    elif data.startswith("id1:"):
        _, uid, idx = data.split(":")
        uid, idx = int(uid), int(idx)
        if uid not in sessions:
            await query.message.reply_text("⚠️ Session expired. Send the pack link again.")
            return
        s = sessions[uid]["stickers"][idx]
        await query.message.reply_text(f"{s.emoji or ''}  <code>{s.custom_emoji_id or s.file_unique_id}</code>", parse_mode="HTML")

    elif data.startswith("idall:"):
        _, uid = data.split(":")
        uid = int(uid)
        if uid not in sessions:
            await query.message.reply_text("⚠️ Session expired. Send the pack link again.")
            return
        sess = sessions[uid]
        lines = [f"{i}. {s.emoji or ''} {s.custom_emoji_id or s.file_unique_id}" for i, s in enumerate(sess["stickers"], 1)]
        txt = f"{sess['title']} — {len(lines)} emojis\n\n" + "\n".join(lines)
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", sess["pack_name"])
        await query.message.reply_document(
            document=io.BytesIO(txt.encode()), filename=f"{safe}_ids.txt",
            caption=f"📋 <b>{sess['title']}</b>\n{len(lines)} emoji IDs", parse_mode="HTML",
        )


def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN is not set!\n   export BOT_TOKEN='your_token_here'")
        return
    request = HTTPXRequest(connection_pool_size=8, read_timeout=60, write_timeout=60, connect_timeout=30, pool_timeout=30)
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
