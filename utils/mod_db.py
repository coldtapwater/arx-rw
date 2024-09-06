import sqlite3
from datetime import datetime

class ModDB:
    def __init__(self, db_file='moderation.db'):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id INTEGER PRIMARY KEY,
            modlog_channel INTEGER,
            ban_message TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            timestamp DATETIME
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            action_type TEXT,
            user_id INTEGER,
            mod_id INTEGER,
            reason TEXT,
            timestamp DATETIME,
            duration TEXT
        )
        ''')
        self.conn.commit()

    def get_modlog_channel(self, guild_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT modlog_channel FROM guild_config WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    def set_modlog_channel(self, guild_id, channel_id):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO guild_config (guild_id, modlog_channel) VALUES (?, ?)', 
                       (guild_id, channel_id))
        self.conn.commit()

    def get_ban_message(self, guild_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT ban_message FROM guild_config WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        return result[0] if result else "You have been banned from the server."

    def set_ban_message(self, guild_id, message):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO guild_config (guild_id, ban_message) VALUES (?, ?)', 
                       (guild_id, message))
        self.conn.commit()

    def add_warning(self, guild_id, user_id, reason):
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        cursor.execute('INSERT INTO warnings (guild_id, user_id, reason, timestamp) VALUES (?, ?, ?, ?)',
                       (guild_id, user_id, reason, timestamp))
        self.conn.commit()

    def get_warnings(self, guild_id, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ?', 
                       (guild_id, user_id))
        return cursor.fetchall()

    def add_action(self, guild_id, action_type, user_id, mod_id, reason, duration=None):
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        cursor.execute('''
        INSERT INTO actions (guild_id, action_type, user_id, mod_id, reason, timestamp, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (guild_id, action_type, user_id, mod_id, reason, timestamp, str(duration) if duration else None))
        self.conn.commit()

    def get_actions(self, guild_id, user_id=None):
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute('''
            SELECT action_type, user_id, mod_id, reason, timestamp, duration
            FROM actions WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
        else:
            cursor.execute('''
            SELECT action_type, user_id, mod_id, reason, timestamp, duration
            FROM actions WHERE guild_id = ?
            ''', (guild_id,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()