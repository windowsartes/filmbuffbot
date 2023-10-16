import asyncio
import sqlite3
import typing as tp


class CinemabotDatabase:
    """
    Database for storing search history.
    """
    def __init__(self, path_to_database: str):
        """
        Create a connection to given database, if database doesn't exist, the new one is automatically created;
        Also creates 'history' table if it doesn't exist. 'History' table will be used in 'get_personal_statistics',
        'insert_value' and 'get_last_records' methods.
        :param path_to_database: path to database
        """
        self.connection = sqlite3.connect(path_to_database)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
            chat_id VARCHAR(255) NOT NULL,
            movie_title CHAR(255) NOT NULL,
            movie_count INT DEFAULT 1
        ); """)

    async def insert_value(self, chat_id: str, movie_title: str) -> None:
        """
        Insert new search value into the 'history' table
        :param chat_id: chat id from message.from_user.id
        :param movie_title: movie's title
        :return:
        """
        self.cursor.execute("""
            INSERT INTO history (chat_id, movie_title)
            VALUES (:chat_id, :movie_title)
        """, {'chat_id': chat_id, 'movie_title': movie_title})
        await asyncio.sleep(0.05)
        self.connection.commit()

    async def get_personal_statistics(self, chat_id: str) -> tp.List[tp.Tuple[str, int]]:
        """
        Return search history according to user's chat id. Associated with /stats command in button
        :param chat_id: user's chat id from message.from_user.id or callback.from_user.id
        :return: user's search statistics
        """
        self.cursor.execute("""
                SELECT movie_title, sum(movie_count)
                FROM history
                WHERE chat_id = :chat_id
                GROUP BY chat_id, movie_title
              """, {'chat_id': chat_id})
        await asyncio.sleep(0.05)
        return self.cursor.fetchall()

    async def get_last_records(self, chat_id: str) -> tp.List[tp.Tuple[str]]:
        """
        Return user's search history. Here lower means newer. Associated with /history command in button
        :param chat_id: user's chat id from message.from_user.id or callback.from_user.id
        :return: user's search history
        """
        self.cursor.execute("""
                SELECT movie_title
                FROM history
                WHERE chat_id = :chat_id
                ORDER BY rowid DESC
              """, {'chat_id': chat_id})
        await asyncio.sleep(0.05)
        return self.cursor.fetchall()[::-1]
