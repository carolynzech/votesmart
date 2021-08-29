import tkinter as tk
import os
import sys
from tabulate import tabulate

sys.path.append(os.path.dirname(os.path.abspath('./')))

from interface import cli
from database.connection import ConnectionInfo
from database.adapters import PostgreSQL
from database.dbtools import QueryTool


class QueryWriter(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):
        name = 'query-writer'
        self.query_tool = controller

        # OBJECTS
        self.__display = cli.objects.Display("Opening Writer...", command=cli.objects.Command(self._execute))
        self.__prompt = cli.objects.Prompt("Select a following action:")

        # NODES
        self.__node_F = cli.LinkNode(self.__display, show_instructions=False)
        self.__node_0 = cli.LinkNode(self.__prompt, self.__node_F)
        self.__node_1 = ExecuteQuery(self.query_tool, self.__node_0)
        self.__node_2 = QueryMessages(self.query_tool, self.__node_1.last_node())
        self.__node_3 = QueryResults(self.query_tool, self.__node_2.last_node())
        self.__node_L = self.__node_0

        self.__node_3.adopt_node(self.__node_L)

        # CONFIGURATIONS
        self.__prompt.options = {'1': cli.objects.Command(self.__node_0.set_next, value="Run",
                                                          command=cli.objects.Command(self.set_query),
                                                          next_node=self.__node_1.first_node())}

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):
        root = tk.Tk()
        root.title("Query Writer")

        x_scrollbar = tk.Scrollbar(root, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        y_scrollbar = tk.Scrollbar(root)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.__text_widget = tk.Text(root, wrap=tk.NONE, relief=tk.RIDGE, borderwidth=2,
                                     xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        self.__text_widget.configure(font=('Courier New', 16))
        self.__text_widget.pack(expand=True, fill=tk.BOTH)

        x_scrollbar.config(command=self.__text_widget.xview)
        y_scrollbar.config(command=self.__text_widget.yview)

    def set_query(self):
        self.query_tool.query = self.__text_widget.get('1.0', tk.END)


class ExecuteQuery(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'execute-query'
        self.query_tool = controller

        # OBJECTS
        self.__display = cli.objects.Display("Running Query...",
                                             command=cli.objects.Command(self._execute, respond=True))

        # NODES
        self.__node_F = cli.LinkNode(self.__display, show_instructions=False)
        self.__node_L = self.__node_F

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):
        message = self.query_tool.run()

        if message:
            return cli.format.Presets.error(f"There was an error executing the query:\n{message}")
        else:
            return ''


class QueryResults(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'query-results'
        self.query_tool = controller

        # OBJECTS
        self.__display = cli.objects.Display("Opening Results Window...", command=cli.objects.Command(self._execute))

        # NODES
        self.__node_F = cli.LinkNode(self.__display, show_instructions=False)
        self.__node_L = self.__node_F

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):
        r = self.query_tool.results

        root = tk.Tk()
        root.title("Query Results")

        x_scrollbar = tk.Scrollbar(root, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        y_scrollbar = tk.Scrollbar(root)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(root, wrap=tk.NONE, relief=tk.RIDGE, borderwidth=2,
                              xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        if r:
            table = tabulate(r[1], headers=r[0], tablefmt='fancy_grid')
            text_widget.insert(tk.END, str(table))
        else:
            pass

        text_widget.configure(state=tk.DISABLED, font=('Courier New', 12))
        text_widget.bind("<1>", lambda event: text_widget.focus_set())
        text_widget.pack(expand=True, fill=tk.BOTH)

        x_scrollbar.config(command=text_widget.xview)
        y_scrollbar.config(command=text_widget.yview)


class QueryMessages(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):
        name = 'query-messages'
        self.query_tool = controller

        # OBJECTS
        self.__display = cli.objects.Display("Query Message", cli.objects.Command(self._execute, respond=True))

        # nODES
        self.__node_F = cli.LinkNode(self.__display, show_instructions=False)
        self.__node_L = self.__node_F

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):
        message = self.query_tool.message()
        return cli.format.Presets.description(message)


if __name__ == '__main__':
    c = ConnectionInfo(host='REDACTED', database='REDACTED', port='REDACTED', user='REDACTED', password='REDACTED')

    pg = PostgreSQL(c)
    pg.connect()

    qt = QueryTool(pg)

    n_1 = QueryWriter(qt)

    e = cli.Engine(n_1.first_node())
    e.run()
