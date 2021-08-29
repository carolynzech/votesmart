try:
    import sys
    from interface import cli
    from database import connection

except ImportError:
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.abspath('../')))

    from interface import cli
    from database import connection


class ConnectionMenu(cli.LinkNodeBundle):
    """
    Menu contains the bundles to add, list, select and delete connection(s).
    """

    def __init__(self, controller, parent=None):

        name = 'connection-menu'

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Connection Menu")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, name=name, clear_screen=True)
        self.__node_L = self.__node_F

        self.add_connection = AddConnection(controller, parent=self.__node_F)
        self.list_connection = ListConnection(controller, parent=self.__node_F)
        self.delete_connection = DeleteConnection(controller, parent=self.__node_F)

        self.add_connection.adopt_node(self.__node_F)
        self.list_connection.adopt_node(self.__node_F)
        self.delete_connection.adopt_node(self.__node_F)

        # CONFIGURATIONS

        self.__prompt.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Add a connection",
                                     next_node=self.add_connection.first_node),
            '2': cli.objects.Command(self.__node_F.set_next, value="List Connection(s)",
                                     next_node=self.list_connection.first_node),
            '3': cli.objects.Command(self.__node_F.set_next, value="Delete Connection(s)",
                                     next_node=self.delete_connection.first_node)
        }

        if parent:
            self.__prompt.options.update(
                {'R': cli.objects.Command(self.__node_F.set_next, value="Return", next_node=parent)})

        super().__init__(self.__node_F, self.__node_L, parent=parent, name=self.name)


class AddConnection(cli.LinkNodeBundle):
    """
    Prompts user to enter necessary information for a connection to be stored.
    """

    def __init__(self, controller, parent=None):

        name = 'add-connection'

        self.connection_manager = controller

        # OBJECTS
        self.__display = cli.objects.Display(cli.format.Presets.header("Add a connection"))
        self.__prompt_0 = cli.objects.Prompt("Hostname")
        self.__prompt_1 = cli.objects.Prompt("Database Name")
        self.__prompt_2 = cli.objects.Prompt("Port", verification=self.will_it_int)
        self.__prompt_3 = cli.objects.Prompt("Username")
        self.__prompt_4 = cli.objects.Prompt("Password")
        self.__prompt_5 = cli.objects.Prompt("Confirm changes?")

        # NODES
        self.__node_F = cli.LinkNode(self.__display, name=name, clear_screen=True)
        self.__node_0 = cli.LinkNode(self.__prompt_0, self.__node_F, name=f'{name}_hostname', show_instructions=False)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_0, f'{name}_database', show_instructions=False)
        self.__node_2 = cli.LinkNode(self.__prompt_2, self.__node_1, f'{name}_port', show_instructions=False)
        self.__node_3 = cli.LinkNode(self.__prompt_3, self.__node_2, f'{name}_username', show_instructions=False)
        self.__node_4 = cli.LinkNode(self.__prompt_4, self.__node_3, f'{name}_password', show_instructions=False)
        self.__node_L = cli.LinkNode(self.__prompt_5, self.__node_4, f'{name}_confirm', show_instructions=False)

        # CONFIGURATIONS

        self.__prompt_5.options = {'1': cli.objects.Command(self._execute, value='Yes', respond=True),
                                   '2': 'No'}

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _execute(self):
        new_connection = {'host': self.__prompt_0.response,
                          'database': self.__prompt_1.response,
                          'port': self.__prompt_2.response,
                          'user': self.__prompt_3.response,
                          'password': self.__prompt_4.response}

        return self.connection_manager.add(new_connection)

    @cli.objects.Command()
    def will_it_int(self, response):
        try:
            int(response)
            return True,
        except ValueError:
            return False, "Input needs to be an integer"


class ListConnection(cli.LinkNodeBundle):
    """
    List the connections stored in a local database (sqlite3).
    """

    def __init__(self, controller, parent=None):
        name = 'list-connection'

        self.connection_manager = controller

        # OBJECTS
        self.__table = cli.objects.SimpleTable([connection.ConnectionInfo.get_keys()], as_rows=True,
                                               command=cli.objects.Command(self._execute))

        self.__table.title = "Stored Connections"
        self.__table.table_padding = 3
        self.__table.column_alignments = {0: 'L', 1: 'R'}

        # NODES
        self.__node_F = cli.LinkNode(self.__table, name=f'{name}_retrieve', show_instructions=False, clear_screen=True,
                                     acknowledge=True)
        self.__node_L = self.__node_F

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _execute(self):
        connection_list = self.connection_manager.list()
        connection_values = [list(map(str, c.get_list())) for c in connection_list]

        self.__table.matrix = [connection.ConnectionInfo.get_keys()] + connection_values


class SelectConnection(cli.LinkNodeBundle):
    """
    List the table containing the connections and prompts the user to select single or multiple connections.
    """

    def __init__(self, controller, parent=None):

        name = 'select-connection'

        self.connection_manager = controller

        # Connection selected will be stored in this list
        self.connections = []

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Select a connection (by ID)", verification=self.will_it_int, multiple_selection=True,
                                           command=cli.objects.Command(self._execute, respond=True, delay=0.5))
        # NODES
        self.__node_F = ListConnection(self.connection_manager)
        self.__node_L = cli.LinkNode(self.__prompt, self.__node_F.last_node, acknowledge=True)

        # CONFIGURATIONS
        self.__node_F.name = name
        self.__node_F.first_node.acknowledge = False

        super().__init__(name, self.__node_F.first_node, self.__node_L, parent=parent)

    def _execute(self):

        if self.__prompt.response == ['']:
            return "Skipped."

        s = list(map(int, self.__prompt.response))
        self.connections.clear()

        if len(s) > 1:
            results = self.connection_manager.select_multiple(s)
            message = '\n'.join([r[0] for r in results])
            self.connections += [r[1] for r in results if r]
            return message
        else:
            message, result = self.connection_manager.select(s[0])
            if result:
                self.connections.append(result)
            return message

    @cli.objects.Command()
    def will_it_int(self, response):
        if not response:
            return True,
        try:
            int(response)
            return True,
        except ValueError:
            return False, "Input needs to be an integer. "


class DeleteConnection(cli.LinkNodeBundle):
    """
    List the table of connections and prompts user to select single or multiple connections to delete
    """

    def __init__(self, controller, parent=None):

        name = 'delete-connection'

        self.connection_manager = controller

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Confirm Deletion?")

        # NODES
        self.__bundle_F = SelectConnection(self.connection_manager)
        self.__node_0 = cli.LinkNode(self.__prompt, name=f'{name}_confirmation', parent=self.__bundle_F)
        self.__node_L = cli.DummyLinkNode(parent=self.__node_0)

        self.__bundle_F.adopt_node(self.__node_L)

        # CONFIGURATIONS
        self.__bundle_F.last_node.object.question = "Select a connection to delete"
        self.__bundle_F.last_node.object.command.command = cli.objects.Command(self.is_connection_list)

        self.__prompt.options = {'1': cli.objects.Command(self._execute, value="Yes", respond=True),
                                 '2': "No"}

        super().__init__(name, self.__bundle_F.first_node, self.__node_L, parent=parent)

    def _execute(self):
        s = [c.connection_id if c else None for c in self.__bundle_F.connections]

        if len(s) > 1:
            results = self.connection_manager.delete_multiple(s)
            message = '\n'.join(results)
            return message
        elif len(s) == 1:
            results = self.connection_manager.delete(s[0])
            message = results
            return message
        else:
            pass

    def is_connection_list(self):
        if not self.__bundle_F.connections:
            self.__bundle_F.last_node.set_next(self.__node_L)
        else:
            self.__bundle_F.last_node.set_next(self.__node_0)


def main():
    cm = connection.ConnectionManager()
    menu = ConnectionMenu(cm)

    e = cli.Engine(menu.first_node)
    e.run()


if __name__ == '__main__':
    main()
