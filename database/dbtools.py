import csv
import time
import pandas


class QueryTool:

    def __init__(self, adapter):

        self.connection_adapter = adapter

        self.__query = None
        self.__query_params = None
        self.__results = None

        self.__number_of_rows = 0
        self.__number_of_columns = 0
        self.__time_taken = 0

    @property
    def query(self):
        return self.__query

    @query.setter
    def query(self, q):
        if not isinstance(q, str):
            self.__query, self.__query_params = q
        else:
            self.__query = q

    def run(self):

        try:
            start = time.process_time()

            cursor = self.connection_adapter.execute(self.__query, self.__query_params)
            header = [str(k[0]) for k in cursor.description] if cursor else []
            rows = cursor.fetchall() if cursor else []

            end = time.process_time()

            cursor.close()

            self.__results = (header, rows)
            self.__time_taken = end - start
            self.__number_of_columns = len(header)
            self.__number_of_rows = len(rows)

        except Exception as e:
            self.__results = None
            self.__time_taken = 0
            self.__number_of_columns = 0
            self.__number_of_rows = 0
            return e

    @property
    def results(self):
        return self.__results

    def results_as_df(self):
        if self.__results:
            return pandas.DataFrame(self.__results[1], columns=self.__results[0])

    def export_as_csv(self, filename=''):
        filename = "Query_Results" if not filename else filename
        filename += '.csv'

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(self.__results)

    def message(self):
        return f"Query returns {self.__number_of_rows} rows, {self.__number_of_columns} columns.\n" \
               f"Time taken: {self.__time_taken}s"
