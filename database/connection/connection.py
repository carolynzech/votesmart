import os
import sys

sys.path.append(os.path.dirname(os.path.abspath('../')))

from database.adapters import ConfigDB
from dataclasses import dataclass, fields


@dataclass
class ConnectionInfo:
    connection_id: int = None
    host: str = None
    database: str = None
    port: int = None
    user: str = None
    password: str = None

    def __str__(self):
        return ', '.join([f'{k}: {v}' for k, v in {'connection_id': self.connection_id,
                                                   'host': self.host,
                                                   'database': self.database,
                                                   'port': self.port,
                                                   'user': self.user}.items()])

    def get_list(self):
        return [self.connection_id, self.host, self.database, self.port, self.user]

    @staticmethod
    def get_keys():
        return ['connection_id', 'host', 'database', 'port', 'user']

    def deltas(self):
        return [getattr(self, field.name) is not field.default for field in fields(self)]


class ConnectionManager:

    def __init__(self):

        self.db = ConfigDB('connection.db')
        self.table = 'connection'

        self.db.create(self.table, {'connection_id': 'integer primary key autoincrement',
                                    'host': 'text not null',
                                    'database': 'text',
                                    'port': 'integer',
                                    'user': 'text',
                                    'password': 'text'})

    def add(self, connection):
        self.db.insert(self.table, connection)
        return "Connection added!"

    def select(self, value, column='connection_id'):
        connection_list = [c.connection_id for c in self.list()]

        if connection_list:
            if value in connection_list:
                cursor = self.db.select(self.table, {column: value})

                header = [str(k[0]) for k in cursor.description] if cursor else None
                rows = cursor.fetchone()

                cursor.close()

                message = f"{column}={value} is selected."
                return message, ConnectionInfo(**dict(zip(header, rows)))
            else:
                message = f"{column}={value} is not found."
                return message, None
        else:
            message = f"No existing connections to select."
            return message, None

    def select_multiple(self, values, column='connection_id'):
        return [self.select(v, column) for v in values]

    def list(self):
        results = self.db.select(self.table)

        header = [str(k[0]) for k in results.description] if results else None
        rows = results.fetchall() if results else []

        records = [ConnectionInfo(**dict(zip(header, value))) for value in rows]

        return records

    def delete(self, connection_id):
        connection_list = [c.connection_id for c in self.list()]

        if connection_list:
            if connection_id in connection_list:
                self.db.delete(self.table, {'connection_id': connection_id})
                return f"connection_id={connection_id} is now deleted."

            else:
                return f"connection_id={connection_id} does not exist."
        else:
            return "No existing connections to delete."

    def delete_multiple(self, connection_ids):
        return [self.delete(connection_id) for connection_id in connection_ids]


class ConnectionUsage:

    def __init__(self):

        self.db = ConfigDB('connection.db')
        self.table = 'connection_usage'

        self.db.create(self.table, {'connection_usage_id': 'integer primary key autoincrement',
                                    'usage': 'text',
                                    'connection_id': 'integer',
                                    })

    def assign(self, usage, connection_info):
        self.db.insert(self.table, {'usage': usage, 'connection_id': connection_info.connection_id})
        return f"{usage} is associated with {connection_info.connection_id}"

    def is_assigned(self, usage):
        cursor = self.db.select(self.table, {'usage': usage})

        header = [str(k[0]) for k in cursor.description] if cursor else []
        rows = cursor.fetchone() or []

        cursor.close()

        results = dict(zip(header, rows))

        return results['connection_id'] if results else None

    def delete(self, usage):
        pass
