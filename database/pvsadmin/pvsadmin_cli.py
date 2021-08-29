import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath('../')))

from database import pvsadmin
from database.connection import connection_cli
from interface import cli


class PVSAdminMenu(cli.LinkNodeBundle):
    def __init__(self, pvsadmin, connection_manager, parent=None):

        name = 'pvsadmin-menu'
        self.pvsadmin = pvsadmin
        self.connection_manager = connection_manager

        # OBJECTS
        self.__prompt = cli.objects.Prompt("PVSAdmin Menu", command=cli.objects.Command(self._feature_access))
        self.__command = cli.objects.Command(self.pvsadmin.destroy_connection)

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, name=name, clear_screen=True)
        self.__node_0 = EstablishConnection(self.pvsadmin, parent=self.__node_F)
        self.__node_1 = cli.LinkNode(self.__command, parent=self.__node_F)
        self.__node_2 = ModifyConnection(self.pvsadmin, self.connection_manager, parent=self.__node_F)
        self.__node_L = self.__node_F

        self.__node_F.adopt(self.__node_F)
        self.__node_0.adopt_node(self.__node_L)
        self.__node_1.adopt(self.__node_L)
        self.__node_2.adopt_node(self.__node_L)

        # CONFIGURATIONS
        self.__prompt.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Connect", next_node=self.__node_0.first_node()),
            '2': cli.objects.Command(self.__node_F.set_next, value="Modify Connection",
                                     next_node=self.__node_2.first_node())}

        self.__prompt.exe_seq = 'before'

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt.options.update({'R': cli.objects.Command(self.__node_F.set_next, value="Return",
                                                                   next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _feature_access(self):

        if not self.pvsadmin.connected:
            self.__prompt.options.update({'2': cli.objects.Command(self.__node_F.set_next, value="Modify Connection",
                                                                   next_node=self.__node_2.first_node())})
            if self.pvsadmin.is_connection_set():
                self.__prompt.options.update(
                    {'1': cli.objects.Command(self.__node_F.set_next, value="Connect",
                                              next_node=self.__node_0.first_node())})
            else:
                self.__prompt.options.update(
                    {'1': cli.objects.Command(self.__node_F.set_next, value=cli.format.Presets.unavailable("Connect"),
                                              next_node=self.__node_F)})
        else:
            self.__prompt.options.update(
                {'1': cli.objects.Command(self.__node_F.set_next, value="Disconnect", next_node=self.__node_1)})
            self.__prompt.options.update(
                {'2': cli.objects.Command(self.__node_F.set_next,
                                          value=cli.format.Presets.unavailable("Modify Connection"),
                                          next_node=self.__node_F)})


class ModifyConnection(cli.LinkNodeBundle):

    def __init__(self, pvsadmin, connection_manager, parent=None):

        name = 'modify-connection'
        self.pvsadmin = pvsadmin
        self.connection_manager = connection_manager

        # OBJECTS
        self.__display = cli.objects.Display("Checking for stored connections...",
                                             command=cli.objects.Command(self._check_stored_connections, respond=True))

        # NODES
        self.__node_F = cli.LinkNode(self.__display, acknowledge=True)
        self.__node_0 = connection_cli.SelectConnection(self.connection_manager, parent=self.__node_F)
        self.__node_1 = connection_cli.AddConnection(self.connection_manager, parent=self.__node_F)
        self.__node_L = cli.LinkNode(cli.objects.Command(self._set_connection), self.__node_0.last_node(), show_instructions=False)

        self.__node_1.adopt_node(self.__node_0.first_node())
        self.connections = self.__node_0.connections

        # CONFIGURATIONS
        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _check_stored_connections(self):
        results = self.connection_manager.list()

        if results:
            self.__node_F.set_next(self.__node_0.first_node())
            return cli.format.Presets.instruction(f"{len(results)} connection(s) detected. Proceed to select a "
                                                  f"connection.")
        else:
            self.__node_F.set_next(self.__node_1.first_node())
            return cli.format.Presets.instruction("No connection detected. Proceed to add a new connection.")

    def _set_connection(self):
        connection_info = self.connections[0]
        self.pvsadmin.set_connection(connection_info)


class EstablishConnection(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'establish-connection'
        self.pvsadmin = controller

        # OBJECTS
        self.__display_0 = cli.objects.Display('Establishing connection...',
                                               command=cli.objects.Command(self._execute, respond=True))
        self.__prompt_0 = cli.objects.Prompt('Connection failed because of the above exception. What would you like '
                                             'to do?')
        # NODES
        self.__node_F = cli.LinkNode(self.__display_0, name=f'{name}-execute')
        self.__node_0 = cli.LinkNode(self.__prompt_0, self.__node_F, name=f'{name}-failure')
        self.__node_L = cli.LinkNode(cli.objects.Command())

        # CONFIGURATIONS
        self.__prompt_0.options = {
            '1': cli.objects.Command(self.__node_0.set_next, next_node=self.__node_F, value='Try Again')}

        if parent:
            self.__node_0.adopt(parent)
            self.__prompt_0.options.update(
                {'R': cli.objects.Command(self.__node_0.set_next, next_node=parent, value='Return')})

        self.__node_0.adopt(self.__node_F)
        self.__node_F.adopt(self.__node_L)

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _execute(self):
        success, message = self.pvsadmin.establish_connection()

        if success:
            self.__node_F.set_next(self.__node_L)
            return cli.format.Presets.success(message)
        else:
            self.__node_F.set_next(self.__node_0)
            return cli.format.Presets.error(message)


class IncumbentQuery(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'incumbent-select'
        self.query_tool = controller

        # OBJECTS
        self.__prompt_0 = cli.objects.Prompt("Which of the following information do you have?")
        self.__prompt_1 = cli.objects.Prompt("Which of the following office(s) are of these incumbents?")
        self.__prompt_2 = cli.objects.Prompt("Which of the following office type(s) are of these incumbents?")
        self.__prompt_3 = cli.objects.Prompt("Active year(s) of incumbents ('-' in between years to denote range)",
                                             verification=self.is_validyear)
        self.__prompt_4 = cli.objects.Prompt("Which of the following state(s) are of these incumbents")
        self.__prompt_5 = cli.objects.Prompt("Proceed with the changes?")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt_0, name=f'{name}_office-choice', clear_screen=True)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_F, name=f'{name}_office-id')
        self.__node_2 = cli.LinkNode(self.__prompt_2, self.__node_F, name=f'{name}_office-types')
        self.__node_3 = cli.LinkNode(self.__prompt_3, self.__node_2, name=f'{name}_year')
        self.__node_4 = cli.LinkNode(self.__prompt_4, self.__node_3, name=f'{name}_states')
        self.__node_L = cli.LinkNode(self.__prompt_5, self.__node_4, name=f'{name}_confirm')

        self.__node_1.adopt(self.__node_3)

        # CONFIGURATIONS
        self.__prompt_0.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Office ID", next_node=self.__node_1),
            '2': cli.objects.Command(self.__node_F.set_next, value="Office Types", next_node=self.__node_2)}

        self.__prompt_1.options = pvsadmin.tables.OFFICE
        self.__prompt_2.options = pvsadmin.tables.OFFICE_TYPE
        self.__prompt_4.options = pvsadmin.tables.STATES_BY_ABV

        self.__prompt_5.options = \
            {'1': cli.objects.Command(self._execute, value="Yes"),
             '2': cli.objects.Command(self.__node_L.set_next, value="No", next_node=self.__node_F)}

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _execute(self):

        office_ids = self.__prompt_1.response.split(',')
        office_types = self.__prompt_2.response.split(',')
        range_year = self.__prompt_3.response
        states = self.__prompt_4.response.split(',')

        if int(range_year.split('-')[0]) >= 2005:
            query = pvsadmin.queries.Incumbents(range_year, office_ids, office_types, states).by_congstatus()
        else:
            query = pvsadmin.queries.Incumbents(range_year, office_ids, office_types, states).by_electdates()

        self.query_tool = query

    @cli.objects.Command()
    def is_validyear(self, x):

        regex = r'(19[8-9][0-9]|20[0-9][0-9])[\-]' \
                r'(19[8-9][0-9]|20[0-9][0-9]|2100)|' \
                r'(19[8-9][0-9]|20[0-9][0-9]|2100)'

        return re.fullmatch(regex, x),


class ElectionCandidates(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):
        name = 'candidate-select'

        self.query_tool = controller

        # OBJECTS
        self.__prompt_0 = cli.objects.Prompt("Is this for a primary or a general election?")
        self.__prompt_1 = cli.objects.Prompt("Which of the following information do you have?")
        self.__prompt_2 = cli.objects.Prompt("Which of the following office(s) are of these candidates?")
        self.__prompt_3 = cli.objects.Prompt("Which of the following office types are of these candidates?")
        self.__prompt_4 = cli.objects.Prompt("What are the years of this election?", verification=self.is_validyear)
        self.__prompt_5 = cli.objects.Prompt("Which of the following state(s) are included in the scorecard?")
        self.__prompt_6 = cli.objects.Prompt("Confirm Changes?")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt_0, name=f'{name}_election-stage', clear_screen=True)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_F, name=f'{name}_office-choice')
        self.__node_2 = cli.LinkNode(self.__prompt_2, self.__node_1, name=f'{name}_office-id')
        self.__node_3 = cli.LinkNode(self.__prompt_3, self.__node_1, name=f'{name}_office-types')
        self.__node_4 = cli.LinkNode(self.__prompt_4, self.__node_3, name=f'{name}_year')
        self.__node_5 = cli.LinkNode(self.__prompt_5, self.__node_4, name=f'{name}_state')
        self.__node_L = cli.LinkNode(self.__prompt_6, self.__node_5, name=f'{name}_confirm')

        self.__node_2.adopt(self.__node_4)

        # CONFIGURATIONS
        self.__prompt_0.options = pvsadmin.tables.ELECTION_STAGE

        self.__prompt_1.options = {
            '1': cli.objects.Command(self.__node_1.set_next, value='Office ID', next_node=self.__node_2),
            '2': cli.objects.Command(self.__node_1.set_next, value='Office Types', next_node=self.__node_3)}

        self.__prompt_2.options = pvsadmin.tables.OFFICE
        self.__prompt_3.options = pvsadmin.tables.OFFICE_TYPE
        self.__prompt_5.options = pvsadmin.tables.STATES_BY_ABV

        self.__prompt_6.options = {
            '1': cli.objects.Command(self._execute, value="Yes"),
            '2': "No"}

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _execute(self):
        election_years = self.__prompt_4.response.split(',')
        election_stages = self.__prompt_1.response.split(',')
        office_ids = self.__prompt_2.response.split(',')
        office_types = self.__prompt_3.response.split(',')
        states = self.__prompt_5.response.split(',')

        self.query_tool.query = pvsadmin.queries.ElectionCandidates(election_years, election_stages, office_ids,
                                                                    office_types, states).by_yoss()

    @cli.objects.Command()
    def is_validyear(self, x):
        regex = r'(19[8-9][0-9]|20[0-9][0-9]|2100)'

        return re.fullmatch(regex, x),


if __name__ == "__main__":
    from database import connection

    n_1 = PVSAdminMenu(pvsadmin.PVSAdmin(), connection_manager=connection.ConnectionManager())

    e = cli.Engine(n_1.first_node())
    e.run()
