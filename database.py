import sqlite3
import datetime
import time

DB_NAME = 'bot_db.sqlite'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            user_id INTEGER,
            messages INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            stickers INTEGER DEFAULT 0,
            photos INTEGER DEFAULT 0,
            videos INTEGER DEFAULT 0,
            gifs INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_msg_date TEXT,
            commands INTEGER DEFAULT 0,
            night_messages INTEGER DEFAULT 0,
            vc_joins INTEGER DEFAULT 0,
            vc_duration INTEGER DEFAULT 0,
            platinum_awarded INTEGER DEFAULT 0,
            vc_session_start INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')
    
    columns_to_add = [
        ("streak", "INTEGER DEFAULT 0"),
        ("last_msg_date", "TEXT"),
        ("commands", "INTEGER DEFAULT 0"),
        ("night_messages", "INTEGER DEFAULT 0"),
        ("vc_joins", "INTEGER DEFAULT 0"),
        ("vc_duration", "INTEGER DEFAULT 0"),
        ("platinum_awarded", "INTEGER DEFAULT 0"),
        ("vc_session_start", "INTEGER DEFAULT 0"),
        ("gifs", "INTEGER DEFAULT 0")  # Добавлена колонка для гифок
    ]
    for col_name, col_type in columns_to_add:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
            
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            stat_type INTEGER,
            max_val INTEGER,
            difficulty TEXT,
            image TEXT
        )
    ''')
    
    try:
        c.execute("ALTER TABLE achievements ADD COLUMN image TEXT")
    except sqlite3.OperationalError:
        pass
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            chat_id INTEGER,
            user_id INTEGER,
            achievement_id INTEGER,
            PRIMARY KEY (chat_id, user_id, achievement_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ ---

def update_advanced_stats(chat_id, user_id, msg_type, is_reply, msg_date_str, is_night, is_cmd):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (chat_id, user_id) VALUES (?, ?)', (chat_id, user_id))

    c.execute('SELECT last_msg_date, streak FROM users WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    row = c.fetchone()
    last_date = row[0]
    current_streak = row[1] if row[1] is not None else 0
    
    new_streak = current_streak
    
    if last_date != msg_date_str:
        c.execute('UPDATE users SET messages = 0 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        
        if last_date is None:
            new_streak = 1
        else:
            try:
                ldate = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
                cdate = datetime.datetime.strptime(msg_date_str, "%Y-%m-%d").date()
                days_diff = (cdate - ldate).days
                if days_diff == 1:
                    new_streak += 1
                elif days_diff > 1:
                    new_streak = 1
            except ValueError:
                new_streak = 1

    if msg_type == 'text':
        c.execute('UPDATE users SET messages = messages + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    elif msg_type == 'sticker':
        c.execute('UPDATE users SET stickers = stickers + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    elif msg_type == 'photo':
        c.execute('UPDATE users SET photos = photos + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    elif msg_type == 'video':
        c.execute('UPDATE users SET videos = videos + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    elif msg_type == 'animation':
        c.execute('UPDATE users SET gifs = gifs + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))

    if is_reply:
        c.execute('UPDATE users SET replies = replies + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        
    if is_cmd:
        c.execute('UPDATE users SET commands = commands + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        
    if is_night:
        c.execute('UPDATE users SET night_messages = night_messages + 1 WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))

    c.execute('''UPDATE users SET 
                 streak = ?,
                 last_msg_date = ?
                 WHERE chat_id = ? AND user_id = ?''', 
              (new_streak, msg_date_str, chat_id, user_id))

    conn.commit()
    conn.close()

def get_profile(chat_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT messages, replies, stickers, photos, videos, 
                 streak, commands, night_messages, vc_joins, vc_duration, platinum_awarded, last_msg_date, gifs 
                 FROM users WHERE chat_id = ? AND user_id = ?''', (chat_id, user_id))
    row = c.fetchone()
    conn.close()

    if row is None:
        return {'messages': 0, 'replies': 0, 'stickers': 0, 'photos': 0, 'videos': 0, 
                'streak': 0, 'commands': 0, 'night_messages': 0, 'vc_joins': 0, 'vc_duration': 0, 'platinum': 0, 'gifs': 0}

    msk_tz = datetime.timezone(datetime.timedelta(hours=3))
    current_date_str = datetime.datetime.now(msk_tz).strftime('%Y-%m-%d')
    
    messages = row[0] or 0
    last_date = row[11]
    
    if last_date != current_date_str:
        messages = 0

    return {
        'messages': messages,
        'replies': row[1] or 0,
        'stickers': row[2] or 0,
        'photos': row[3] or 0,
        'videos': row[4] or 0,
        'streak': row[5] or 0,
        'commands': row[6] or 0,
        'night_messages': row[7] or 0,
        'vc_joins': row[8] or 0,
        'vc_duration': row[9] or 0,
        'platinum': row[10] or 0,
        'gifs': row[12] or 0
    }

def toggle_vc_session(chat_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (chat_id, user_id) VALUES (?, ?)', (chat_id, user_id))
    c.execute('SELECT vc_session_start FROM users WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    row = c.fetchone()
    current_start = row[0] if row and row[0] else 0
    
    now = int(time.time())
    
    if current_start == 0:
        c.execute('UPDATE users SET vc_session_start = ? WHERE chat_id = ? AND user_id = ?', (now, chat_id, user_id))
        conn.commit()
        conn.close()
        return {"status": "started", "time": 0}
    else:
        duration = now - current_start
        # Ограничение сессии до 12 часов (43200 сек), на случай если забыли выключить таймер
        if duration > 43200:
            duration = 43200 
            
        c.execute('''UPDATE users SET 
                     vc_duration = vc_duration + ?,
                     vc_session_start = 0
                     WHERE chat_id = ? AND user_id = ?''', (duration, chat_id, user_id))
        conn.commit()
        conn.close()
        return {"status": "ended", "time": duration}

def mark_platinum_awarded(chat_id, user_id, total_count):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET platinum_awarded = ? WHERE chat_id = ? AND user_id = ?', (total_count, chat_id, user_id))
    conn.commit()
    conn.close()

# --- АДМИНИСТРАТОРЫ ---
def is_admin(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row is not None

def add_admin(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_admin(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# --- ДОСТИЖЕНИЯ ---
def add_achievement(name, stat_type, max_val, difficulty, image):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO achievements (name, stat_type, max_val, difficulty, image) VALUES (?, ?, ?, ?, ?)', 
              (name, stat_type, max_val, difficulty, image))
    conn.commit()
    conn.close()

def remove_achievement(ach_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM achievements WHERE id = ?', (ach_id,))
    c.execute('DELETE FROM user_achievements WHERE achievement_id = ?', (ach_id,))
    conn.commit()
    conn.close()

def get_all_achievements():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, stat_type, max_val, difficulty, image FROM achievements')
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_completed_achievements(chat_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT achievement_id FROM user_achievements WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def mark_achievement_completed(chat_id, user_id, achievement_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO user_achievements (chat_id, user_id, achievement_id) VALUES (?, ?, ?)', (chat_id, user_id, achievement_id))
    conn.commit()
    conn.close()

def update_achievement(ach_id, name, stat_type, max_val, difficulty, image):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''UPDATE achievements 
                 SET name = ?, stat_type = ?, max_val = ?, difficulty = ?, image = ? 
                 WHERE id = ?''', 
              (name, stat_type, max_val, difficulty, image, ach_id))
    conn.commit()
    conn.close()

def remove_achievement_completions(ach_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM user_achievements WHERE achievement_id = ?', (ach_id,))
    conn.commit()
    conn.close()
