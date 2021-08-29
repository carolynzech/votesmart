import sqlite3
import pg8000


class ConfigDB:

    def __init__(self, filename):
        self.connection = sqlite3.connect(filename)

    def _execute(self, statement, values=None):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(statement, values or [])
            return cursor

    def create(self, table_name, columns):
        columns_and_types = ', '.join([f"{k} {v}" for k, v in columns.items()])

        self._execute(f"""
                       CREATE TABLE IF NOT EXISTS {table_name}
                       ({columns_and_types})
                       """)

    def select(self, table_name, conditions=None or {}):
        select_query = f"SELECT * FROM {table_name}"

        if conditions:
            select_conditions = ' AND '.join([f"{col} = ?" for col in conditions.keys()])
            select_query += f" WHERE {select_conditions}"

        return self._execute(select_query, tuple(conditions.values()))

    def insert(self, table_name, columns):
        column_names = ', '.join(columns.keys())

        self._execute(f"""
                       INSERT INTO {table_name} ({column_names})
                       VALUES({', '.join('?' * len(columns))})
                       """
                      , tuple(columns.values())
                      )

    def delete(self, table_name, conditions):
        delete_conditions = ' AND '.join([f"{col} = ?" for col in conditions.keys()])

        self._execute(f"""
                        DELETE FROM {table_name}
                        WHERE {delete_conditions}
                        """
                      , tuple(conditions.values())
                      )

    def reset(self, table_name):
        self._execute(f"DELETE FROM {table_name}")
        self._execute("VACUUM")

    def __del__(self):
        self.connection.close()


class PostgreSQL:

    def __init__(self, connection_info, paramstyle='named'):

        pg8000.paramstyle = paramstyle

        self.__connection_info = connection_info
        self.__connection = None

    @property
    def connection_info(self):
        return self.__connection_info

    @connection_info.setter
    def connection_info(self, c):
        if not self.__connection:
            self.__connection_info = c

    def connect(self, autocommit=True):

        connect_args = {'host': self.__connection_info.host,
                        'database': self.__connection_info.database,
                        'port': self.__connection_info.port,
                        'user': self.__connection_info.user,
                        'password': self.__connection_info.password
                        }
        self.__connection = pg8000.connect(**connect_args)
        self.__connection.autocommit = autocommit

    def disconnect(self):
        self.__connection.close()
        self.__connection = None

    def execute(self, statement, values=None):
        cursor = self.__connection.cursor()
        cursor.execute(statement, values or {})
        return cursor

    def __del__(self):
        if self.__connection:
            self.__connection.close()
