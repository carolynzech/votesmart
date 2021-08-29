import pandas
from tqdm import tqdm
from fuzzywuzzy import fuzz
from tools import pdext


class PandasMatcher:

    def __init__(self):

        # INITIALIZATION
        # _to is typically from the __worksheet, and _from is from the database results
        self.match_to = pandas.DataFrame()
        self.match_from = pandas.DataFrame()

        self.__algo = {'exact': self._exact,
                       'fuzzy_simple': self._fuzzy_simple,
                       'fuzzy_partial': self._fuzzy_partial,
                       'token_set': self._token_set}

        # CONFIGURATIONS
        self.optimize = True
        self.auto_optimize = False
        self.fuzzy_threshold = 0.75
        self.partial_fuzzy_threshold = 0.75
        self.token_set_threshold = 0.75
        self.total_threshold = 0.80
        self.optimize_threshold = 0.50
        self.match_priority_default = ['exact', 'fuzzy_simple', 'fuzzy_partial', 'token_set']
        self.columns_to_match = {}

        # {column_1: [customized_priority], column_2: [default_priority]...}
        self.match_priority_by_column = {}

        self.__uniqueness_to = {}
        self.__uniqueness_from = {}

        # RESULTS
        self.__matched = {}
        self.__matched_df = pandas.DataFrame()
        self.__total_count = 0
        self.__total_matched_count = 0
        self.__pass_matched_count = 0
        self.__review_matched_count = 0

    @staticmethod
    def _exact(cell_to, cell_from):
        return 1.0 if cell_to == cell_from else 0.0

    def _fuzzy_simple(self, cell_to, cell_from):
        score = float(fuzz.ratio(cell_to, cell_from)) / 100
        return score if score > self.fuzzy_threshold else 0.0

    def _fuzzy_partial(self, cell_to, cell_from):
        score = float(fuzz.partial_ratio(cell_to, cell_from)) / 100
        return score if score > self.partial_fuzzy_threshold else 0.0

    def _token_set(self, cell_to, cell_from):
        score = float(fuzz.token_set_ratio(cell_to, cell_from)) / 100
        return score if score > self.token_set_threshold else 0.0

    def _cell_score(self, cell_to, cell_from, columns):
        priority = self.match_priority_by_column[columns] if columns in self.match_priority_by_column.keys() \
                                                          else self.match_priority_default
        for algo_name in priority:
            cell_score = self.__algo[algo_name](cell_to, cell_from)

            if cell_score:
                return algo_name, cell_score

        return 'unmatched', float(0)

    def _row_score(self, row_to, row_from):
        row_score = {}
        row_algo = {}

        for column, u in self.__uniqueness_to.items():
            algo_name, score = self._cell_score(row_to[column], row_from[column], column)
            row_score[column] = score * u
            row_algo[column] = algo_name

        return row_score, row_algo

    def setup(self, columns):

        self.match_to = self.match_to.astype('string').replace(pandas.NA, '')
        self.match_from = self.match_from.astype('string').replace(pandas.NA, '')

        # FIXME: Adjusted column accounts only for number of selected columns, where a correct match between two
        #        different column names will exceed the adjusted percentage.

        self.__uniqueness_to = pdext.analysis.adjusted_column_uniqueness(self.match_to, self.columns_to_match.keys())
        self.__uniqueness_from = pdext.analysis.adjusted_column_uniqueness(self.match_from, self.columns_to_match.keys())

        if self.auto_optimize:
            self.optimize_threshold = max(self.__uniqueness_to)

        if not self.optimize:
            self.optimize_threshold = self.total_threshold

    def match(self):

        for index_to in tqdm(range(0, len(self.match_to)), desc="Progress"):

            # {row_1: {column_1: score_1, column_2: score_2...}, row_2:{...}}
            passable_matches_row_score = {}
            # {row_1: {column_1: score_1, column_2: score_2...}, row_2:{...}}
            passable_matches_algo = {}
            # {row_1: sum_score_1, row_2: sum_score_2...}
            passable_matches_row_score_sum = {}

            for index_from in tqdm(range(0, len(self.match_from)), leave=False, desc="Matching"):
                row_score, row_algo = self._row_score(self.match_to.iloc[index_to],
                                                      self.match_from.iloc[index_from])
                row_score_sum = sum(row_score.values())

                if row_score_sum >= self.optimize_threshold:
                    passable_matches_row_score[index_from] = row_score
                    passable_matches_algo[index_from] = row_algo
                    passable_matches_row_score_sum[index_from] = row_score_sum

            top_matches = {}

            if passable_matches_row_score_sum:
                for k in self.highest(passable_matches_row_score_sum):
                    status = 'MATCHED' if passable_matches_row_score_sum[k] >= self.total_threshold else 'REVIEW'
                    top_matches[k] = {'row_score_sum': passable_matches_row_score_sum[k],
                                      'row_score': passable_matches_row_score[k],
                                      'row_algo': passable_matches_algo[k],
                                      'match_status': status}

            self.__matched[index_to] = top_matches
            self.__total_count = len(self.match_to)

    def apply_to_columns(self, columns):

        """Copies matched column data from match_from to match_to, overwrites data in match_to"""

        self.__matched_df = self.match_to

        for index_to, top_matches in self.__matched.items():

            if len(top_matches) == 1:
                i = next(iter(top_matches))

                for column in columns:
                    self.__matched_df.at[index_to, column] = self.match_from.at[i, column]

                self.__matched_df.at[index_to, 'matched_row'] = i + 2
                self.__matched_df.at[index_to, 'match_score'] = top_matches[i]['row_score_sum']
                self.__matched_df.at[index_to, 'match_status'] = top_matches[i]['match_status']

            elif len(top_matches) >= 1:
                i = ', '.join(top_matches.keys())

                self.__matched_df.at[index_to, 'matched_row'] = i
                self.__matched_df.at[index_to, 'match_status'] = 'AMBIGUOUS MATCH'

            else:
                self.__matched_df.at[index_to, 'match_status'] = 'UNMATCHED'

    def results_description(self):
        return {"Total number of rows": self.__total_count,
                "Number of total matches": self.__total_matched_count,
                "Matches passed": self.__pass_matched_count,
                "Matches needs review": self.__review_matched_count}

    @property
    def matched_df(self):
        return self.__matched_df

    def get_algo_breakdown(self):
        pass

    def get_score_breakdown(self):
        pass

    def export(self, filepath):
        if not self.__matched_df.empty:
            self.__matched_df.to_excel(filepath)

    def swap_priority(self, swap_from, swap_to, column=None):
        if column:
            self.match_priority_by_column[column][swap_from], self.match_priority_by_column[column][swap_to] = \
                self.match_priority_by_column[column][swap_to], self.match_priority_by_column[column][swap_from]
        else:
            self.match_priority_default[swap_from], self.match_priority_default[swap_to] = \
                self.match_priority_default[swap_to], self.match_priority_default[swap_from]

    @staticmethod
    def highest(y):
        return [k for k, v in y.items() if v == max(y.values())]
