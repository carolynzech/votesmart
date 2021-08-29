import pandas


class ScorecardWorksheet:

    def __init__(self):

        self.columns = ['lastname', 'firstname', 'middlename', 'suffix', 'nickname',
                        'party', 'state', 'office', 'district',
                        'candidate_id', 'sig_rating', 'our_rating']

        self.df = pandas.DataFrame(columns=self.columns)

    def read(self, filepath):

        df = pandas.read_excel(filepath)

        recognized_columns = [cols for cols in self.columns if cols in df.columns]
        unused_columns = [cols for cols in df.columns if cols not in self.columns]

        self.df = df[recognized_columns]

        return df[unused_columns]

    def generate(self, rows=100):
        self.df = pandas.DataFrame(index=[i for i in range(0, rows)], columns=self.columns)

    def export(self, filepath):
        self.df.to_excel(filepath, index=False)

    def __dict__(self):
        return self.df.to_dict('records')

    def __repr__(self):
        return str(self.df)


class ScorecardHarvest:

    def __init__(self):

        self.span = ''
        self.sig_id = ''
        self.usesigrating = 'f'
        self.ratingsession = ''
        self.ratingformat_id = ''

        self.columns = ['candidate_id', 'sig_rating', 'our_rating',
                        'span', 'sig_id', 'usesigrating', 'ratingsession', 'ratingformat_id']

        self.df = pandas.DataFrame(columns=self.columns)

        self.__required_columns = ['candidate_id', 'sig_rating', 'our_rating']

    def read(self, filepath):

        df = pandas.read_excel(filepath)

        recognized_columns = [col for col in self.columns if col in df.columns]

        self.df = df[recognized_columns]
        columns_not_found = []

        if not set(self.__required_columns).issubset(recognized_columns):
            columns_found = [col for col in self.__required_columns if col in self.df.columns]
            columns_not_found = [col for col in self.__required_columns if col not in self.df.columns]

            temp_df = pandas.DataFrame(index=[i for i in range(0, len(self.df))], columns=columns_not_found)
            worksheet_df = self.df[columns_found]

            self.df = pandas.concat([temp_df, worksheet_df], axis=1)

        return columns_not_found

    def set_cols(self, span, sig_id, ratingsession, ratingformat_id):
        self.span = span
        self.sig_id = sig_id
        self.ratingsession = ratingsession
        self.ratingformat_id = ratingformat_id

    def generate(self):
        rows = len(self.df)
        df = pandas.DataFrame(index=[i for i in range(0, rows)], columns=self.columns)

        if not self.df.empty:
            df['candidate_id'] = self.df['candidate_id']
            df['sig_rating'] = self.df['sig_rating']
            df['our_rating'] = self.df['our_rating']

        df['span'] = [self.span] * rows
        df['sig_id'] = [self.sig_id] * rows
        df['usesigrating'] = [self.usesigrating] * rows
        df['ratingsession'] = [self.ratingsession] * rows
        df['ratingformat_id'] = [self.ratingformat_id] * rows

        self.df = df

    def export(self, filepath):
        self.df.to_csv(filepath, index=False)

    def __dict__(self):
        return self.df.to_dict('records')

    def __repr__(self):
        return str(self.df)
