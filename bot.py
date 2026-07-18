import time
import datetime
import telebot
from telebot import types
import database as db

# ВАЖНО: Вставьте сюда НОВЫЙ токен. Старый токен скомпрометирован!
TOKEN = '8921063094:AAEaC0SnoUXBEVQWu6Bw6KOwBLrMhp94SUc'
SUPER_ADMIN_ID = 1857617424 

bot = telebot.TeleBot(TOKEN)
db.init_db()

user_states = {}

DIFFICULTIES = [
    "🥉 Легкая сложность 🥉",
    "🥈 Средняя сложность 🥈",
    "🥇 Тяжелая сложность 🥇",
    "🎖️ Безумная сложность 🎖️",
    "🏆 Кошмарная сложность 🏆",
    "🏵️ Адская сложность 🏵️",
    "🎁 Секретная сложность 🎁"
]

def check_is_admin(user_id):
    if user_id == SUPER_ADMIN_ID:
        return True
    return db.is_admin(user_id)

def send_achievement_notification(chat_id, name, difficulty, image, user, reply_to_id=None):
    diff_emoji = difficulty.split()[0]
    display_name = name if (name.startswith('«') and name.endswith('»')) else f"«{name}»"
    
    # Формируем ссылку-упоминание
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    text = f'Достижение "{diff_emoji}" сложности получено!\n{display_name}\n\n{mention}'
    
    if image:
        bot.send_photo(
            chat_id, 
            photo=image, 
            caption=text,
            reply_to_message_id=reply_to_id,
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            chat_id, 
            text,
            reply_to_message_id=reply_to_id,
            parse_mode='Markdown'
        )

def check_and_issue_achievements(message, user_id):
    chat_id = message.chat.id
    
    # Получаем объект пользователя для упоминания
    try:
        user = bot.get_chat_member(chat_id, user_id).user
    except:
        user = message.from_user
        
    stats = db.get_profile(chat_id, user_id)
    achievements = db.get_all_achievements()
    completed = db.get_user_completed_achievements(chat_id, user_id)
    
    for ach in achievements:
        ach_id, name, stat_type, max_val, difficulty, image = ach
        
        if ach_id in completed:
            continue
            
        current_val = 0
        if stat_type == 1: current_val = stats['messages']
        elif stat_type == 2: current_val = stats['replies']
        elif stat_type == 3: current_val = stats['stickers']
        elif stat_type == 4: current_val = stats['photos']
        elif stat_type == 5: current_val = stats['videos']
        elif stat_type == 6: current_val = stats['streak']
        elif stat_type == 7: current_val = stats['commands']
        elif stat_type == 8: current_val = stats['night_messages']
        elif stat_type == 9: current_val = stats['gifs']
        elif stat_type == 10: current_val = stats['vc_duration'] // 60
        elif stat_type == 0: continue
        
        if current_val >= max_val:
            db.mark_achievement_completed(chat_id, user_id, ach_id)
            send_achievement_notification(chat_id, name, difficulty, image, user, reply_to_id=message.message_id)
            completed.append(ach_id)
            
    total_achievements = len(achievements)
    if total_achievements > 0 and len(completed) >= total_achievements:
        if stats['platinum'] < total_achievements:
            db.mark_platinum_awarded(chat_id, user_id, total_achievements)
            
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            caption_text = f"Испытание завершено!\n!ПОЗДРАВЛЯЕМ ВЫ ЗАКРЫЛИ ВСЕ АЧИВКИ!\n🏆Платина🏆\n\n{mention}"
            
            try:
                with open(r'D:\AchievementBot\Достижение (77).png', 'rb') as photo:
                    bot.send_photo(
                        chat_id, 
                        photo, 
                        caption=caption_text,
                        reply_to_message_id=message.message_id,
                        parse_mode='Markdown'
                    )
            except FileNotFoundError:
                bot.send_message(
                    chat_id,
                    caption_text,
                    reply_to_message_id=message.message_id,
                    parse_mode='Markdown'
                )

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Пошел нахуй, я на месте✅")

@bot.message_handler(commands=['wiki', 'вики'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'вики')
def wiki_command(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Открыть Wiki", url="https://teletype.in/@blazevoide/editor/hxpShdt852N")
    markup.add(button)
    
    text = "📖Держи сайт с достижениями\n📖Там ты сможешь узнать как выполнить ачивки!"
    
    bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['profile', 'профиль'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'профиль')
def profile_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    stats = db.get_profile(chat_id, user_id)
    
    completed_count = len(db.get_user_completed_achievements(chat_id, user_id))
    total_achievements = len(db.get_all_achievements())
    
    vc_hours = stats['vc_duration'] // 3600
    vc_minutes = (stats['vc_duration'] % 3600) // 60

    if total_achievements > 0 and completed_count >= total_achievements:
        achievements_text = f"🏆 ПЛАТИНА 🏆 Выполнено достижений: {completed_count} из {total_achievements}"
    else:
        achievements_text = f"🏆 Выполнено достижений: {completed_count} из {total_achievements}"

    text = (f"👤 Профиль в этом чате\n\n"
            f"💬 Сообщения за сегодня: {stats['messages']}\n"
            f"↩️ Ответов: {stats['replies']}\n"
            f"😄 Стикеров: {stats['stickers']}\n"
            f"📷 Фото: {stats['photos']}\n"
            f"🎥 Видео: {stats['videos']}\n"
            f"🎞 Гифки: {stats['gifs']}\n"
            f"🔥 Серия (дней подряд): {stats['streak']}\n"
            f"🤖 Использовано команд: {stats['commands']}\n"
            f"🌙 Ночных сообщений: {stats['night_messages']}\n"
            f"⏳ Время в Видеочате: {vc_hours} ч. {vc_minutes} м.\n\n"
            f"{achievements_text}")

    bot.reply_to(message, text)

@bot.message_handler(commands=['achievements', 'достижения'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'достижения')
def achievements_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    stats = db.get_profile(chat_id, user_id)
    all_achievements = db.get_all_achievements()
    completed = db.get_user_completed_achievements(chat_id, user_id)
    
    total_count = len(all_achievements)
    completed_count = len(completed)
    
    lock_icon_header = "✅" if (total_count > 0 and completed_count == total_count) else "🔒"
    
    response = f"🏆 **Ваши достижения в этом чате:**\n———{lock_icon_header}{completed_count}/{total_count}{lock_icon_header}———\n\n"
    
    for diff in DIFFICULTIES:
        diff_achievements = [a for a in all_achievements if a[4] == diff]
        
        response += f"{diff}\n"
        if not diff_achievements:
            response += "— Пусто —\n\n"
            continue
            
        for idx, ach in enumerate(diff_achievements, 1):
            ach_id, name, stat_type, max_val, difficulty, _ = ach
            
            is_done = ach_id in completed
            
            if difficulty == "🎁 Секретная сложность 🎁" and not is_done:
                response += f"{idx}. «???» 🔒\n"
                continue
            
            current_val = 0
            if stat_type == 1: current_val = stats['messages']
            elif stat_type == 2: current_val = stats['replies']
            elif stat_type == 3: current_val = stats['stickers']
            elif stat_type == 4: current_val = stats['photos']
            elif stat_type == 5: current_val = stats['videos']
            elif stat_type == 6: current_val = stats['streak']
            elif stat_type == 7: current_val = stats['commands']
            elif stat_type == 8: current_val = stats['night_messages']
            elif stat_type == 9: current_val = stats['gifs']
            elif stat_type == 10: current_val = stats['vc_duration'] // 60
            elif stat_type == 0: current_val = 1 if is_done else 0
            
            if is_done or current_val > max_val:
                current_val = max_val
                
            status_icon = "🎁" if (difficulty == "🎁 Секретная сложность 🎁" and is_done) else ("✅" if is_done else "🔒")
            display_name = name if (name.startswith('«') and name.endswith('»')) else f"«{name}»"
            
            if stat_type == 0:
                response += f"{idx}. {display_name} {status_icon}\n"
            elif stat_type == 10:
                curr_h, curr_m = current_val // 60, current_val % 60
                max_h, max_m = max_val // 60, max_val % 60
                response += f"{idx}. {display_name} {curr_h}:{curr_m:02d}/{max_h}:{max_m:02d} {status_icon}\n"
            else:
                response += f"{idx}. {display_name} {current_val}/{max_val} {status_icon}\n"
        response += "\n"
        
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['vc', 'войс'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'войс')
def toggle_vc_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        result = db.toggle_vc_session(chat_id, user_id)
        
        if result['status'] == 'started':
            bot.reply_to(message, "🎙 **Таймер войса запущен.**\n\nНе забудьте снова написать `/vc` (или слово `войс`), когда выйдете, чтобы время сохранилось в базу!", parse_mode='Markdown')
        else:
            duration = result['time']
            mins = duration // 60
            hours = mins // 60
            mins_left = mins % 60
            
            bot.reply_to(message, f"⏹ **Таймер остановлен.**\n\nЗаработано времени: {hours} ч. {mins_left} м.", parse_mode='Markdown')
            check_and_issue_achievements(message, user_id)
    except Exception as e:
        bot.reply_to(message, "⚠️ Произошла ошибка при работе с таймером. Проверьте базу данных.")
        print(f"Ошибка в toggle_vc_command: {e}")

@bot.message_handler(commands=['testadmin'])
@bot.message_handler(func=lambda m: m.text and m.text.lower().split()[0] in ['проверка', 'проверить'])
def test_admin_command(message):
    args = message.text.split()
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(args) >= 2 and args[1].isdigit():
        target_id = int(args[1])
    else:
        target_id = message.from_user.id
        
    is_admin = check_is_admin(target_id)
    
    if target_id == message.from_user.id:
        if is_admin:
            bot.reply_to(message, "✅ Вы являетесь администратором бота.")
        else:
            bot.reply_to(message, "❌ У вас нет прав администратора.")
    else:
        if is_admin:
            bot.reply_to(message, f"✅ Пользователь {target_id} является администратором бота.")
        else:
            bot.reply_to(message, f"❌ Пользователь {target_id} не имеет прав администратора.")

@bot.message_handler(commands=['addadmin'])
@bot.message_handler(func=lambda m: m.text and m.text.lower().split()[0] == 'админ')
def add_admin_command(message):
    if not check_is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Отказано в доступе.")
    
    args = message.text.split()
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(args) >= 2 and args[1].isdigit():
        target_id = int(args[1])
        
    if not target_id:
        return bot.reply_to(message, "Использование: `админ <ID>` или ответьте словом `админ` на сообщение пользователя.", parse_mode='Markdown')
    
    db.add_admin(target_id)
    bot.reply_to(message, f"✅ Пользователь {target_id} добавлен в администраторы.")

@bot.message_handler(commands=['removeadmin'])
@bot.message_handler(func=lambda m: m.text and m.text.lower().split()[0] == 'снять')
def remove_admin_command(message):
    if not check_is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Отказано в доступе.")
    
    args = message.text.split()
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(args) >= 2 and args[1].isdigit():
        target_id = int(args[1])
        
    if not target_id:
        return bot.reply_to(message, "Использование: `снять <ID>` или ответьте словом `снять` на сообщение пользователя.", parse_mode='Markdown')
    
    db.remove_admin(target_id)
    bot.reply_to(message, f"✅ Пользователь {target_id} удален из администраторов.")

@bot.message_handler(commands=['addachievement'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'создать')
def start_achievement_constructor(message):
    admin_id = message.from_user.id
    if not check_is_admin(admin_id):
        return bot.reply_to(message, "❌ Отказано в доступе.")
        
    user_states[admin_id] = {}
    msg = bot.reply_to(message, "Введите название достижения:")
    bot.register_next_step_handler(msg, process_ach_name, admin_id)

def process_ach_name(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_ach_name, admin_id)
        return

    user_states[admin_id]['name'] = message.text
    
    text = ("📊 Тип:\n\n"
            "1 — Сообщения за сегодня\n"
            "2 — Ответы\n"
            "3 — Стикеры\n"
            "4 — Фото\n"
            "5 — Видео\n"
            "6 — Дни подряд (Серия)\n"
            "7 — Использование команд бота\n"
            "8 — Ночные сообщения (00:00 - 04:00 МСК)\n"
            "9 — Гифки\n"
            "10 — Часы в Видеочате\n"
            "0 — Без счетчика")
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, process_ach_type, admin_id)

def process_ach_type(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_ach_type, admin_id)
        return

    valid_types = [str(i) for i in range(11)]
    if message.text not in valid_types:
        msg = bot.reply_to(message, "Ошибка. Выберите цифру из списка:")
        bot.register_next_step_handler(msg, process_ach_type, admin_id)
        return
        
    user_states[admin_id]['type'] = int(message.text)
    
    if message.text == '0':
        user_states[admin_id]['max'] = 1
        ask_difficulty(message, admin_id)
    elif message.text == '10':
        msg = bot.reply_to(message, "Введите необходимое время в видеочате в формате ЧАСЫ:МИНУТЫ (например, 1:30 для 1.5 часов, 0:30 для 30 минут):")
        bot.register_next_step_handler(msg, process_ach_max, admin_id)
    else:
        msg = bot.reply_to(message, "Введите максимум для выполнения (например, 50):")
        bot.register_next_step_handler(msg, process_ach_max, admin_id)

def process_ach_max(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_ach_max, admin_id)
        return

    stat_type = user_states[admin_id]['type']
    
    if stat_type == 10:
        try:
            parts = message.text.split(':')
            if len(parts) != 2:
                raise ValueError
            hours = int(parts[0])
            mins = int(parts[1])
            if mins < 0 or mins >= 60 or hours < 0:
                raise ValueError
            
            # Сохраняем лимит времени в минутах
            user_states[admin_id]['max'] = hours * 60 + mins
            ask_difficulty(message, admin_id)
        except ValueError:
            msg = bot.reply_to(message, "⚠️ Пожалуйста, введите время в правильном формате (например, 1:30 или 0:30):")
            bot.register_next_step_handler(msg, process_ach_max, admin_id)
            return
    else:
        if not message.text.isdigit():
            msg = bot.reply_to(message, "Пожалуйста, введите число:")
            bot.register_next_step_handler(msg, process_ach_max, admin_id)
            return
            
        user_states[admin_id]['max'] = int(message.text)
        ask_difficulty(message, admin_id)

def ask_difficulty(message, admin_id):
    text = "Выберите сложность, отправив её номер:\n\n"
    for idx, diff in enumerate(DIFFICULTIES, 1):
        text += f"{idx} — {diff}\n"
        
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, process_ach_difficulty, admin_id)

def process_ach_difficulty(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_ach_difficulty, admin_id)
        return

    if not message.text or not message.text.isdigit() or not (1 <= int(message.text) <= len(DIFFICULTIES)):
        msg = bot.reply_to(message, "Ошибка. Выберите номер из списка:")
        bot.register_next_step_handler(msg, process_ach_difficulty, admin_id)
        return
        
    difficulty = DIFFICULTIES[int(message.text) - 1]
    user_states[admin_id]['difficulty'] = difficulty
    
    msg = bot.reply_to(message, "Отправьте картинку для достижения (просто отправьте фото боту).\n\nЕсли хотите использовать ссылку на картинку, отправьте ссылку. Если картинка не нужна, напишите «нет» (без кавычек).")
    bot.register_next_step_handler(msg, process_ach_image, admin_id)

def process_ach_image(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_ach_image, admin_id)
        return

    if admin_id not in user_states:
        return
        
    data = user_states[admin_id]
    image_id = None
    
    if message.photo:
        image_id = message.photo[-1].file_id
    elif message.text:
        if message.text.lower() != 'нет':
            image_id = message.text
            
    raw_name = data['name'].strip().strip('"').strip("'").strip('«').strip('»')
    quoted_name = f"«{raw_name}»"
            
    db.add_achievement(quoted_name, data['type'], data['max'], data['difficulty'], image_id)
    
    bot.reply_to(message, f"✅ Достижение {quoted_name} успешно создано в разделе:\n{data['difficulty']}")
    del user_states[admin_id]

@bot.message_handler(commands=['editachievement'])
@bot.message_handler(func=lambda m: m.text and m.text.lower().split()[0] == 'изменить')
def start_edit_achievement(message):
    admin_id = message.from_user.id
    if not check_is_admin(admin_id):
        return bot.reply_to(message, "❌ Отказано в доступе.")
        
    all_achievements = db.get_all_achievements()
    if not all_achievements:
        return bot.reply_to(message, "Достижений нет.")
        
    text = message.text.strip()
    if text.startswith('/editachievement'):
        ach_name_input = text[len('/editachievement'):].strip()
    elif text.lower().startswith('изменить'):
        ach_name_input = text[8:].strip()
    else:
        ach_name_input = ""
        
    if not ach_name_input:
        text_resp = "📝 Список достижений для изменения:\n"
        for ach in all_achievements:
            text_resp += f"ID: {ach[0]} — {ach[1]} ({ach[4]})\n"
        text_resp += "\nВведите `изменить <Название>` для редактирования."
        return bot.reply_to(message, text_resp, parse_mode='Markdown')
        
    def clean_string(s):
        return s.strip().strip('"').strip("'").strip('«').strip('»').lower()
        
    target_ach = None
    cleaned_input = clean_string(ach_name_input)
    
    for a in all_achievements:
        if clean_string(a[1]) == cleaned_input:
            target_ach = a
            break
            
    if not target_ach:
        return bot.reply_to(message, f"❌ Достижение с названием «{ach_name_input}» не найдено.")
        
    # Начинаем конструктор изменения
    user_states[admin_id] = {'edit_id': target_ach[0]}
    msg = bot.reply_to(message, f"🛠 Редактируем достижение: {target_ach[1]}\n\nВведите НОВОЕ название достижения:")
    bot.register_next_step_handler(msg, process_edit_name, admin_id)

def process_edit_name(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_edit_name, admin_id)
        return

    user_states[admin_id]['name'] = message.text
    
    text = ("📊 Выберите НОВЫЙ тип:\n\n"
            "1 — Сообщения за сегодня\n"
            "2 — Ответы\n"
            "3 — Стикеры\n"
            "4 — Фото\n"
            "5 — Видео\n"
            "6 — Дни подряд (Серия)\n"
            "7 — Использование команд бота\n"
            "8 — Ночные сообщения (00:00 - 04:00 МСК)\n"
            "9 — Гифки\n"
            "10 — Часы в Видеочате\n"
            "0 — Без счетчика")
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, process_edit_type, admin_id)

def process_edit_type(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_edit_type, admin_id)
        return

    valid_types = [str(i) for i in range(11)]
    if message.text not in valid_types:
        msg = bot.reply_to(message, "Ошибка. Выберите цифру из списка:")
        bot.register_next_step_handler(msg, process_edit_type, admin_id)
        return
        
    user_states[admin_id]['type'] = int(message.text)
    
    if message.text == '0':
        user_states[admin_id]['max'] = 1
        ask_edit_difficulty(message, admin_id)
    elif message.text == '10':
        msg = bot.reply_to(message, "Введите НОВОЕ время для выполнения в формате ЧАСЫ:МИНУТЫ (например, 1:30 для 1.5 часов, 0:30 для 30 минут):")
        bot.register_next_step_handler(msg, process_edit_max, admin_id)
    else:
        msg = bot.reply_to(message, "Введите НОВЫЙ максимум для выполнения (например, 50):")
        bot.register_next_step_handler(msg, process_edit_max, admin_id)

def process_edit_max(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_edit_max, admin_id)
        return

    stat_type = user_states[admin_id]['type']
    
    if stat_type == 10:
        try:
            parts = message.text.split(':')
            if len(parts) != 2:
                raise ValueError
            hours = int(parts[0])
            mins = int(parts[1])
            if mins < 0 or mins >= 60 or hours < 0:
                raise ValueError
            
            user_states[admin_id]['max'] = hours * 60 + mins
            ask_edit_difficulty(message, admin_id)
        except ValueError:
            msg = bot.reply_to(message, "⚠️ Пожалуйста, введите время в правильном формате (например, 1:30 или 0:30):")
            bot.register_next_step_handler(msg, process_edit_max, admin_id)
            return
    else:
        if not message.text.isdigit():
            msg = bot.reply_to(message, "Пожалуйста, введите число:")
            bot.register_next_step_handler(msg, process_edit_max, admin_id)
            return
            
        user_states[admin_id]['max'] = int(message.text)
        ask_edit_difficulty(message, admin_id)

def ask_edit_difficulty(message, admin_id):
    text = "Выберите НОВУЮ сложность, отправив её номер:\n\n"
    for idx, diff in enumerate(DIFFICULTIES, 1):
        text += f"{idx} — {diff}\n"
        
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, process_edit_difficulty, admin_id)

def process_edit_difficulty(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_edit_difficulty, admin_id)
        return

    if not message.text or not message.text.isdigit() or not (1 <= int(message.text) <= len(DIFFICULTIES)):
        msg = bot.reply_to(message, "Ошибка. Выберите номер из списка:")
        bot.register_next_step_handler(msg, process_edit_difficulty, admin_id)
        return
        
    difficulty = DIFFICULTIES[int(message.text) - 1]
    user_states[admin_id]['difficulty'] = difficulty
    
    msg = bot.reply_to(message, "Отправьте НОВУЮ картинку для достижения (просто отправьте фото боту).\n\nЕсли хотите использовать ссылку на картинку, отправьте ссылку. Если картинка не нужна, напишите «нет» (без кавычек).")
    bot.register_next_step_handler(msg, process_edit_image, admin_id)

def process_edit_image(message, admin_id):
    if message.from_user.id != admin_id:
        bot.register_next_step_handler(message, process_edit_image, admin_id)
        return

    if admin_id not in user_states:
        return
        
    data = user_states[admin_id]
    image_id = None
    
    if message.photo:
        image_id = message.photo[-1].file_id
    elif message.text:
        if message.text.lower() != 'нет':
            image_id = message.text
            
    raw_name = data['name'].strip().strip('"').strip("'").strip('«').strip('»')
    quoted_name = f"«{raw_name}»"
            
    # Обновляем в базе
    db.update_achievement(data['edit_id'], quoted_name, data['type'], data['max'], data['difficulty'], image_id)
    # УДАЛЯЕМ ачивку у всех пользователей
    db.remove_achievement_completions(data['edit_id'])
    
    bot.reply_to(message, f"✅ Достижение {quoted_name} успешно обновлено!\n\n⚠️ *Прогресс всех пользователей для этого достижения сброшен.* Оно будет выдано заново только тем, чья статистика соответствует новым требованиям (при их следующем сообщении).", parse_mode='Markdown')
    del user_states[admin_id]

@bot.message_handler(commands=['removeachievement'])
@bot.message_handler(func=lambda m: m.text and m.text.lower().split()[0] == 'удалить')
def remove_achievement_command(message):
    if not check_is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Отказано в доступе.")
        
    all_achievements = db.get_all_achievements()
    if not all_achievements:
        return bot.reply_to(message, "Достижений нет.")
        
    text = message.text.strip()
    if text.startswith('/removeachievement'):
        ach_name_input = text[len('/removeachievement'):].strip()
    elif text.lower().startswith('удалить'):
        ach_name_input = text[7:].strip()
    else:
        ach_name_input = ""
        
    if not ach_name_input:
        text_resp = "Список достижений для удаления:\n"
        for ach in all_achievements:
            text_resp += f"ID: {ach[0]} — {ach[1]} ({ach[4]})\n"
        text_resp += "\nВведите `удалить <Название>` для удаления."
        return bot.reply_to(message, text_resp, parse_mode='Markdown')
        
    def clean_string(s):
        return s.strip().strip('"').strip("'").strip('«').strip('»').lower()
        
    target_ach = None
    cleaned_input = clean_string(ach_name_input)
    
    for a in all_achievements:
        if clean_string(a[1]) == cleaned_input:
            target_ach = a
            break
            
    if not target_ach:
        return bot.reply_to(message, f"❌ Достижение с названием «{ach_name_input}» не найдено.")
        
    db.remove_achievement(target_ach[0])
    bot.reply_to(message, f"✅ Достижение {target_ach[1]} успешно удалено.")

@bot.message_handler(commands=['giveachievement'])
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('выдать'))
def give_achievement_command(message):
    if not check_is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Отказано в доступе.")
    
    text = message.text.strip()
    if text.startswith('/giveachievement'):
        text_args = text[len('/giveachievement'):].strip()
    elif text.lower().startswith('выдать'):
        text_args = text[6:].strip()
    else:
        text_args = ""

    target_id = None
    ach_name_input = ""

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        ach_name_input = text_args
    else:
        parts = text_args.split(maxsplit=1)
        if len(parts) >= 2 and parts[0].isdigit():
            target_id = int(parts[0])
            ach_name_input = parts[1]

    if not target_id or not ach_name_input:
        return bot.reply_to(
            message, 
            "Использование:\n`выдать <ID_Пользователя> <Название>`\nИли ответьте словом `выдать <Название>` на сообщение пользователя.",
            parse_mode='Markdown'
        )
        
    chat_id = message.chat.id
    all_ach = db.get_all_achievements()
    
    def clean_string(s):
        return s.strip().strip('"').strip("'").strip('«').strip('»').lower()

    target_ach = None
    cleaned_input = clean_string(ach_name_input)
    
    for a in all_ach:
        if clean_string(a[1]) == cleaned_input:
            target_ach = a
            break
            
    if not target_ach:
        return bot.reply_to(message, f"❌ Достижение с названием «{ach_name_input}» не найдено.")
        
    ach_id, name, stat_type, max_val, difficulty, image = target_ach
    
    try:
        target_user = bot.get_chat_member(chat_id, target_id).user
    except:
        target_user = message.from_user
    
    completed = db.get_user_completed_achievements(chat_id, target_id)
    if ach_id in completed:
        return bot.reply_to(message, f"❌ У данного участника уже есть достижение {name}.")
        
    db.mark_achievement_completed(chat_id, target_id, ach_id)
    
    send_achievement_notification(chat_id, name, difficulty, image, target_user, reply_to_id=message.message_id)
    
    check_and_issue_achievements(message, target_id)

@bot.message_handler(content_types=['text', 'sticker', 'photo', 'video', 'animation'])
def count_messages(message):
    if (time.time() - message.date) > 30:
        return
        
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg_type = message.content_type
    is_reply = message.reply_to_message is not None
    
    msk_tz = datetime.timezone(datetime.timedelta(hours=3))
    msg_dt = datetime.datetime.fromtimestamp(message.date, tz=msk_tz)
    msg_date_str = msg_dt.strftime('%Y-%m-%d')
    
    is_night = 0 <= msg_dt.hour < 4
    is_cmd = msg_type == 'text' and message.text.startswith('/')

    db.update_advanced_stats(chat_id, user_id, msg_type, is_reply, msg_date_str, is_night, is_cmd)
    check_and_issue_achievements(message, user_id)

if __name__ == '__main__':
    print("Бот запускается...")
    bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен и готов к работе!")
    bot.infinity_polling(skip_pending=True)
