import sqlite3
import time


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"""INSERT INTO "users" (user_id) VALUES ('{user_id}')""")

    def user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT user_id FROM users WHERE user_id='{user_id}'")
        return bool(len(self.cursor.fetchall()))

    def get_user_attr(self, user_id, column_name):
        with self.connection:
            try:
                self.cursor.execute(f"SELECT {column_name} FROM users WHERE user_id='{user_id}'")
                return self.cursor.fetchone()[0]
            except:
                pass

    def set_user_attr(self, user_id, column_name, value):
        with self.connection:
            if str(value).isnumeric():
                self.cursor.execute(f"UPDATE users SET {column_name}={value} WHERE user_id='{user_id}'")
            else:
                self.cursor.execute(f"UPDATE users SET {column_name}='{value}' WHERE user_id='{user_id}'")

    def get_users_with_request(self):
        with self.connection:
            cur_time = int(time.time())
            self.cursor.execute(f"SELECT user_id FROM users WHERE request_time BETWEEN 2 and {cur_time + 3600}")
            users = self.cursor.fetchall()

        return list(map(lambda x: x[0], users))

    def remove_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"""DELETE FROM users WHERE user_id='{user_id}'""")

# db = Database()
# print(db.get_unreminded_users_after_day())
# print(time.time() - 1667293888)
