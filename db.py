import sqlite3


class BotDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def user_exists(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        result = self.cursor.execute(f"SELECT `id` FROM `users` WHERE `user_id` = {user_id}")
        return bool(len(result.fetchall()))

    def get_user_id(self, user_id):
        """Достаем id юзера в базе по его user_id"""
        result = self.cursor.execute(f"SELECT `id` FROM `users` WHERE `user_id` = {user_id}")
        return result.fetchone()[0]

    def add_user(self, user_id):
        """Добавляем юзера в базу"""
        self.cursor.execute(f"INSERT INTO `users` (`user_id`) VALUES ({user_id})")
        return self.conn.commit()

    def add_record(self, user_id, l, d, m):
        """Создаем запись о доходах/расходах"""
        # print(f"INSERT INTO 'reminders' ('users_id', 'loop', 'date', 'msg') VALUES "
        #                     f"({self.get_user_id(user_id)}, {l}, '{d}', '{m}')")
        self.cursor.execute(f"INSERT INTO 'reminders' ('users_id', 'loop', 'date', 'msg') VALUES "
                            f"({self.get_user_id(user_id)}, {l}, '{d}', '{m}')")
        return self.conn.commit()

    def get_users(self):
        result = self.cursor.execute("SELECT * FROM users")
        return result.fetchall()

    def get_records(self, users_id):
        result = self.cursor.execute(f"SELECT * FROM reminders WHERE users_id = {users_id}")
        return result.fetchall()

    def remove_record(self, id_record):
        self.cursor.execute(f"DELETE FROM reminders WHERE id = {id_record}")
        return self.conn.commit()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()
