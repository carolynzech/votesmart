import os

from tools.pdext import pdext as pdext
from ratings import ratings


class HarvestFileGenerator:

    def __init__(self):

        self.__sh = ratings.ScorecardHarvest()
        self.filename = None
        self.directory = None
        self.worksheet_filepath = None
        self.all_cols_imported = False

    def read_worksheet(self):
        try:
            cols_not_found = self.__sh.read(self.worksheet_filepath)
            if len(cols_not_found) == 0:
                self.all_cols_imported = True
                return f"You have successfully imported the worksheet, only columns " \
                       f"{', '.join(['candidate_id', 'sig_rating', 'our_rating'])} will be taken."
            else:
                return f"WARNING: Imported worksheet without these columns: {', '.join(cols_not_found)}."

        except FileNotFoundError:
            return f"Cannot find file with filepath:\n'{self.worksheet_filepath}'."

        except ImportError:
            return f"Unrecognizable file. Valid file extensions: " \
                   f"{', '.join(['xls', 'xlsx', 'xlsm', 'xlsb', 'odf', 'ods', 'odt'])}."

    def generate_file(self, span, sig_id, rating_session, rating_format_id):

        self.__sh.set_cols(span, sig_id, rating_session, rating_format_id)
        self.__sh.generate()

        # Setting filename, and setting default directory with worksheet, subject to change
        worksheet_filename = os.path.basename(self.worksheet_filepath)
        i = worksheet_filename.find('Scorecard')

        self.filename = 'Scorecard-Harvest' if i == -1 else worksheet_filename[:i] + 'Scorecard-Harvest'
        self.directory = os.path.dirname(self.worksheet_filepath)

    def export(self, filename=''):

        if filename:
            self.filename = filename

        self.__sh.export(filepath=self.directory + '/' + self.filename + '.csv')

        return f"File exported to {self.directory} as {self.filename}.csv."

    def get_dupe_blank(self):
        dupes = pdext.analysis.get_dupe_index(self.__sh.df, 'candidate_id')
        blanks = pdext.analysis.get_blank_index(self.__sh.df, 'candidate_id')
        return dupes, blanks
