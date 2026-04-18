import telebot
import time
import json
import os
import random
from datetime import datetime, timedelta
from telebot import types

# --- الإعدادات الأساسية ---
TOKEN = '8607488569:AAF4bSlqa7m4COKzQUAZ50giIAy7BtGfZSM'
ADMIN_ID =8741892307
DATA_FILE = 'pro_data.json'
USERS_FILE = 'pro_users.json'
GIFT_LOG = 'gift_log.json'
STATS_FILE = 'global_stats.json'
BAN_FILE = 'banned_users.json'

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- دوال التخزين الآمن ---
def load_db(file, default):
    try:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f: return json.load(f)
    except: pass
    return default

def save_db(file, data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

db = load_db(DATA_FILE, {})
users = load_db(USERS_FILE, [])
gift_data = load_db(GIFT_LOG, {})
global_stats = load_db(STATS_FILE, {"total_served": 0})
banned_users = load_db(BAN_FILE, {}) # { "user_id": "unlock_time" }

user_states = {}
last_msg_time = {}

# --- نظام الحماية من الحظر والسبام ---
def is_banned(user_id):
    uid = str(user_id)
    if uid in banned_users:
        unlock_time = datetime.strptime(banned_users[uid], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > unlock_time:
            del banned_users[uid]
            save_db(BAN_FILE, banned_users)
            return False
        return True
    return False

def is_spam(user_id):
    curr = time.time()
    if user_id in last_msg_time and curr - last_msg_time[user_id] < 0.7:
        return True
    last_msg_time[user_id] = curr
    return False

# --- لوحة المفاتيح الشفافة المحدثة ---
def get_main_keyboard(is_admin):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    u1 = types.InlineKeyboardButton("تريند اليوم 🔥", callback_data="u_trend", icon_custom_emoji_id="5852942192720486360")
    u2 = types.InlineKeyboardButton("عجلة الحظ 🎡", callback_data="u_spin", icon_custom_emoji_id="5210885740640100140")
    u3 = types.InlineKeyboardButton("نظام VIP 👑", callback_data="u_vip", icon_custom_emoji_id="5992405033566607909")
    u4 = types.InlineKeyboardButton("قائمة المشاهير 📱", callback_data="u_list", icon_custom_emoji_id="5330237710655306682")
    
    markup.add(u1, u2, u3, u4)

    if is_admin:
        a1 = types.InlineKeyboardButton("إضافة تصميم ✅", callback_data="a_add", icon_custom_emoji_id="5940251786857158376")
        a2 = types.InlineKeyboardButton("إذاعة عامة 📢", callback_data="a_bc", icon_custom_emoji_id="5879809712827928815")
        a3 = types.InlineKeyboardButton("الإحصائيات 📊", callback_data="a_stats", icon_custom_emoji_id="5310244917065294444")
        markup.add(a1, a2, a3)

    # العداد يبلش من 0 ويكون آخر زر بالأسفل
    count = global_stats["total_served"]
    b_count = types.InlineKeyboardButton(f"🎬 تصاميم تم إنجازها: {count}", callback_data="none", icon_custom_emoji_id="5785317387184116231")
    markup.add(b_count)
    
    return markup

# --- رسالة الترحيب الاحترافية ---
@bot.message_handler(commands=['start'])
def welcome_start(message):
    try:
        uid = message.from_user.id
        if is_banned(uid):
            bot.send_message(message.chat.id, "🚫 <b>أنت محظور من البوت مؤقتاً!</b>")
            return
            
        if is_spam(uid): return
        
        if uid not in users:
            users.append(uid)
            save_db(USERS_FILE, users)
            alert = (f"👑 <b>عضو جديد انضم!</b>\nالاسم: {message.from_user.first_name}\nالآيدي: <code>{uid}</code>")
            bot.send_message(ADMIN_ID, alert)

        welcome_text = (
            f"<tg-emoji emoji-id='5339156021266916158'>😊</tg-emoji> <b>هلا والله بـ {message.from_user.first_name} في Video Star!</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"<b>🚀 أقوى بوت لتصاميم المشاهير بنسخة التوربو</b>\n"
            f"<b>🛡️ نظام الحماية وفك الحظر: مـفـعـل ✅</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"<b>💡 اكتب اسم مشهورك الآن بالأسفل مباشرةً!</b>"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(uid == ADMIN_ID))
    except: pass

# --- نظام سحب الفيديوهات والبحث ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    try:
        uid = message.from_user.id
        if is_banned(uid): return
        if is_spam(uid): return
        
        name = message.text.strip()
        
        # ميزة الحظر للمالك (اكتب: حظر + الآيدي)
        if name.startswith("حظر ") and uid == ADMIN_ID:
            target_id = name.split(" ")[1]
            unlock_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            banned_users[target_id] = unlock_date
            save_db(BAN_FILE, banned_users)
            bot.reply_to(message, f"✅ تم حظر <code>{target_id}</code> لمدة 24 ساعة.")
            return

        if name in db:
            video_id = db[name][-1]
            global_stats["total_served"] += 1
            save_db(STATS_FILE, global_stats)
            
            temp = bot.send_message(message.chat.id, "🔍 <b>جاري سحب التصميم...</b>")
            time.sleep(0.5)
            bot.delete_message(message.chat.id, temp.message_id)
            
            bot.send_video(
                message.chat.id, 
                video_id, 
                caption=f"✅ <b>تم التجهيز: {name}</b>\n\n<b>👤 المطور: @z388a</b>",
                protect_content=True
            )
        elif name != "/start":
            bot.send_message(message.chat.id, f"😔 <b>عذراً، ({name}) مو موجود.. تم إبلاغ عباس!</b>")
    except: pass

# --- إدارة الأزرار الشفافة ---
@bot.callback_query_handler(func=lambda call: True)
def handle_inline(call):
    try:
        uid = call.from_user.id
        if is_banned(uid): return
        
        if call.data == "u_spin":
            spin_wheel(call.message, call.from_user)
        elif call.data == "u_vip":
            bot.send_message(call.message.chat.id, "👑 <b>مميزات VIP:</b>\n• إزالة حقوق البوت\n• طلبات خاصة\n<b>للتفعيل: @z388a</b>")
        elif call.data == "a_stats" and uid == ADMIN_ID:
            msg = f"📊 <b>إحصائياتك يا عباس:</b>\n👤 الأعضاء: {len(users)}\n🎬 الفيديوهات: {len(db)}\n⚡️ الإنجازات: {global_stats['total_served']}"
            bot.send_message(call.message.chat.id, msg)
        elif call.data == "a_add" and uid == ADMIN_ID:
            bot.send_message(call.message.chat.id, "ارسل اسم المشهور:")
            bot.register_next_step_handler(call.message, get_name_admin)
        bot.answer_callback_query(call.id)
    except: pass

# --- نظام عجلة الحظ ---
def spin_wheel(message, user):
    try:
        uid = str(user.id)
        today = datetime.now().strftime("%Y-%m-%d")
        if uid in gift_data and gift_data[uid] == today:
            bot.send_message(message.chat.id, "😔 <b>جرب حظك غداً عزيزي!</b>")
            return

        win = random.choice([True, False, False, False])
        if win:
            bot.send_message(message.chat.id, "🎁 <b>مبروك! فزت بـ قلب نجوم 💝 ارسل سكرين للمالك @Clewa1</b>")
        else:
            bot.send_message(message.chat.id, "🤔 <b>حظ أوفر! العجلة ما وكفت يمك اليوم.</b>")
            
        gift_data[uid] = today
        save_db(GIFT_LOG, gift_data)
    except: pass

# --- وظائف الإدارة ---
def get_name_admin(message):
    user_states[message.from_user.id] = message.text.strip()
    bot.send_message(message.chat.id, "ارسل الفيديو:")
    bot.register_next_step_handler(message, save_video_admin)

def save_video_admin(message):
    try:
        if message.content_type == 'video':
            name = user_states.get(message.from_user.id)
            if name not in db: db[name] = []
            db[name].append(message.video.file_id)
            save_db(DATA_FILE, db)
            bot.send_message(message.chat.id, "✅ <b>تم الحفظ يا ملك!</b>")
        else:
            bot.send_message(message.chat.id, "❌ ارسل فيديو فقط!")
    except: pass

print("Bot Video Star V21 SAFE & CLEAN is Running...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
