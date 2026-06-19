from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os
import sys
import io
import random
import logging
from datetime import datetime

# ============ تنظیم لاگ ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# حل مشکل یونیکد در ویندوز
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ============ توکن ربات ============
TOKEN = '8838127583:AAGRdHB1XJw0GLJkWeXRxMC7WDA0T_zuues'  # توکن خودت رو اینجا بذار

CHANNEL_USERNAME = '@AppleCatcherBotDB'

DATA_FILE = 'catcher_data.json'
PHOTOS_FILE = 'channel_photos.json'
ADMINS_FILE = 'admins.json'

# ============ مدیریت فایل‌ها ============

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_photos():
    if os.path.exists(PHOTOS_FILE):
        with open(PHOTOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_photos(photos):
    with open(PHOTOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(photos, f, ensure_ascii=False, indent=2)

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'admins': ['7927200406']}  # ادمین پیش‌فرض (آیدی خودت)

def save_admins(admins):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    admins = load_admins()
    return str(user_id) in admins.get('admins', [])

def is_owner(callback_data, user_id):
    parts = callback_data.split('_')
    if len(parts) >= 2:
        try:
            owner_id = parts[-1]
            return owner_id == str(user_id)
        except:
            return False
    return False

# ============ رتبه‌بندی ============

RANKS = {
    'S+': {'emoji': '🌟', 'name': 'طلایی ویژه', 'points': 1500},
    'S':  {'emoji': '👑', 'name': 'طلایی', 'points': 1000},
    'A':  {'emoji': '💜', 'name': 'بنفش', 'points': 600},
    'B':  {'emoji': '💙', 'name': 'آبی', 'points': 300},
    'C':  {'emoji': '💚', 'name': 'سبز', 'points': 150},
}

RANK_ORDER = {'S+': 0, 'S': 1, 'A': 2, 'B': 3, 'C': 4}

GACHA_COST = {
    'S+': 400,
    'S':  300,
    'A':  60,
    'B':  120,
    'C':  180
}

# ============ دکمه شیشه‌ای ============

def glass_button(text, callback_data, emoji=""):
    return InlineKeyboardButton(f"{emoji} {text}", callback_data=callback_data)

# ============ مدیریت همه پیام‌ها (شمارنده ۱۲۰) ============

async def handle_all_messages(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if update.message.text and update.message.text.startswith('/'):
        await handle_commands(update, context)
        return
    
    data = load_data()
    
    if user_id not in data:
        data[user_id] = {
            'score': 0,
            'coins': 0,
            'catches': 0,
            'total_catches': 0,
            'joined': str(datetime.now()),
            'name': user.first_name,
            'message_count': 0,
            'current_photo_id': None,
            'claimed_arts': []
        }
    
    data[user_id]['message_count'] = data[user_id].get('message_count', 0) + 1
    
    if data[user_id]['message_count'] >= 120:
        data[user_id]['message_count'] = 0
        
        photos = load_photos()
        if photos:
            photo = random.choice(photos)
            data[user_id]['current_photo_id'] = photo['id']
            save_data(data)
            
            caption = f"""
✨ 𝗔 𝗪𝗶𝗹𝗱 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿 𝗔𝗽𝗽𝗲𝗮𝗿𝘀 ✨
━━━━━━━━━━━━
🔍 Look closely at the video edit
🎯 Use /claim <name> to catch
━━━━━━━━━━━━
⚡ 𝗕𝗲 𝘁𝗵𝗲 𝗳𝗶𝗿𝘀𝘁 𝘁𝗼 𝗴𝘂𝗲𝘀𝘀 𝗰𝗼𝗿𝗿𝗲𝗰𝘁𝗹𝘆!
"""
            
            await update.message.reply_photo(
                photo=photo['file_id'],
                caption=caption
            )
        else:
            await update.message.reply_text("📭 ɴᴏ ᴀʀᴛꜱ ᴀᴠᴀɪʟᴀʙʟᴇ!")
    
    save_data(data)

# ======================================================================
# 🟢 دستور /claim
# ======================================================================

async def claim_command(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ **روش استفاده:**\n"
            "`/claim [اسم شخصیت]`\n\n"
            "📌 **مثال:**\n"
            "`/claim light yagami`\n"
            "`/claim naruto`"
        )
        return
    
    claim_name = ' '.join(context.args).strip().lower()
    claim_name_clean = ' '.join(claim_name.split())
    
    logger.info(f"📝 کاربر {user_id} حدس زد: '{claim_name_clean}'")
    
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ ابتدا با `/start` ربات را شروع کنید.")
        return
    
    photo_id = data[user_id].get('current_photo_id')
    
    if not photo_id:
        await update.message.reply_text(
            "❌ **هیچ آرتی برای ادعا وجود ندارد!**\n\n"
            "📌 راه‌های دریافت آرت:\n"
            "1️⃣ ارسال ۱۲۰ پیام به ربات\n"
            "2️⃣ درخواست از ادمین برای `/spawn`"
        )
        return
    
    photos = load_photos()
    photo = None
    for p in photos:
        if p['id'] == photo_id:
            photo = p
            break
    
    if not photo:
        await update.message.reply_text("❌ آرت مورد نظر در دیتابیس پیدا نشد!")
        data[user_id]['current_photo_id'] = None
        save_data(data)
        return
    
    character_name = photo['character'].lower().strip()
    character_name_clean = ' '.join(character_name.split())
    
    logger.info(f"🔍 اسم اصلی: '{character_name_clean}'")
    logger.info(f"🔍 حدس کاربر: '{claim_name_clean}'")
    
    is_match = (
        claim_name_clean == character_name_clean or
        claim_name_clean in character_name_clean or
        character_name_clean in claim_name_clean or
        claim_name_clean.replace(' ', '') == character_name_clean.replace(' ', '')
    )
    
    if is_match:
        points = photo['points']
        coins_earned = points // 2
        
        data[user_id]['score'] = data[user_id].get('score', 0) + points
        data[user_id]['coins'] = data[user_id].get('coins', 0) + coins_earned
        data[user_id]['catches'] = data[user_id].get('catches', 0) + 1
        data[user_id]['total_catches'] = data[user_id].get('total_catches', 0) + 1
        data[user_id]['current_photo_id'] = None
        
        if 'claimed_arts' not in data[user_id]:
            data[user_id]['claimed_arts'] = []
        if photo['id'] not in data[user_id]['claimed_arts']:
            data[user_id]['claimed_arts'].append(photo['id'])
        
        save_data(data)
        
        logger.info(f"✅ کاربر {user_id} با موفقیت '{character_name}' را ادعا کرد!")
        
        rank_emoji = RANKS[photo['rank']]['emoji']
        caption = f"""
✨ 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹 𝗖𝗮𝘁𝗰𝗵! ✨
━━━━━━━━━━━━━━━━━━━
🎴 {photo['character']}
🎬 {photo['anime']} • {rank_emoji} {photo['rank']}
🆔 {photo['id']}
💛 +{points} XP
⚡ +{coins_earned} NOX
━━━━━━━━━━━━━━━━━━━
"""
        
        await update.message.reply_photo(
            photo=photo['file_id'],
            caption=caption
        )
    else:
        await update.message.reply_text(
            f"""
❌ 𝗪𝗿𝗼𝗻𝗴 𝗡𝗮𝗺𝗲
━━━━━━━━━━━━━━━━━━━
𝗧𝗵𝗮𝘁'𝘀 𝗻𝗼𝘁 𝘁𝗵𝗲 𝗿𝗶𝗴𝗵𝘁 𝗻𝗮𝗺𝗲.
🔍 𝗟𝗼𝗼𝗸 𝗰𝗹𝗼𝘀𝗲𝗹𝘆 𝗮𝘁 𝘁𝗵𝗲 𝘃𝗶𝗱𝗲𝗼 𝗲𝗱𝗶𝘁 𝗮𝗻𝗱 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻!
"""
        )

# ======================================================================
# 🟢 دستور /gacha
# ======================================================================

async def gacha_command(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not context.args:
        rank_list = '\n'.join([f"{r} (هزینه {GACHA_COST[r]} NOX)" for r in GACHA_COST])
        await update.message.reply_text(
            f"❌ **روش استفاده:**\n"
            f"`/gacha [رنک]`\n\n"
            f"📌 **رنک‌های قابل انتخاب:**\n{rank_list}\n\n"
            f"مثال: `/gacha S+`"
        )
        return
    
    rank = context.args[0].upper()
    if rank == 'S+':
        rank = 'S+'
    
    if rank not in GACHA_COST:
        await update.message.reply_text(
            f"❌ رنک نامعتبر!\n"
            f"رنک‌های مجاز: {', '.join(GACHA_COST.keys())}"
        )
        return
    
    cost = GACHA_COST[rank]
    
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ ابتدا با `/start` ربات را شروع کنید.")
        return
    
    coins = data[user_id].get('coins', 0)
    
    if coins < cost:
        await update.message.reply_text(
            f"❌ **موجودی ناکافی!**\n"
            f"شما {coins} NOX دارید، اما هزینه {rank} رنک {cost} NOX است."
        )
        return
    
    photos = load_photos()
    rank_photos = [p for p in photos if p['rank'] == rank]
    
    if not rank_photos:
        await update.message.reply_text(f"❌ هیچ آرتی با رنک {rank} در دیتابیس وجود ندارد!")
        return
    
    photo = random.choice(rank_photos)
    photo_id = photo['id']
    
    claimed_arts = data[user_id].get('claimed_arts', [])
    is_duplicate = photo_id in claimed_arts
    
    data[user_id]['coins'] = coins - cost
    
    if is_duplicate:
        refund = cost // 2
        data[user_id]['coins'] += refund
        save_data(data)
        
        await update.message.reply_photo(
            photo=photo['file_id'],
            caption=f"""
⚠️ **ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴀʀᴛ!**
━━━━━━━━━━━━━━━━━━━
🎴 {photo['character']}
🎬 {photo['anime']} • {RANKS[photo['rank']]['emoji']} {photo['rank']}
🆔 {photo['id']}

شما قبلاً این آرت را داشتید!
⚡ {refund} NOX برگشت داده شد.
━━━━━━━━━━━━━━━━━━━
💰 **موجودی جدید:** {data[user_id]['coins']} NOX
"""
        )
    else:
        data[user_id]['claimed_arts'].append(photo_id)
        save_data(data)
        
        await update.message.reply_photo(
            photo=photo['file_id'],
            caption=f"""
🎉 **ɢᴀᴄʜᴀ ꜱᴜᴄᴄᴇꜱꜱ!**
━━━━━━━━━━━━━━━━━━━
🎴 {photo['character']}
🎬 {photo['anime']} • {RANKS[photo['rank']]['emoji']} {photo['rank']}
🆔 {photo['id']}

⚡ -{cost} NOX
━━━━━━━━━━━━━━━━━━━
💰 **موجودی جدید:** {data[user_id]['coins']} NOX
"""
        )

# ======================================================================
# 🟢 دستورات مدیریتی جدید (فقط ادمین)
# ======================================================================

async def remove_art_command(update, context):
    user = update.effective_user
    admin_id = str(user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ **روش استفاده:**\n"
            "`/removeart [آیدی کاربر] [شناسه آرت]`\n\n"
            "📌 **مثال:**\n"
            "`/removeart 123456789 5`\n\n"
            "برای حذف همه آرت‌های کاربر:\n"
            "`/removeart 123456789 all`"
        )
        return
    
    target_id = context.args[0]
    art_id = context.args[1]
    
    if not target_id.isdigit():
        await update.message.reply_text("❌ آیدی کاربر باید عدد باشد!")
        return
    
    data = load_data()
    
    if target_id not in data:
        await update.message.reply_text(f"❌ کاربر با آیدی `{target_id}` در دیتابیس وجود ندارد!")
        return
    
    claimed_arts = data[target_id].get('claimed_arts', [])
    
    if not claimed_arts:
        await update.message.reply_text(f"ℹ️ کاربر `{target_id}` هیچ آرتی ندارد!")
        return
    
    if art_id.lower() == 'all':
        removed_count = len(claimed_arts)
        data[target_id]['claimed_arts'] = []
        save_data(data)
        await update.message.reply_text(
            f"🗑️ **همه آرت‌های کاربر `{target_id}` حذف شد!**\n"
            f"تعداد: {removed_count} آرت"
        )
        return
    
    if not art_id.isdigit():
        await update.message.reply_text("❌ شناسه آرت باید عدد باشد یا از `all` استفاده کنید!")
        return
    
    art_id_int = int(art_id)
    
    if art_id_int not in claimed_arts:
        await update.message.reply_text(f"❌ کاربر `{target_id}` آرت با شناسه `{art_id_int}` را ندارد!")
        return
    
    data[target_id]['claimed_arts'].remove(art_id_int)
    save_data(data)
    
    await update.message.reply_text(
        f"🗑️ **آرت با شناسه `{art_id_int}` از کاربر `{target_id}` حذف شد!**"
    )

async def remove_cat_command(update, context):
    user = update.effective_user
    admin_id = str(user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ **روش استفاده:**\n"
            "`/removecat [آیدی کاربر] [مقدار]`\n\n"
            "📌 **مثال:**\n"
            "`/removecat 123456789 50`\n\n"
            "برای پاک کردن کل NOX کاربر:\n"
            "`/removecat 123456789 all`"
        )
        return
    
    target_id = context.args[0]
    amount_str = context.args[1]
    
    if not target_id.isdigit():
        await update.message.reply_text("❌ آیدی کاربر باید عدد باشد!")
        return
    
    data = load_data()
    
    if target_id not in data:
        await update.message.reply_text(f"❌ کاربر با آیدی `{target_id}` در دیتابیس وجود ندارد!")
        return
    
    current_cat = data[target_id].get('coins', 0)
    
    if amount_str.lower() == 'all':
        data[target_id]['coins'] = 0
        save_data(data)
        await update.message.reply_text(
            f"🗑️ **همه NOX کاربر `{target_id}` حذف شد!**\n"
            f"مقدار حذف شده: {current_cat} NOX"
        )
        return
    
    if not amount_str.isdigit():
        await update.message.reply_text("❌ مقدار باید عدد باشد یا از `all` استفاده کنید!")
        return
    
    amount = int(amount_str)
    
    if amount < 0:
        await update.message.reply_text("❌ مقدار باید مثبت باشد!")
        return
    
    if amount > current_cat:
        await update.message.reply_text(
            f"❌ کاربر `{target_id}` فقط {current_cat} NOX دارد!\n"
            f"شما نمی‌توانید بیش از موجودی حذف کنید."
        )
        return
    
    data[target_id]['coins'] = current_cat - amount
    save_data(data)
    
    await update.message.reply_text(
        f"🗑️ **{amount} NOX از کاربر `{target_id}` حذف شد!**\n"
        f"موجودی جدید: {data[target_id]['coins']} NOX"
    )

async def give_art_command(update, context):
    user = update.effective_user
    admin_id = str(user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ **روش استفاده:**\n"
            "`/giveart [آیدی کاربر] [شناسه آرت]`\n\n"
            "📌 **مثال:**\n"
            "`/giveart 123456789 5`\n\n"
            "برای دادن یک آرت تصادفی:\n"
            "`/giveart 123456789 random`"
        )
        return
    
    target_id = context.args[0]
    art_id_str = context.args[1]
    
    if not target_id.isdigit():
        await update.message.reply_text("❌ آیدی کاربر باید عدد باشد!")
        return
    
    data = load_data()
    
    if target_id not in data:
        await update.message.reply_text(f"❌ کاربر با آیدی `{target_id}` در دیتابیس وجود ندارد!")
        return
    
    photos = load_photos()
    
    if not photos:
        await update.message.reply_text("❌ هیچ آرتی در دیتابیس وجود ندارد!")
        return
    
    if 'claimed_arts' not in data[target_id]:
        data[target_id]['claimed_arts'] = []
    
    if art_id_str.lower() == 'random':
        weighted_photos = []
        for p in photos:
            weight = {'S+': 2, 'S': 4, 'A': 10, 'B': 20, 'C': 30}.get(p['rank'], 10)
            weighted_photos.extend([p] * weight)
        photo = random.choice(weighted_photos)
        
        if photo['id'] not in data[target_id]['claimed_arts']:
            data[target_id]['claimed_arts'].append(photo['id'])
            save_data(data)
            
            await update.message.reply_photo(
                photo=photo['file_id'],
                caption=f"""
🎁 **ᴀʀᴛ ɢɪᴠᴇɴ ʙʏ ᴀᴅᴍɪɴ!**
━━━━━━━━━━━━━━━━━━━
🎴 {photo['character']}
🎬 {photo['anime']} • {RANKS[photo['rank']]['emoji']} {photo['rank']}
🆔 {photo['id']}

👤 به کاربر `{target_id}` داده شد!
"""
            )
        else:
            for p in photos:
                if p['id'] not in data[target_id]['claimed_arts']:
                    data[target_id]['claimed_arts'].append(p['id'])
                    save_data(data)
                    await update.message.reply_photo(
                        photo=p['file_id'],
                        caption=f"""
🎁 **ᴀʀᴛ ɢɪᴠᴇɴ ʙʏ ᴀᴅᴍɪɴ!**
━━━━━━━━━━━━━━━━━━━
🎴 {p['character']}
🎬 {p['anime']} • {RANKS[p['rank']]['emoji']} {p['rank']}
🆔 {p['id']}

👤 به کاربر `{target_id}` داده شد!
"""
                    )
                    return
            await update.message.reply_text("❌ کاربر قبلاً همه آرت‌ها را دارد!")
        return
    
    if not art_id_str.isdigit():
        await update.message.reply_text("❌ شناسه آرت باید عدد باشد یا از `random` استفاده کنید!")
        return
    
    art_id = int(art_id_str)
    
    photo = None
    for p in photos:
        if p['id'] == art_id:
            photo = p
            break
    
    if not photo:
        await update.message.reply_text(f"❌ آرت با شناسه `{art_id}` در دیتابیس وجود ندارد!")
        return
    
    if art_id in data[target_id]['claimed_arts']:
        await update.message.reply_text(f"ℹ️ کاربر `{target_id}` قبلاً این آرت را دارد!")
        return
    
    data[target_id]['claimed_arts'].append(art_id)
    save_data(data)
    
    await update.message.reply_photo(
        photo=photo['file_id'],
        caption=f"""
🎁 **ᴀʀᴛ ɢɪᴠᴇɴ ʙʏ ᴀᴅᴍɪɴ!**
━━━━━━━━━━━━━━━━━━━
🎴 {photo['character']}
🎬 {photo['anime']} • {RANKS[photo['rank']]['emoji']} {photo['rank']}
🆔 {photo['id']}

👤 به کاربر `{target_id}` داده شد!
"""
    )

async def add_cat_command(update, context):
    user = update.effective_user
    admin_id = str(user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ **روش استفاده:**\n"
            "`/addcat [آیدی کاربر] [مقدار]`\n\n"
            "📌 **مثال:**\n"
            "`/addcat 123456789 50`\n\n"
            "برای اضافه کردن به خودتان:\n"
            "`/addcat me 50`"
        )
        return
    
    target = context.args[0]
    amount_str = context.args[1]
    
    if not amount_str.isdigit():
        await update.message.reply_text("❌ مقدار باید عدد باشد!")
        return
    
    amount = int(amount_str)
    
    if amount < 0:
        await update.message.reply_text("❌ مقدار باید مثبت باشد!")
        return
    
    data = load_data()
    
    if target.lower() == 'me':
        target_id = admin_id
    else:
        if not target.isdigit():
            await update.message.reply_text("❌ آیدی کاربر باید عدد باشد یا از `me` استفاده کنید!")
            return
        target_id = target
    
    if target_id not in data:
        await update.message.reply_text(f"❌ کاربر با آیدی `{target_id}` در دیتابیس وجود ندارد!")
        return
    
    data[target_id]['coins'] = data[target_id].get('coins', 0) + amount
    save_data(data)
    
    await update.message.reply_text(
        f"✅ **{amount} NOX به کاربر `{target_id}` اضافه شد!**\n"
        f"موجودی جدید: {data[target_id]['coins']} NOX"
    )

# ============ دستور /spawn ============

async def spawn_command(update, context):
    user = update.effective_user
    admin_id = str(user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن!")
        return
    
    target_id = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = str(target_user.id)
    else:
        if not context.args:
            await update.message.reply_text(
                "❌ روش‌های استفاده:\n"
                "1. روی پیام کاربر ریپلای کن و بفرست `/spawn`\n"
                "2. `/spawn @username`\n"
                "3. `/spawn 123456789`"
            )
            return
        
        target = context.args[0]
        
        if target.startswith('@'):
            try:
                chat = await context.bot.get_chat(target)
                target_id = str(chat.id)
            except Exception as e:
                await update.message.reply_text(f"❌ کاربر با نام‌کاربری `{target}` پیدا نشد!\nخطا: {e}")
                return
        elif target.isdigit():
            target_id = target
        else:
            await update.message.reply_text("❌ ورودی نامعتبر! از آیدی عددی یا نام‌کاربری با @ استفاده کن.")
            return
    
    if not target_id:
        await update.message.reply_text("❌ کاربر مورد نظر شناسایی نشد!")
        return
    
    data = load_data()
    
    if target_id not in data:
        await update.message.reply_text(f"❌ کاربر با آیدی `{target_id}` در دیتابیس وجود ندارد!\n(ابتدا باید ربات را استارت کرده باشد)")
        return
    
    photos = load_photos()
    if not photos:
        await update.message.reply_text("📭 هیچ آرتی در دیتابیس وجود ندارد!")
        return
    
    photo = random.choice(photos)
    
    data[target_id]['current_photo_id'] = photo['id']
    save_data(data)
    
    try:
        caption = f"""
✨ 𝗔 𝗪𝗶𝗹𝗱 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿 𝗔𝗽𝗽𝗲𝗮𝗿𝘀 ✨
━━━━━━━━━━━━
🔍 Look closely at the video edit
🎯 Use /claim <name> to catch
━━━━━━━━━━━━
⚡ 𝗕𝗲 𝘁𝗵𝗲 𝗳𝗶𝗿𝘀𝘁 𝘁𝗼 𝗴𝘂𝗲𝘀𝘀 𝗰𝗼𝗿𝗿𝗲𝗰𝘁𝗹𝘆!
"""
        
        await context.bot.send_photo(
            chat_id=int(target_id),
            photo=photo['file_id'],
            caption=caption
        )
        await update.message.reply_text(f"✅ آرت با شناسه {photo['id']} برای کاربر {target_id} اسپاون شد!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارسال به کاربر: {e}")

# ============ دستور /check ============

async def check_command(update, context):
    user