import sqlite3
from collections import Counter
from typing import List, Tuple

class CareerDB:
    def __init__(self, db_name: str = 'career_bot.db'):
        self.db_name = db_name
        self._init_db()  

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                tags TEXT,
                current INTEGER DEFAULT 0
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS careers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age TEXT,
                name TEXT,
                description TEXT,
                tags TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get_user_session(self, user_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT tags, current FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            tags = row[0].split(',') if row[0] else []
            current = int(row[1]) if row[1] is not None else 0
            return {"tags": tags, "current": current}
        return None

    def save_user_session(self, user_id: int, tags: List[str], current: int):
        conn = self._connect()
        cur = conn.cursor()
        tag_string = ','.join(tags)  
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cur.fetchone():
            cur.execute(
                "UPDATE users SET tags = ?, current = ? WHERE user_id = ?",
                (tag_string, current, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO users (user_id, tags, current) VALUES (?, ?, ?)",
                (user_id, tag_string, current)
            )
        conn.commit()
        conn.close()

    def clear_user_session(self, user_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def add_career(self, name: str, description: str, tags: List[str]):
        conn = self._connect()
        cur = conn.cursor()
        tag_string = ','.join(tags)  
        cur.execute("INSERT INTO careers (name, description, tags) VALUES (?, ?, ?)",
                    (name, description, tag_string))
        conn.commit()
        conn.close()

    def get_best_careers(self, user_id: int, top_n: int = 3) -> List[Tuple[str, str]]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT tags FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return []

        user_tags = row[0].split(',') if row[0] else []

        if "age_under_18" in user_tags:
            age_tag = "age_under_18"
        elif "age_plus_18" in user_tags:
            age_tag = "age_plus_18"
        else:
            age_tag = "None"

        if age_tag:
            cur.execute("SELECT name, description, tags FROM careers WHERE age = ? OR age = 'all'", (age_tag,))
        else:
            cur.execute("SELECT name, description, tags FROM careers WHERE age = 'all'")

        careers = cur.fetchall()

        scored = []
        for name, description, tag_str in careers:
            career_tags = tag_str.split(',') if tag_str else []
            score = sum((Counter(user_tags) & Counter(career_tags)).values())
            scored.append((score, name, description))

        conn.close()

        scored.sort(reverse=True, key=lambda x: x[0])
        return [(name, description) for score, name, description in scored[:top_n]]
    
    def load_careers(self, careers: List[dict]):
        conn = self._connect()
        cur = conn.cursor()

        for career in careers:
            age = career.get("age", "all")
            name = career["name"]
            description = career["description"]
            tags = ','.join(career.get("tags", []))

            cur.execute("SELECT id FROM careers WHERE name = ? AND age = ?", (name, age))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO careers (age, name, description, tags) VALUES (?, ?, ?, ?)",
                    (age, name, description, tags)
                )
        conn.commit()
        conn.close()