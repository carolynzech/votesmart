import sys
import os
import re
from tkinter import filedialog
from tkinter import *

sys.path.append(os.path.dirname(os.path.abspath('../')))

from interface import cli
from ratings.harvest import harvest
from database.pvsadmin import tables


class HarvestMenu(cli.LinkNodeBundle):
    """All the necessary prompts and nodes to import the worksheet file to the application."""

    def __init__(self, controller, parent=None):

        name = 'harvest-menu'
        self.ratings_harvest = controller

        self.__display_0 = cli.objects.Display('Welcome to the Harvester!')

        self.__prompt_0 = cli.objects.Display('Select the worksheet file',
                                              command=cli.objects.Command(self._execute, respond=True))

        self.__prompt_1 = cli.objects.Prompt("You didn't choose a worksheet file. What would you like to do?")

        self.__prompt_2 = cli.objects.Prompt('Enter the filepath for the worksheet',
                                             command=cli.objects.Command(self._set_filepath_manual, respond=True),
                                             verification=cli.objects.Command(os.path.isfile))
        self.__prompt_2.error_msg = 'Input must be a valid absolute filepath.'

        self.__display = cli.objects.Display("Accessing file...")

        self.__node_F = cli.LinkNode(self.__display_0, name=f'{name}_welcome', show_instructions=False)
        self.__node_0 = cli.LinkNode(self.__prompt_0, self.__node_F, name=f'{name}_select', show_instructions=False)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_0, name=f'{name}_empty')
        self.__node_2 = cli.LinkNode(self.__prompt_2, self.__node_1, name=f'{name}_manual')
        self.__node_L = cli.LinkNode(self.__display, name=f'{name}_display', show_instructions=False)

        self.__node_0.adopt(self.__node_L)
        self.__node_1.adopt(self.__node_L)
        self.__node_1.adopt(self.__node_0)
        self.__node_2.adopt(self.__node_L)

        self.__prompt_1.__options({'1': cli.objects.Command(self.__node_1.set_next, next_node=self.__node_0,
                                                            value='Go back to file window and try again'),
                                     '2': cli.objects.Command(self.__node_1.set_next, next_node=self.__node_2,
                                                              value='Enter the filepath manually')})

        super().__init__(name, first_node=self.__node_F, last_node=self.__node_L, parent=parent)

    def _execute(self):
        tk = Tk()
        tk.withdraw()
        self.ratings_harvest.import_filepath = filedialog.askopenfilename()
        tk.destroy()

        if self.ratings_harvest.import_filepath:
            self.__node_0.set_next(self.__node_L)
            return f"Worksheet filepath: {self.ratings_harvest.import_filepath}"
        else:
            self.__node_0.set_next(self.__node_1)
            return ''

    def _set_filepath_manual(self):
        self.ratings_harvest.import_filepath = self.__prompt_2.get_user_response()
        return f"Worksheet filepath: {self.ratings_harvest.import_filepath}"


class HarvestImportWorksheetBundle(cli.LinkNodeBundle):
    """Import file and check for duplicates or blanks"""

    def __init__(self, controller, parent=None):

        name = 'harvest-import-worksheet-bundle'
        self.ratings_harvest = controller

        self.__display_0 = cli.objects.Display("Importing Worksheet...",
                                               command=cli.objects.Command(self._execute))

        self.__display_1 = cli.objects.Display('Checking for duplicates and blanks...',
                                               command=cli.objects.Command(self._dupes_blanks))

        self.__prompt = cli.objects.Prompt('')

        self.__table = cli.objects.SimpleTable([['Duplicates', 'Blanks']])
        self.__table.title = 'Duplicates and Blanks'
        self.__table.description = "The line numbers for the duplicate and blank candidate ids in the worksheet. " \
                                   "The line numbers for each duplicate id are grouped together."
        self.__table.table_padding = 2

        self.__display_2 = cli.objects.Display("Moving On...")

        self.__node_F = cli.LinkNode(self.__display_0, show_instructions=False, name=f'{name}_import')
        self.__node_0 = cli.LinkNode(self.__display_1, self.__node_F, show_instructions=False,
                                     name=f'{name}_dupes-blanks')
        self.__node_1 = cli.LinkNode(self.__table, self.__node_0, show_instructions=False,
                                     acknowledge=True, name=f'{name}_table')
        self.__node_2 = cli.LinkNode(self.__prompt, show_instructions=False, name=f'{name}_prompt')
        self.__node_L = cli.LinkNode(self.__display_2, show_instructions=False, name=f'{name}_moving-on')

        self.__node_F.adopt(self.__node_2)
        self.__node_0.adopt(self.__node_L)
        self.__node_1.adopt(self.__node_2)
        self.__node_2.adopt(self.__node_F)
        self.__node_2.adopt(self.__node_L)

        self.__prompt.__options({'1': cli.objects.Command(self.__node_2.set_next, value="Try Again",
                                                          next_node=self.__node_F),
                                   '2': cli.objects.Command(self.__node_2.set_next, value="Continue Without Fixing",
                                                            next_node=self.__node_L),
                                   '3': cli.objects.Command(sys.exit, value='Exit and try again later.')})

        super().__init__(name, first_node=self.__node_F, last_node=self.__node_L, parent=parent)

    def _dupes_blanks(self):

        dupes, blanks = self.ratings_harvest.get_dupe_blank()
        dupes_blanks_matrix = [['Duplicates'] + dupes, ['Blanks'] + blanks]
        self.__table.by_rows = True
        self.__table.matrix = dupes_blanks_matrix

        if len(dupes) > 0 or len(blanks) > 0 and self.ratings_harvest.all_cols_imported:
            self.__node_0.set_next(self.__node_1)
            self.__node_1.set_next(self.__node_2)
            self.__prompt.question = cli.format.Presets.error("There are some duplicates and/or blanks found. "
                                                              "What would you like to do?")
        else:
            self.__node_0.set_next(self.__node_L)

    def _execute(self):
        msg = self.ratings_harvest.read_worksheet()

        if self.ratings_harvest.all_cols_imported:
            self.__node_F.set_next(self.__node_0)
            self.__display_2.message = msg
        else:
            self.__node_F.set_next(self.__node_2)
            self.__prompt.question = cli.format.Presets.error(f"{msg} What would you like to do?")


class HarvesterFormBundle(cli.LinkNodeBundle):
    """Prompts and Nodes to fill the required columns of the Harvester eg. sig_id, span etc."""

    def __init__(self, controller, parent=None):

        name = 'harvester-form-bundle'
        self.ratings_harvest = controller

        self.__prompt_0 = cli.objects.Prompt('Which year(s) is the scorecard for?',
                                             verification=self.is_validyear)
        self.__prompt_0.error_msg = 'Input must be YYYY or YYYY-YYYY.'
        self.__prompt_1 = cli.objects.Prompt('What is the sig_id for this interest group?',
                                             verification=cli.objects.Command(re.fullmatch))
        self.__prompt_1.error_msg = 'Input must be a number.'
        self.__prompt_2 = cli.objects.Prompt('When was the rating session?')
        self.__prompt_3 = cli.objects.Prompt('What type of rating does the scorecard use?',
                                             command=cli.objects.Command(self._execute))

        options_2 = {'1': 'First Session', '2': 'Second Session', '3': 'Full Session', '4': 'Unknown'}
        options_3 = {'1': 'Numerical', '2': 'Letter Grade', '3': 'Rating Strings', '4': 'Open Format'}

        self.__prompt_2.__options(options_2)
        self.__prompt_3.__options(options_3)

        self.__node_F = cli.LinkNode(self.__prompt_0, name=f'{name}_year')
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_F, name=f'{name}_sig-id')
        self.__node_2 = cli.LinkNode(self.__prompt_2, self.__node_1, name=f'{name}_rating-session')
        self.__node_L = cli.LinkNode(self.__prompt_3, self.__node_2, acknowledge=True, name=f'{name}_rating-type')

        super().__init__(name, first_node=self.__node_F, last_node=self.__node_L, parent=parent)

    def _execute(self):
        matched_keys_session = dict(zip(self.__prompt_2.__options.keys(), tables.RATING_SESSION.keys()))
        matched_keys_format = dict(zip(self.__prompt_3.__options.keys(), tables.RATING_FORMAT.keys()))

        span = self.__prompt_0.get_user_response()
        sig_id = self.__prompt_1.get_user_response()
        rating_session = matched_keys_session[self.__prompt_2.get_user_response()]
        rating_format_id = matched_keys_format[self.__prompt_3.get_user_response()]

        self.ratings_harvest.generate_file(span, sig_id, rating_session, rating_format_id)

    @cli.objects.Command()
    def is_validyear(self, x):
        regex = r'(19[8-9][0-9]|20[0-9][0-9])[\-]' \
                r'(19[8-9][0-9]|20[0-9][0-9]|2100)|' \
                r'(19[8-9][0-9]|20[0-9][0-9]|2100)'

        return re.fullmatch(regex, x),


class HarvestExportBundle(cli.LinkNodeBundle):
    """Prompts and Nodes to export a harvest file to a chosen location"""

    def __init__(self, controller, parent=None):

        name = 'harvest-export-bundle'
        self.ratings_harvest = controller

        self.__display_0 = cli.objects.Display('Harvest file is ready to be exported, would like you to verify a few '
                                               'things...', )

        self.__display_1 = cli.objects.Display('Exporting file...',
                                               command=cli.objects.Command(self._execute, respond=True))

        self.__command = cli.objects.Command(self._update_questions)

        self.__prompt_0 = cli.objects.Prompt('')
        self.__prompt_1 = cli.objects.Prompt("What would you like to name your file?",
                                             command=cli.objects.Command(self._set_filename))

        self.__prompt_2 = cli.objects.Prompt('')
        self.__prompt_3 = cli.objects.Display('Where would you like to save your file instead?',
                                              command=cli.objects.Command(self._set_directory_tk))

        self.__prompt_4 = cli.objects.Prompt("You didn't choose a worksheet file. What would you like to do?")
        self.__prompt_5 = cli.objects.Prompt('Enter the directory',
                                             command=cli.objects.Command(self._set_directory_manual),
                                             verification=cli.objects.Command(os.path.isdir))
        self.__prompt_5.error_msg = 'Input must be a valid absolute directory path.'

        self.__node_F = cli.LinkNode(self.__display_0, show_instructions=False, clear_screen=True,
                                     name=f'{name}_welcome')
        self.__node_0 = cli.LinkNode(self.__command, self.__node_F, show_instructions=False, name=f'{name}_update-file')
        self.__node_1 = cli.LinkNode(self.__prompt_0, self.__node_0, name=f'{name}_confirm-filename')
        self.__node_2 = cli.LinkNode(self.__prompt_1, self.__node_1, name=f'{name}_new-filename')
        self.__node_3 = cli.LinkNode(self.__prompt_2, self.__node_0, name=f'{name}_confirm-directory')
        self.__node_4 = cli.LinkNode(self.__prompt_3, self.__node_3, name=f'{name}_new-directory',
                                     show_instructions=False)
        self.__node_5 = cli.LinkNode(self.__prompt_4, self.__node_3, name=f'{name}_empty')
        self.__node_6 = cli.LinkNode(self.__prompt_5, self.__node_5, name=f'{name}_manual')
        self.__node_L = cli.LinkNode(self.__display_1, show_instructions=False, acknowledge=True,
                                     name=f'{name}_export')

        self.__node_0.set_next(self.__node_1)
        self.__node_1.adopt(self.__node_3)
        self.__node_2.adopt(self.__node_0)
        self.__node_3.adopt(self.__node_L)
        self.__node_4.adopt(self.__node_0)
        self.__node_4.adopt(self.__node_5)
        self.__node_4.adopt(self.__node_L)
        self.__node_5.adopt(self.__node_4)
        self.__node_5.adopt(self.__node_L)
        self.__node_6.adopt(self.__node_L)

        self.__prompt_0.__options(
            {'1': cli.objects.Command(self.__node_1.set_next, value='Yes', next_node=self.__node_3),
             '2': cli.objects.Command(self.__node_1.set_next, value='No', next_node=self.__node_2)
             })

        self.__prompt_2.__options(
            {'1': cli.objects.Command(self.__node_3.set_next, value='Yes', next_node=self.__node_L),
             '2': cli.objects.Command(self.__node_3.set_next, value='No', next_node=self.__node_4)
             })

        self.__prompt_4.__options({'1': cli.objects.Command(self.__node_5.set_next, next_node=self.__node_4,
                                                            value='Go back to file window and try again'),
                                     '2': cli.objects.Command(self.__node_5.set_next, next_node=self.__node_6,
                                                              value='Enter the directory manually')})

        super().__init__(name, first_node=self.__node_F, last_node=self.__node_L, parent=parent)

    def _execute(self):
        user_filename_input = self.__prompt_1.get_user_response().strip()
        return cli.format.Presets.success(self.ratings_harvest.export(user_filename_input))

    def _update_questions(self):
        self.__prompt_0.question = f'Would you like {self.ratings_harvest.filename} to be the name of the file?'
        self.__prompt_2.question = f'Would you like to save your file to {self.ratings_harvest.directory}?'

    def _set_filename(self):
        self.ratings_harvest.filename = self.__prompt_1.get_user_response()
        self.__node_0.set_next(self.__node_1)

    def _set_directory_tk(self):
        tk = Tk()
        tk.withdraw()
        self.ratings_harvest.directory = filedialog.askdirectory(initialdir=self.ratings_harvest.directory)
        tk.destroy()

        self.__node_0.set_next(self.__node_3)

        if self.ratings_harvest.directory == '':
            self.__node_4.set_next(self.__node_5)
        else:
            self.__node_4.set_next(self.__node_L)

    def _set_directory_manual(self):
        self.ratings_harvest.directory = self.__prompt_5.get_user_response()


if __name__ == '__main__':
    h = harvest.HarvestFileGenerator()

    n_1 = HarvestMenu(h)
    n_2 = HarvestImportWorksheetBundle(h, parent=n_1.last_node())
    n_3 = HarvesterFormBundle(h, parent=n_2.last_node())
    n_4 = HarvestExportBundle(h, parent=n_3.last_node())

    engine = cli.Engine(n_1.first_node())
    engine.run()
