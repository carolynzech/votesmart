import os
import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilename

sys.path.append(os.path.dirname(os.path.abspath("../")))

from interface import cli
from database import dbtools_cli
from database.pvsadmin import pvsadmin_cli
from tools.pdext import pdext_cli


class RatingsMatchMenu(cli.LinkNodeBundle):

    def __init__(self, ratings_match, parent=None):
        name = 'ratings-match-menu'
        self.ratings_match = ratings_match

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Ratings Match Menu")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, name=name, clear_screen=True)
        self.__bundle_0 = ImportMatchMenu(self.ratings_match, parent=self.__node_F)
        self.__bundle_1 = pvsadmin_cli.PVSAdminMenu(self.ratings_match.database, self.ratings_match.connection_manager,
                                                    parent=self.__node_F)
        self.__bundle_2 = pdext_cli.ConfigureMatchMainMenu(self.ratings_match.pandas_matcher, parent=self.__node_F)
        self.__node_L = self.__node_F

        # CONFIGURATIONS
        self.__prompt.options = {'1': cli.objects.Command(self.__node_F.set_next, value="Import and Match",
                                                          next_node=self.__bundle_0.first_node()),
                                 '2': cli.objects.Command(self.__node_F.set_next, value="Configure PVSAdmin connection",
                                                          next_node=self.__bundle_1.first_node()),
                                 '3': cli.objects.Command(self.__node_F.set_next, value="Edit match configurations",
                                                          next_node=self.__bundle_2.first_node())}

        super().__init__(self.__node_F, self.__node_L, parent=parent)


class ImportMatchMenu(cli.LinkNodeBundle):

    def __init__(self, ratings_match, parent=None):

        name = 'import-and-match'
        self.ratings_match = ratings_match

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Select the following:", command=cli.objects.Command(self._feature_access))

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, name=f'{name}_menu', clear_screen=True)
        self.__bundle_0 = ImportRatingsWorksheet(self.ratings_match, parent=self.__node_F)
        self.__bundle_1 = DatabaseConfigurations(self.ratings_match, parent=self.__node_F)
        self.__bundle_2 = QueryAndExecution(self.ratings_match, parent=self.__bundle_1)
        self.__bundle_3 = MatchRatings(self.ratings_match, parent=self.__bundle_2)
        self.__node_L = self.__node_F

        self.__node_F.adopt(self.__node_F)
        self.__bundle_0.adopt_node(self.__node_F)
        self.__bundle_3.adopt_node(self.__node_F)

        # CONFIGURATIONS
        self.__prompt.options = {'1': cli.objects.Command(self.__node_F.set_next, value="Import worksheet",
                                                          next_node=self.__bundle_0.first_node()),
                                 '2': cli.objects.Command(self.__node_F.set_next, value="Match worksheet",
                                                          next_node=self.__bundle_1.first_node())}
        self.__prompt.exe_seq = 'before'

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt.options.update(
                {'R': cli.objects.Command(self.__node_F.set_next, value='Return', next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _feature_access(self):

        if self.ratings_match.is_worksheet():
            self.__prompt.options.update({'2': cli.objects.Command(self.__node_F.set_next, value="Match worksheet",
                                                                   next_node=self.__bundle_1.first_node())})

        else:
            self.__prompt.options.update({'2': cli.objects.Command(self.__node_F.set_next,
                                                                   value=cli.format.Presets.unavailable(
                                                                       "Match worksheet"),
                                                                   next_node=self.__node_F)})


class ImportRatingsWorksheet(cli.LinkNodeBundle):

    def __init__(self, ratings_match, parent=None):

        name = 'ratings-worksheet-import'
        self.ratings_match = ratings_match

        # OBJECTS
        self.__display_0 = cli.objects.Display("Opening FileDialog...",
                                               command=cli.objects.Command(self._set_file, respond=True))
        self.__prompt_0 = cli.objects.Prompt("Would you like to continue with the filepath?")
        self.__display_1 = cli.objects.Display("Importing File...",
                                               cli.objects.Command(self._import_file, respond=True))
        self.__prompt_1 = cli.objects.Prompt("Fail to import file, what would you like to do?")

        # NODES
        self.__node_F = cli.LinkNode(self.__display_0, name=f'{name}_file-dialog', acknowledge=True,
                                     show_instructions=False)
        self.__node_0 = cli.LinkNode(self.__prompt_0, name=f'{name}_confirm', parent=self.__node_F)
        self.__node_1 = cli.LinkNode(self.__display_1, name=f'{name}_import', parent=self.__node_0, acknowledge=True)
        self.__node_2 = cli.LinkNode(self.__prompt_1, name=f'{name}_fail-keeper', parent=self.__node_1)
        self.__node_L = cli.DummyLinkNode()

        self.__node_F.adopt(self.__node_F)
        self.__node_0.adopt(self.__node_1)
        self.__node_0.adopt(self.__node_F)
        self.__node_1.adopt(self.__node_L)
        self.__node_2.adopt(self.__node_F)
        self.__node_2.adopt(self.__node_1)

        # CONFIGURATIONS
        self.__prompt_0.options = {
            '1': cli.objects.Command(self.__node_0.set_next, value="Yes", next_node=self.__node_1),
            '2': cli.objects.Command(self.__node_0.set_next, value="No", next_node=self.__node_F)}

        self.__prompt_1.options = {
            '1': cli.objects.Command(self.__node_2.set_next, value="Try Again", next_node=self.__node_1),
            '2': cli.objects.Command(self.__node_2.set_next, value="Change filepath", next_node=self.__node_F)}

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt_1.options.update(
                {'3': cli.objects.Command(self.__node_2.set_next, value="Return", next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _set_file(self):
        tk = Tk()
        tk.withdraw()
        filepath = askopenfilename(filetypes=[('Spreadsheet files', '.ods .xlsx .xlsm .xlsb .odf .xls .odt')])
        tk.destroy()

        if not filepath:
            self.__node_F.set_next(self.__node_L)
            return f"Filepath is not set."
        else:
            self.ratings_match.import_filepath = filepath
            self.__node_F.set_next(self.__node_0)
            return f"Filepath is set to: {filepath}"

    def _import_file(self):
        success, message = self.ratings_match.import_worksheet()

        if success:
            self.__node_1.set_next(self.__node_L)
            return cli.format.Presets.success(message)
        else:
            self.__node_1.set_next(self.__node_2)
            return cli.format.Presets.error(message)


class DatabaseConfigurations(cli.LinkNodeBundle):

    def __init__(self, ratings_match, parent=None):

        name = 'database-configurations'

        self.ratings_match = ratings_match

        # OBJECTS
        self.__display = cli.objects.Display("Checking for previously assigned database connection...",
                                             command=cli.objects.Command(self._check_for_assigned_connection))
        self.__prompt = cli.objects.Prompt("Remember this connection?")

        # NODES
        self.__node_F = cli.LinkNode(self.__display, name=f'{name}_db-config', acknowledge=True)
        self.__bundle_0 = pvsadmin_cli.ModifyConnection(self.ratings_match.database, self.ratings_match.connection_manager,
                                                        parent=self.__node_F)
        self.__node_0 = cli.LinkNode(self.__prompt, name=f'{name}_remember', parent=self.__bundle_0)
        self.__node_L = cli.DummyLinkNode(name=f'{name}_last', parent=self.__node_F)
        self.__node_F.adopt(self.__node_L)

        # CONFIGURATIONS
        self.__prompt.options = {
            '1': cli.objects.Command(self._remember_connection, value="Yes", respond=True),
            '2': "No"
        }

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _check_for_assigned_connection(self):
        connection_id = self.ratings_match.connection_usage.is_assigned('ratings-match')

        if connection_id:
            _, connection_info = self.ratings_match.connection_manager.select(str(connection_id))
            self.ratings_match.database.set_connection(connection_info)
            self.__node_F.set_next(self.__node_L)
        else:
            self.__node_F.set_next(self.__bundle_0.first_node())

    def _remember_connection(self):
        connection_info = self.__bundle_0.connections[0]
        message = self.ratings_match.connection_usage.assign('ratings-match', connection_info)
        return cli.format.Presets.description(message)


class QueryAndExecution(cli.LinkNodeBundle):

    def __init__(self, ratings_match, parent=None):
        name = 'query-and-execution'
        self.ratings_match = ratings_match

        # OBJECTS
        self.__prompt = cli.objects.Prompt("What type of scorecard is this?")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt)
        self.__bundle_0 = pvsadmin_cli.IncumbentQuery(self.ratings_match.database.query_tool, parent=self.__node_F)
        self.__bundle_1 = pvsadmin_cli.ElectionCandidates(self.ratings_match.database.query_tool, parent=self.__node_F)
        self.__bundle_2 = pvsadmin_cli.EstablishConnection(self.ratings_match.database)
        self.__bundle_3 = dbtools_cli.ExecuteQuery(self.ratings_match.database.query_tool, parent=self.__bundle_2)
        self.__bundle_4 = dbtools_cli.QueryMessages(self.ratings_match.database.query_tool, parent=self.__bundle_3)
        self.__node_L = self.__bundle_4.last_node()

        self.__bundle_0.adopt_node(self.__bundle_2.first_node())
        self.__bundle_1.adopt_node(self.__bundle_2.first_node())

        # CONFIGURATIONS
        self.__prompt.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value='Incumbent', next_node=self.__bundle_0.first_node()),
            '2': cli.objects.Command(self.__node_F.set_next, value='Candidate', next_node=self.__bundle_1.first_node())}

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)


class MatchRatings(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):
        name = 'match-ratings'
        self.ratings_match = controller

        # OBJECTS
        self.__prompt = cli.objects.Prompt("How would you like to configure your match",
                                           command=cli.objects.Command(self.ratings_match.setup))
        self.__display = cli.objects.Display("Begin Matching...", command=cli.objects.Command(self.ratings_match.match))
        self.__table = cli.objects.SimpleTable([['']], as_rows=False, command=cli.objects.Command(self.populate_table))

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt)
        self.__bundle_0 = pdext_cli.ConfigureMatchMainMenu(self.ratings_match.pandas_matcher, parent=self.__node_F)
        self.__node_0 = cli.LinkNode(self.__display, name=name, parent=self.__node_F)
        self.__node_L = cli.LinkNode(self.__table, name=f'{name}_results', parent=self.__node_0, acknowledge=True)

        self.__node_F.adopt(self.__node_0)

        # CONFIGURATIONS
        self.__prompt.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Use recommended configurations",
                                     command=cli.objects.Command(self.ratings_match.recommended_configurations),
                                     next_node=self.__node_0),
            '2': cli.objects.Command(self.__node_F.set_next, value="Use current configurations",
                                     next_node=self.__node_0),
            '3': cli.objects.Command(self.__node_F.set_next, "Edit match configurations",
                                     next_node=self.__bundle_0.first_node())}

        self.__prompt.exe_seq = 'before'

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def populate_table(self):
        header, values = list(self.ratings_match.results().keys()), list(self.ratings_match.results().values())
        self.__table.matrix = [header, values]


if __name__ == '__main__':
    from tools.pdext import PandasMatcher
    from ratings.match import RatingsMatch
    from database.pvsadmin import PVSAdmin
    from database.connection import ConnectionUsage, ConnectionManager

    pm = PandasMatcher()
    db = PVSAdmin()
    cm = ConnectionManager()
    cu = ConnectionUsage()

    rm = RatingsMatch(pm, db, cm, cu)

    n_1 = RatingsMatchMenu(rm)

    e = cli.Engine(n_1.first_node())
    e.run()
