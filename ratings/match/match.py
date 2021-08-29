import os
import sys
sys.path.append(os.path.dirname(os.path.abspath('../')))

from ratings import ratings


class RatingsMatch:

    def __init__(self, pandas_matcher, database, connection_manager, connection_usage):

        self.worksheet = ratings.ScorecardWorksheet()

        self.pandas_matcher = pandas_matcher
        self.database = database
        self.connection_manager = connection_manager
        self.connection_usage = connection_usage

        self.matched_worksheet = None
        self.__matchable_columns = ['lastname', 'firstname', 'middlename', 'suffix', 'nickname',
                                    'party', 'state', 'office', 'district']
        self.__unused_df = None

        self.import_filepath = ''
        self.export_filepath = ''

    def import_worksheet(self):
        try:
            self.__unused_df = self.worksheet.read(self.import_filepath)
            return True, f"Import Success! File has {len(self.worksheet.df)} row(s) and " \
                         f"{len(self.worksheet.df.columns)} column(s)."

        except FileNotFoundError:
            return False, f"Cannot find file with filepath:\n'{self.import_filepath}'."

        except ImportError:
            return False, f"Unrecognizable file. Valid file extensions: \
            {', '.join(['xls', 'xlsx', 'xlsm', 'xlsb', 'odf', 'ods', 'odt'])}."

    def is_worksheet(self):
        return True if not self.worksheet.df.empty else False

    def setup(self):
        self.pandas_matcher.match_to = self.worksheet.df
        self.pandas_matcher.match_from = self.database.query_tool.results_as_df()

    def recommended_configurations(self):
        self.pandas_matcher.optimize = True
        self.pandas_matcher.auto_optimize = False
        self.pandas_matcher.match_priority_by_column.update(
            {'middlename': ['fuzzy_partial', 'exact', 'fuzzy_simple', 'token_set'],
             'suffix': ['fuzzy_partial', 'token_set', 'fuzzy_simple', 'exact'],
             'party': ['token_set', 'fuzzy_partial', 'exact', 'fuzzy_simple'],
             'office': ['fuzzy_partial', 'exact', 'fuzzy_simple', 'token_set'],
             'district': ['token_set', 'fuzzy_partial', 'exact', 'fuzzy_simple']})

    def match(self):
        matchable_columns = ['lastname', 'firstname', 'middlename', 'suffix', 'nickname',
                             'party', 'state', 'office', 'district']
        self.pandas_matcher.match()

    def export_matched_worksheet(self):
        try:
            self.pandas_matcher.export(self.export_filepath)

        except FileNotFoundError:
            return f"Your file cannot be exported. Cannot find filepath:\n'{self.export_filepath}'"
