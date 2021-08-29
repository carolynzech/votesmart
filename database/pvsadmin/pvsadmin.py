import os
import sys

sys.path.append(os.path.dirname(os.path.abspath('../')))

from database.adapters import PostgreSQL
from database.connection import ConnectionInfo
from database.dbtools import QueryTool


class PVSAdmin:

    def __init__(self):

        self.dbname = 'pvsadmin'
        self.__adapter = PostgreSQL(ConnectionInfo())
        self.__query_tool = QueryTool(self.__adapter)

        self.__connected = False

    @property
    def adapter(self):
        return self.__adapter

    @adapter.setter
    def adapter(self, adapter):
        assert isinstance(self.__adapter, PostgreSQL)
        self.__adapter = adapter
        self.__query_tool.connection_adapter = adapter

    @property
    def query_tool(self):
        return self.__query_tool

    @query_tool.setter
    def query_tool(self, query_tool):
        assert isinstance(self.__adapter, QueryTool)
        self.__query_tool = query_tool
        self.__query_tool.connection_adapter = self.__adapter

    @property
    def connected(self):
        return self.__connected

    def set_connection(self, connection_info):
        self.__adapter.connection_info = connection_info

    def is_connection_set(self):
        return all(self.__adapter.connection_info.deltas())

    def establish_connection(self):

        try:
            self.__adapter.connect()
            self.__connected = True
            return True, f"Connection to {self.dbname} has been established."

        except Exception as e:
            self.__connected = False
            return False, str(e)

    def destroy_connection(self):
        self.__adapter.disconnect()
        self.__connected = False
