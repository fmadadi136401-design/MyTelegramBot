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

# ============ توکن ربات (جایگزین شده) ============
TOKEN = '8838127583:AAG1ArgaOEKoVE8K0Tc_kL4_yveZX9g-UbI'

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
    return {'admins': ['7927200406']}

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
# 🟢 دستورات مدیریتی (فقط ادمین)
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
    user = update.effective_user
    admin_id = str(user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند از این دستور استفاده کنند!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **روش استفاده:**\n"
            "`/check [آیدی کاربر]`\n\n"
            "📌 **مثال:**\n"
            "`/check 123456789`"
        )
        return
    
    target_id = context.args[0]
    
    if not target_id.isdigit():
        await update.message.reply_text("❌ لطفاً یک آیدی عددی وارد کنید!")
        return
    
    data = load_data()
    
    if target_id not in data:
        await update.message.reply_text(f"❌ کاربر با آیدی `{target_id}` در دیتابیس وجود ندارد!")
        return
    
    photo_id = data[target_id].get('current_photo_id')
    claimed_ids = data[target_id].get('claimed_arts', [])
    
    text = f"""
📋 **اطلاعات کاربر `{target_id}`**

👤 نام: {data[target_id].get('name', 'ناشناس')}
⭐ XP: {data[target_id].get('score', 0)}
⚡ NOX: {data[target_id].get('coins', 0)}
🎯 شکارها: {data[target_id].get('catches', 0)}
🏠 حرمسرا: {len(claimed_ids)} آرت

🔍 آرت فعلی برای ادعا:
"""
    
    if photo_id:
        photos = load_photos()
        photo = None
        for p in photos:
            if p['id'] == photo_id:
                photo = p
                break
        if photo:
            text += f"""
   🆔 شناسه: {photo['id']}
   🎬 انیمه: {photo['anime']}
   👤 شخصیت: `{photo['character']}`
   🏅 رتبه: {RANKS[photo['rank']]['emoji']} {photo['rank']}
   ⭐ امتیاز: {photo['points']}
"""
        else:
            text += "   ❌ آرت پیدا نشد!\n"
    else:
        text += "   ❌ هیچ آرتی برای ادعا ندارد.\n"
    
    if claimed_ids:
        text += f"\n📚 **آرت‌های کاربر:**\n"
        photos = load_photos()
        for pid in claimed_ids[:10]:
            for p in photos:
                if p['id'] == pid:
                    text += f"   🆔 {pid}: {p['character']} ({p['rank']})\n"
                    break
        if len(claimed_ids) > 10:
            text += f"   ... و {len(claimed_ids) - 10} آرت دیگر\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ============ دستور /harem ============

async def harem_command(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text(
            "❌ شما هنوز هیچ آرتی شکار نکرده‌اید!\n"
            "ابتدا با `/start` ربات را شروع کنید و سپس آرت‌ها را شکار کنید."
        )
        return
    
    claimed_ids = data[user_id].get('claimed_arts', [])
    
    if not claimed_ids:
        await update.message.reply_text(
            "🏠 **ɴᴏ ᴀʀᴛꜱ ɪɴ ʏᴏᴜʀ ʜᴀʀᴇᴍ ʏᴇᴛ!**\n\n"
            "📌 برای اضافه کردن آرت به حرمسرا:\n"
            "1️⃣ ارسال ۱۲۰ پیام به ربات\n"
            "2️⃣ ادعا با `/claim [اسم]`\n"
            "3️⃣ استفاده از `/gacha` برای شانس گرفتن"
        )
        return
    
    photos = load_photos()
    
    claimed_arts = []
    for pid in claimed_ids:
        for p in photos:
            if p['id'] == pid:
                claimed_arts.append(p)
                break
    
    if not claimed_arts:
        await update.message.reply_text("❌ خطا در بازیابی آرت‌های شکار شده!")
        return
    
    claimed_arts.sort(key=lambda x: RANK_ORDER.get(x['rank'], 10))
    
    total_points = sum(p['points'] for p in claimed_arts)
    total_coins = sum(p['points'] // 2 for p in claimed_arts)
    
    text = f"""
╔══════════════════════════════════╗
║     🏠 **ʏᴏᴜʀ ʜᴀʀᴇᴍ**             ║
║     ✨ **ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴀʀᴛꜱ**          ║
╚══════════════════════════════════╝

📊 **ᴛᴏᴛᴀʟ ᴀʀᴛꜱ:** {len(claimed_arts)}
⭐ **ᴛᴏᴛᴀʟ XP:** {total_points}
⚡ **ᴛᴏᴛᴀʟ NOX:** {total_coins}

━━━━━━━━━━━━━━━━━━━━━
"""
    
    for i, art in enumerate(claimed_arts, 1):
        rank_emoji = RANKS[art['rank']]['emoji']
        text += f"""
{i}. {rank_emoji} **{art['character']}**
   🎬 {art['anime']}
   🏅 {art['rank']} ({RANKS[art['rank']]['name']})
   ⭐ {art['points']} XP
"""
    
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await update.message.reply_text(part, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')

# ============ دستور /wallet ============

async def wallet_command(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text(
            "❌ شما هنوز در دیتابیس ثبت نشده‌اید!\n"
            "ابتدا با `/start` ربات را شروع کنید."
        )
        return
    
    score = data[user_id].get('score', 0)
    coins = data[user_id].get('coins', 0)
    catches = data[user_id].get('catches', 0)
    claimed_arts = data[user_id].get('claimed_arts', [])
    
    text = f"""
╔══════════════════════════════════╗
║     💰 **ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ**             ║
╚══════════════════════════════════╝

👤 **ᴜꜱᴇʀ:** {data[user_id].get('name', user.first_name)}

⭐ **XP:** {score}
⚡ **NOX:** {coins}
🎯 **ᴄᴀᴛᴄʜᴇꜱ:** {catches}
🏠 **ʜᴀʀᴇᴍ:** {len(claimed_arts)} ᴀʀᴛꜱ

━━━━━━━━━━━━━━━━━━━━━
💡 هر شکار = XP + NOX
⚡ هر ۱ NOX = ½ امتیاز XP
🎲 با `/gacha` شانس بگیر!
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ============ دستور آپلود (فقط ادمین) ============

async def upload_command(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌تونن آپلود کنن!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ روی عکس ریپلای کن!\n"
            "مثال: /upload light yagami / death note / S+"
        )
        return
    
    if not update.message.reply_to_message.photo:
        await update.message.reply_text("❌ روی یک عکس ریپلای کن!")
        return
    
    text = update.message.text
    parts = text.split(' / ')
    
    if len(parts) < 3:
        await update.message.reply_text(
            "❌ فرمت: /upload [اسم شخصیت] / [نام انیمه] / [رتبه]\n"
            "مثال: /upload light yagami / death note / S+"
        )
        return
    
    try:
        character = parts[0].replace('/upload', '').strip()
        anime = parts[1].strip()
        rank_value = parts[2].strip().upper()
        if rank_value == 'S+':
            rank_value = 'S+'
        
        if rank_value not in RANKS:
            await update.message.reply_text(f"❌ رتبه نامعتبر! {', '.join(RANKS.keys())}")
            return
        
        photo = update.message.reply_to_message.photo[-1]
        file_id = photo.file_id
        
        photo_data = {
            'id': len(load_photos()) + 1,
            'file_id': file_id,
            'character': character,
            'anime': anime,
            'rank': rank_value,
            'points': RANKS[rank_value]['points'],
            'uploader': user_id,
            'uploader_name': user.first_name,
            'date': str(datetime.now())
        }
        
        photos = load_photos()
        photos.append(photo_data)
        save_photos(photos)
        
        try:
            caption = f"""
{random.choice(['✨', '🌟', '💫', '⭐', '🔥', '⚡', '🎯', '🎨', '🖼️', '📸'])} **ᴀ ɴᴇᴡ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴀᴘᴘᴇᴀʀᴇᴅ!**

🎬 **ᴀɴɪᴍᴇ:** {anime}
👤 **ᴄʜᴀʀᴀᴄᴛᴇʀ:** {character}
🏅 **ʀᴀɴᴋ:** {RANKS[rank_value]['emoji']} {rank_value} ({RANKS[rank_value]['name']})
⭐ **ᴘᴏɪɴᴛꜱ:** {RANKS[rank_value]['points']}
🆔 **ɪᴅ:** {photo_data['id']}

━━━━━━━━━━━━━━━━━━━━━
{random.choice(['👾', '🎭', '🎪', '🌀', '🌊', '🔥', '⚡', '💎', '👑', '🌟'])} ᴛʜᴇ ɢᴀᴛᴇ ᴡᴀꜱ ꜱᴘᴀᴡɴᴇᴅ!!

ᴀᴅᴅ ᴛʜɪꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ʏᴏᴜʀ ᴀʀᴍʏ
ʙʏ ꜱᴇɴᴅɪɴɢ `/claim [ɴᴀᴍᴇ]`
━━━━━━━━━━━━━━━━━━━━━

👤 **ᴜᴘʟᴏᴀᴅᴇʀ:** {user.first_name}
"""
            
            await context.bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=file_id,
                caption=caption,
                parse_mode='Markdown'
            )
            await update.message.reply_text(f"✅ عکس آپلود شد! (ID: {photo_data['id']})")
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال به کانال: {e}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

# ============ دستورات مدیریتی اصلی ============

async def add_admin(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ مثال: /addadmin 123456789")
        return
    
    target = context.args[0]
    admins = load_admins()
    
    if target not in admins['admins']:
        admins['admins'].append(target)
        save_admins(admins)
        await update.message.reply_text(f"✅ کاربر {target} به ادمین‌ها اضافه شد!")
    else:
        await update.message.reply_text(f"ℹ️ کاربر {target} قبلاً ادمین است!")

async def remove_admin(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ مثال: /removeadmin 123456789")
        return
    
    target = context.args[0]
    admins = load_admins()
    
    if target in admins['admins']:
        admins['admins'].remove(target)
        save_admins(admins)
        await update.message.reply_text(f"✅ کاربر {target} از ادمین‌ها حذف شد!")
    else:
        await update.message.reply_text(f"ℹ️ کاربر {target} ادمین نیست!")

async def list_admins(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید!")
        return
    
    admins = load_admins()
    
    if not admins['admins']:
        await update.message.reply_text("📭 لیست ادمین‌ها خالی است!")
        return
    
    text = "👑 **لیست ادمین‌ها:**\n\n"
    for i, admin_id in enumerate(admins['admins'], 1):
        text += f"{i}. `{admin_id}`\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def delete_photo(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ فقط ادمین‌ها می‌تونن عکس حذف کنن!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ مثال: /delphoto 5")
        return
    
    try:
        photo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ شناسه باید عدد باشد!")
        return
    
    photos = load_photos()
    photo_to_delete = None
    
    for p in photos:
        if p['id'] == photo_id:
            photo_to_delete = p
            break
    
    if not photo_to_delete:
        await update.message.reply_text(f"❌ عکس با شناسه {photo_id} پیدا نشد!")
        return
    
    photos.remove(photo_to_delete)
    save_photos(photos)
    
    await update.message.reply_text(f"🗑️ عکس با شناسه {photo_id} حذف شد!")

# ============ شروع ============

async def start(update, context):
    user = update.effective_user
    user_id = str(user.id)
    
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
        save_data(data)
    
    keyboard = [
        [glass_button("🖼️ ᴠɪᴇᴡ ᴀʀᴛꜱ", f'view_arts_{user_id}', "🎨")],
        [glass_button("💰 ᴡᴀʟʟᴇᴛ", f'wallet_{user_id}', "💳")],
        [glass_button("🎲 ɢᴀᴄʜᴀ", f'gacha_{user_id}', "🎰")],
        [glass_button("🏆 ʀᴀɴᴋɪɴɢꜱ", 'rankings', "👑")],
        [glass_button("🏠 ʜᴀʀᴇᴍ", f'harem_{user_id}', "💖")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photos = load_photos()
    
    await update.message.reply_text(
        f"""
╔══════════════════════════════════╗
║     🎌 **ʀᴏʙᴀᴛ ᴄᴀᴛᴄʜᴇʀ**        ║
║     ✨ **ᴄʟᴀɪᴍ & ɢᴀᴄʜᴀ**          ║
╚══════════════════════════════════╝

🎯 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴀᴛᴄʜᴇʀ ʙᴏᴛ!**

📝 ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴀʀᴛꜱ!
🎁 ᴀꜰᴛᴇʀ **𝟷𝟸𝟶 ᴍᴇꜱꜱᴀɢᴇꜱ**, ᴀɴ ᴀʀᴛ ᴡɪʟʟ ᴀᴘᴘᴇᴀʀ!
📝 ᴜꜱᴇ `/claim [ɴᴀᴍᴇ]` ᴛᴏ ᴄʟᴀɪᴍ ɪᴛ!
🎲 ᴜꜱᴇ `/gacha [S+/S/A/B/C]` ᴛᴏ ᴛʀʏ ʏᴏᴜʀ ʟᴜᴄᴋ!

─────────────────────────────

🏅 **رنک‌ها به ترتیب:**
🌟 S+ → 👑 S → 💜 A → 💙 B → 💚 C

📸 **ᴛᴏᴛᴀʟ ᴀʀᴛꜱ:** {len(photos)}
👤 **ᴜꜱᴇʀ:** {user.first_name}
⭐ **XP:** {data[user_id].get('score', 0)}
⚡ **NOX:** {data[user_id].get('coins', 0)}
📊 **ᴍᴇꜱꜱᴀɢᴇꜱ:** {data[user_id].get('message_count', 0)}/120
🏠 **ʜᴀʀᴇᴍ:** {len(data[user_id].get('claimed_arts', []))} ᴀʀᴛꜱ

🔮 **ᴘʀᴇꜱꜱ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ꜱᴛᴀʀᴛ!**
""",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ============ منوها ============

async def view_arts(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    callback_data = query.data
    
    if not is_owner(callback_data, user_id):
        await query.answer("❌ ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ʏᴏᴜʀꜱ!", show_alert=True)
        return
    
    await query.answer()
    
    photos = load_photos()
    
    if not photos:
        await query.edit_message_text("📭 ɴᴏ ᴀʀᴛꜱ ᴀᴠᴀɪʟᴀʙʟᴇ!")
        return
    
    text = "🖼️ **ʟɪꜱᴛ ᴏꜰ ᴀʀᴛꜱ:**\n\n"
    for p in photos[:20]:
        text += f"🆔 {p['id']}: ❓❓❓ ({p['rank']})\n"
    if len(photos) > 20:
        text += f"\n... ᴀɴᴅ {len(photos) - 20} ᴍᴏʀᴇ"
    
    keyboard = [
        [glass_button("🏠 ʙᴀᴄᴋ", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def wallet_button(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    callback_data = query.data
    
    if not is_owner(callback_data, user_id):
        await query.answer("❌ ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ʏᴏᴜʀꜱ!", show_alert=True)
        return
    
    await query.answer()
    
    data = load_data()
    user_data = data.get(user_id, {})
    
    text = f"""
╔══════════════════════════════════╗
║     💰 **ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ**             ║
╚══════════════════════════════════╝

👤 **ᴜꜱᴇʀ:** {user_data.get('name', 'ناشناس')}

⭐ **XP:** {user_data.get('score', 0)}
⚡ **NOX:** {user_data.get('coins', 0)}
🎯 **ᴄᴀᴛᴄʜᴇꜱ:** {user_data.get('catches', 0)}
🏠 **ʜᴀʀᴇᴍ:** {len(user_data.get('claimed_arts', []))} ᴀʀᴛꜱ

━━━━━━━━━━━━━━━━━━━━━
💡 هر شکار = XP + NOX
⚡ هر ۱ NOX = ½ امتیاز XP
🎲 با `/gacha` شانس بگیر!
"""
    
    keyboard = [
        [glass_button("🏠 ʙᴀᴄᴋ", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def gacha_button(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    callback_data = query.data
    
    if not is_owner(callback_data, user_id):
        await query.answer("❌ ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ʏᴏᴜʀꜱ!", show_alert=True)
        return
    
    await query.answer()
    
    keyboard = [
        [glass_button(f"🌟 S+ ({GACHA_COST['S+']} NOX)", f'gacha_quick_S+_{user_id}', "🌟")],
        [glass_button(f"👑 S ({GACHA_COST['S']} NOX)", f'gacha_quick_S_{user_id}', "👑")],
        [glass_button(f"💜 A ({GACHA_COST['A']} NOX)", f'gacha_quick_A_{user_id}', "💜")],
        [glass_button(f"💙 B ({GACHA_COST['B']} NOX)", f'gacha_quick_B_{user_id}', "💙")],
        [glass_button(f"💚 C ({GACHA_COST['C']} NOX)", f'gacha_quick_C_{user_id}', "💚")],
        [glass_button("🏠 ʙᴀᴄᴋ", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎲 **ɢᴀᴄʜᴀ ᴍᴇɴᴜ**\n\n"
        "یک رنک را انتخاب کنید:\n"
        "🌟 S+ – هزینه {} NOX\n"
        "👑 S – هزینه {} NOX\n"
        "💜 A – هزینه {} NOX\n"
        "💙 B – هزینه {} NOX\n"
        "💚 C – هزینه {} NOX\n\n"
        "هر بار یک آرت تصادفی از آن رنک دریافت می‌کنید.".format(
            GACHA_COST['S+'], GACHA_COST['S'], GACHA_COST['A'],
            GACHA_COST['B'], GACHA_COST['C']
        ),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def gacha_quick(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    callback_data = query.data
    
    if not is_owner(callback_data, user_id):
        await query.answer("❌ ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ʏᴏᴜʀꜱ!", show_alert=True)
        return
    
    parts = callback_data.split('_')
    if len(parts) < 3:
        await query.answer("خطا!", show_alert=True)
        return
    rank = parts[2]
    if rank == 'S+':
        rank = 'S+'
    elif rank == 'S':
        rank = 'S'
    
    if rank not in GACHA_COST:
        await query.answer("رنک نامعتبر!", show_alert=True)
        return
    
    cost = GACHA_COST[rank]
    data = load_data()
    
    if user_id not in data:
        await query.answer("لطفاً ابتدا /start را بزنید!", show_alert=True)
        return
    
    coins = data[user_id].get('coins', 0)
    
    if coins < cost:
        await query.answer(f"موجودی ناکافی! شما {coins} NOX دارید.", show_alert=True)
        return
    
    photos = load_photos()
    rank_photos = [p for p in photos if p['rank'] == rank]
    
    if not rank_photos:
        await query.answer(f"هیچ آرتی با رنک {rank} وجود ندارد!", show_alert=True)
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
        await query.message.reply_photo(
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
        await query.message.reply_photo(
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
    
    keyboard = [
        [glass_button("🎲 دوباره", f'gacha_quick_{rank}_{user_id}', "🔄")],
        [glass_button("🏠 منو", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✅ گاچا انجام شد! می‌توانید دوباره امتحان کنید.",
        reply_markup=reply_markup
    )

async def harem_button(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    callback_data = query.data
    
    if not is_owner(callback_data, user_id):
        await query.answer("❌ ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ʏᴏᴜʀꜱ!", show_alert=True)
        return
    
    await query.answer()
    
    data = load_data()
    
    if user_id not in data:
        await query.edit_message_text("❌ شما هنوز هیچ آرتی شکار نکرده‌اید!")
        return
    
    claimed_ids = data[user_id].get('claimed_arts', [])
    
    if not claimed_ids:
        await query.edit_message_text(
            "🏠 **ɴᴏ ᴀʀᴛꜱ ɪɴ ʏᴏᴜʀ ʜᴀʀᴇᴍ ʏᴇᴛ!**\n\n"
            "📌 برای اضافه کردن آرت به حرمسرا:\n"
            "1️⃣ ارسال ۱۲۰ پیام به ربات\n"
            "2️⃣ ادعا با `/claim [اسم]`\n"
            "3️⃣ استفاده از `/gacha` برای شانس گرفتن"
        )
        return
    
    photos = load_photos()
    claimed_arts = []
    for pid in claimed_ids:
        for p in photos:
            if p['id'] == pid:
                claimed_arts.append(p)
                break
    
    if not claimed_arts:
        await query.edit_message_text("❌ خطا در بازیابی آرت‌های شکار شده!")
        return
    
    claimed_arts.sort(key=lambda x: RANK_ORDER.get(x['rank'], 10))
    
    total_points = sum(p['points'] for p in claimed_arts)
    total_coins = sum(p['points'] // 2 for p in claimed_arts)
    
    text = f"""
╔══════════════════════════════════╗
║     🏠 **ʏᴏᴜʀ ʜᴀʀᴇᴍ**             ║
║     ✨ **ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴀʀᴛꜱ**          ║
╚══════════════════════════════════╝

📊 **ᴛᴏᴛᴀʟ ᴀʀᴛꜱ:** {len(claimed_arts)}
⭐ **ᴛᴏᴛᴀʟ XP:** {total_points}
⚡ **ᴛᴏᴛᴀʟ NOX:** {total_coins}

━━━━━━━━━━━━━━━━━━━━━
"""
    
    for i, art in enumerate(claimed_arts, 1):
        rank_emoji = RANKS[art['rank']]['emoji']
        text += f"""
{i}. {rank_emoji} **{art['character']}**
   🎬 {art['anime']}
   🏅 {art['rank']} ({RANKS[art['rank']]['name']})
   ⭐ {art['points']} XP
"""
    
    keyboard = [
        [glass_button("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        await query.edit_message_text(parts[0], reply_markup=reply_markup, parse_mode='Markdown')
        for part in parts[1:]:
            await query.message.reply_text(part, parse_mode='Markdown')
    else:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def menu(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    callback_data = query.data
    
    if not is_owner(callback_data, user_id):
        await query.answer("❌ ᴛʜɪꜱ ʙᴜᴛᴛᴏɴ ɪꜱ ɴᴏᴛ ʏᴏᴜʀꜱ!", show_alert=True)
        return
    
    await query.answer()
    
    data = load_data()
    user_data = data.get(user_id, {})
    
    keyboard = [
        [glass_button("🖼️ ᴠɪᴇᴡ ᴀʀᴛꜱ", f'view_arts_{user_id}', "🎨")],
        [glass_button("💰 ᴡᴀʟʟᴇᴛ", f'wallet_{user_id}', "💳")],
        [glass_button("🎲 ɢᴀᴄʜᴀ", f'gacha_{user_id}', "🎰")],
        [glass_button("🏆 ʀᴀɴᴋɪɴɢꜱ", 'rankings', "👑")],
        [glass_button("🏠 ʜᴀʀᴇᴍ", f'harem_{user_id}', "💖")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"""
🎌 **ᴍᴀɪɴ ᴍᴇɴᴜ**

📊 **ᴍᴇꜱꜱᴀɢᴇꜱ:** {user_data.get('message_count', 0)}/120
⭐ **XP:** {user_data.get('score', 0)}
⚡ **NOX:** {user_data.get('coins', 0)}
🎯 **ᴄᴀᴛᴄʜᴇꜱ:** {user_data.get('catches', 0)}
🏠 **ʜᴀʀᴇᴍ:** {len(user_data.get('claimed_arts', []))} ᴀʀᴛꜱ

ᴄʜᴏᴏꜱᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:
""",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def rankings(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    await query.answer()
    
    data = load_data()
    
    rankings_list = []
    for uid, info in data.items():
        rankings_list.append({
            'id': uid,
            'name': info.get('name', 'ɴᴀꜱʜᴇɴᴀꜱ'),
            'score': info.get('score', 0),
            'coins': info.get('coins', 0),
            'catches': info.get('catches', 0)
        })
    
    rankings_list.sort(key=lambda x: x['score'], reverse=True)
    
    top_text = "╔══════════════════════════════════╗\n"
    top_text += "║     🏆 **ᴄᴀᴛᴄʜᴇʀ ʀᴀɴᴋɪɴɢꜱ**    ║\n"
    top_text += "╚══════════════════════════════════╝\n\n"
    
    for i, r in enumerate(rankings_list[:10], 1):
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'{i}.')
        top_text += f"{medal} {r['name']}: {r['score']} XP | ⚡{r['coins']} NOX\n"
    
    user_rank = None
    for i, r in enumerate(rankings_list, 1):
        if r['id'] == user_id:
            user_rank = i
            break
    
    if user_rank:
        top_text += f"\n📍 **ʏᴏᴜʀ ʀᴀɴᴋ:** {user_rank} / {len(rankings_list)}"
    
    keyboard = [
        [glass_button("🏠 ᴍᴇɴᴜ", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(top_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_catcher(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    await query.answer()
    
    keyboard = [
        [glass_button("🏠 ᴍᴇɴᴜ", f'menu_{user_id}', "🔙")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"""
╔══════════════════════════════════╗
║     📋 **ʀᴏʙᴀᴛ ɢᴜɪᴅᴇ**           ║
╚══════════════════════════════════╝

🎯 **ʜᴏᴡ ᴛᴏ ᴘʟᴀʏ:**

1️⃣ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ᴛᴏ ᴛʜᴇ ʙᴏᴛ
2️⃣ ᴀꜰᴛᴇʀ **𝟷𝟸𝟶 ᴍᴇꜱꜱᴀɢᴇꜱ**, ᴀɴ ᴀʀᴛ ᴀᴘᴘᴇᴀʀꜱ
3️⃣ ᴜꜱᴇ `/claim [ɴᴀᴍᴇ]` ᴛᴏ ᴄʟᴀɪᴍ ɪᴛ
4️⃣ ɢᴇᴛ **XP + NOX** ꜰᴏʀ ᴇᴀᴄʜ ᴄᴀᴛᴄʜ!
5️⃣ ᴜꜱᴇ `/gacha [S+/S/A/B/C]` ᴛᴏ ᴛʀʏ ʏᴏᴜʀ ʟᴜᴄᴋ!
6️⃣ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴡɪᴛʜ `/harem`

─────────────────────────────

💰 **ᴄᴜʀʀᴇɴᴄʏ:**
⭐ XP = Main points
⚡ NOX = Coin (½ of XP)

🎲 **ɢᴀᴄʜᴀ ᴄᴏꜱᴛꜱ:**
S+ = {GACHA_COST['S+']} NOX
S  = {GACHA_COST['S']} NOX
A  = {GACHA_COST['A']} NOX
B  = {GACHA_COST['B']} NOX
C  = {GACHA_COST['C']} NOX

─────────────────────────────

👑 **ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ:**
/spawn [ɪᴅ] - ꜱᴘᴀᴡɴ ᴀʀᴛ ꜰᴏʀ ᴜꜱᴇʀ
/check [ɪᴅ] - ᴄʜᴇᴄᴋ ᴜꜱᴇʀ
/upload - ᴜᴘʟᴏᴀᴅ ɴᴇᴡ ᴀʀᴛ
/delphoto [ɪᴅ] - ᴅᴇʟᴇᴛᴇ ᴀʀᴛ
/addadmin [ɪᴅ] - ᴀᴅᴅ ᴀᴅᴍɪɴ
/removeadmin [ɪᴅ] - ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ
/adminlist - ʟɪꜱᴛ ᴀᴅᴍɪɴꜱ

🛠️ **ɴᴇᴡ ᴀᴅᴍɪɴ ᴛᴏᴏʟꜱ:**
/removeart [ɪᴅ] [ᴀʀᴛ_ɪᴅ] - ʀᴇᴍᴏᴠᴇ ᴀʀᴛ ꜰʀᴏᴍ ᴜꜱᴇʀ
/removecat [ɪᴅ] [ᴀᴍᴏᴜɴᴛ] - ʀᴇᴍᴏᴠᴇ NOX ꜰʀᴏᴍ ᴜꜱᴇʀ
/giveart [ɪᴅ] [ᴀʀᴛ_ɪᴅ] - ɢɪᴠᴇ ᴀʀᴛ ᴛᴏ ᴜꜱᴇʀ
/addcat [ɪᴅ] [ᴀᴍᴏᴜɴᴛ] - ᴀᴅᴅ NOX ᴛᴏ ᴜꜱᴇʀ (ᴜꜱᴇ `me` ꜰᴏʀ ꜱᴇʟꜰ)

─────────────────────────────

🏅 **ʀᴀɴᴋꜱ (از بالا به پایین):**
🌟 S+ (نادرترین)
👑 S
💜 A
💙 B
💚 C

─────────────────────────────

📌 **ᴄʜᴀɴɴᴇʟ:** {CHANNEL_USERNAME}
""",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ============ مدیریت دستورات ============

async def handle_commands(update, context):
    text = update.message.text
    
    if text.startswith('/start'):
        await start(update, context)
    elif text.startswith('/claim'):
        await claim_command(update, context)
    elif text.startswith('/gacha'):
        await gacha_command(update, context)
    elif text.startswith('/spawn'):
        await spawn_command(update, context)
    elif text.startswith('/check'):
        await check_command(update, context)
    elif text.startswith('/harem'):
        await harem_command(update, context)
    elif text.startswith('/wallet'):
        await wallet_command(update, context)
    elif text.startswith('/upload'):
        await upload_command(update, context)
    elif text.startswith('/delphoto'):
        await delete_photo(update, context)
    elif text.startswith('/addadmin'):
        await add_admin(update, context)
    elif text.startswith('/removeadmin'):
        await remove_admin(update, context)
    elif text.startswith('/adminlist'):
        await list_admins(update, context)
    elif text.startswith('/removeart'):
        await remove_art_command(update, context)
    elif text.startswith('/removecat'):
        await remove_cat_command(update, context)
    elif text.startswith('/giveart'):
        await give_art_command(update, context)
    elif text.startswith('/addcat'):
        await add_cat_command(update, context)

# ============ اصلی ============

def main():
    if not os.path.exists(ADMINS_FILE):
        save_admins({'admins': ['7927200406']})
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('claim', claim_command))
    app.add_handler(CommandHandler('gacha', gacha_command))
    app.add_handler(CommandHandler('spawn', spawn_command))
    app.add_handler(CommandHandler('check', check_command))
    app.add_handler(CommandHandler('harem', harem_command))
    app.add_handler(CommandHandler('wallet', wallet_command))
    app.add_handler(CommandHandler('upload', upload_command))
    app.add_handler(CommandHandler('delphoto', delete_photo))
    app.add_handler(CommandHandler('addadmin', add_admin))
    app.add_handler(CommandHandler('removeadmin', remove_admin))
    app.add_handler(CommandHandler('adminlist', list_admins))
    
    app.add_handler(CommandHandler('removeart', remove_art_command))
    app.add_handler(CommandHandler('removecat', remove_cat_command))
    app.add_handler(CommandHandler('giveart', give_art_command))
    app.add_handler(CommandHandler('addcat', add_cat_command))
    
    app.add_handler(CallbackQueryHandler(view_arts, pattern=r'^view_arts_\d+$'))
    app.add_handler(CallbackQueryHandler(wallet_button, pattern=r'^wallet_\d+$'))
    app.add_handler(CallbackQueryHandler(gacha_button, pattern=r'^gacha_\d+$'))
    app.add_handler(CallbackQueryHandler(gacha_quick, pattern=r'^gacha_quick_(S\+|S|A|B|C)_\d+$'))
    app.add_handler(CallbackQueryHandler(harem_button, pattern=r'^harem_\d+$'))
    app.add_handler(CallbackQueryHandler(menu, pattern=r'^menu_\d+$'))
    app.add_handler(CallbackQueryHandler(rankings, pattern='^rankings$'))
    app.add_handler(CallbackQueryHandler(help_catcher, pattern='^help_catcher$'))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print('🎌 ʀᴏʙᴀᴛ ᴄᴀᴛᴄʜᴇʀ ɪꜱ ʀᴜɴɴɪɴɢ!')
    print(f'🤖 ʀᴏʙᴀᴛ: @IsuzuCatcherBot')
    print('👑 ᴀᴅᴍɪɴ: 7927200406')
    print('⚡ NOX Cᴏɪɴ ᴀᴅᴅᴇᴅ!')
    print('🏅 Ranks: S+ > S > A > B > C')
    print('🎲 /gacha [S+/S/A/B/C] - random art from rank')
    print('📤 /spawn [id] - spawn art for user')
    print('📝 /claim [name] - claim art')
    print('🔍 /check [id] - check user art (admin only)')
    print('🏠 /harem - view your collected arts')
    print('💰 /wallet - view your currency')
    print('🛠️ Admin tools: /removeart, /removecat, /giveart, /addcat')
    app.run_polling()

if __name__ == '__main__':
    main()