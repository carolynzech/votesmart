import numpy as np
from abc import ABC, abstractmethod
from interface import cli
import time


class CliObject(ABC):
    """Abstract CliObject to be inherited by concrete objects; serves as a blueprint for CliObjects.

    Attributes
    __________
    name: str
        The name of the objects.
    command: Command
        Allow a CliObject ot carry a command.
    exe_seq: 'before' or 'after'
        Determines if a command execute before the object is drawn or after.

    Methods
    _______
    draw()
        Draws the object.
    execute()
        Execute the command the object holds.

    """

    def __init__(self, name, command, exe_seq):
        self.name = name
        self.command = command
        self.exe_seq = exe_seq

    @abstractmethod
    def draw(self):
        pass

    @abstractmethod
    def execute(self):
        pass


class Command(CliObject):
    """ The purpose of this command object is to allow objects to interact with a controller.

    Attributes
    __________
    method: function
        Holds a function or a method.
    value: str
        Display class as a string.
    respond: bool
        Prints return value of method if True.
    kwargs: dict
        Holds keyword arguments of method.

    Methods
    _______
    draw()
        Prints the message of the method's return value.
    execute()
        Executes the method, may also execute other command stored, thus creating a chain of command.

    As Decorator
    _________
    Command class can also be used as a decorator for functions and class methods, this will reduce the number of
    declared variables and shorten parameters.

    However, it is to be used with caution as it will cause an ambiguity if there are two instances of the same object.

    __method_cls_inst will only refer to the address of a subsequent instance, ignoring any instance preceding that. In
    other words, there can only be one namespace

    """

    def __init__(self, method=None, value='', respond=False, command=None, delay=0, **kwargs):

        super().__init__(name='command', command=command, exe_seq='before')

        self.method = method
        self.value = value
        self.respond = respond
        self.delay = delay
        self.kwargs = kwargs

        self.__method_cls_inst = None
        self.__message = ''

    def draw(self):
        if self.__message:
            print(self.__message)

        time.sleep(self.delay)

    def execute(self, *args):

        results = None

        if self.method:
            if self.__method_cls_inst:
                results = self.method(self.__method_cls_inst, *args, **self.kwargs)
            else:
                results = self.method(*args, **self.kwargs)

            if self.respond:
                self.__message = str(results)
                self.draw()

        if isinstance(self.command, Command):
            self.command.execute(*args)

        return results

    def __call__(self, method):
        self.method = method
        return self

    def __get__(self, instance, cls):
        self.__method_cls_inst = instance
        return self

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class Display(CliObject):
    """The purpose of this object is to display a single text message.

    Attributes
    __________
    message: str
        The message to be displayed when drawn.

    Methods
    _______
    draw():
        Prints the message.
    execute():
        Execute a given command.

    """

    def __init__(self, message, command=None):
        super().__init__(name='display', command=command, exe_seq='after')

        self.message = message

    def draw(self):
        print(self.message)

    def execute(self):
        if isinstance(self.command, Command):
            self.command.execute()


class Prompt(CliObject):
    """The purpose of the prompt object is to prompt user a question, then receiving, verifying and storing user inputs.

    Attributes
    __________
    question: str
        The message to prompt the user to input
    options: dict
        Gives the user options to pick based on the questions
    verification: Command
        Verifies the user input, prevents user from going forward if input not verified

    Methods
    _______
    draw():
        Prints the prompt and collects user inputs
    execute():
        Executes a given command.

    """

    def __init__(self, question, options=None, verification=None, command=None, multiple_selection=False):

        super().__init__(name='prompt', command=command, exe_seq='after')

        self.question = question
        self.options = options
        self.verification = verification
        self.multiple_selection = multiple_selection

        self.__responses = None
        self.__error_msg = "Your input(s) are not recognizable, please try again."

    @property
    def response(self):
        return self.__responses if self.multiple_selection else next(iter(self.__responses))

    def _verify(self):

        if isinstance(self.verification, Command):
            verified = []
            messages = []

            for response in self.__responses:
                boolean, *args = self.verification.execute(response)
                verified.append(boolean)
                messages.append(','.join(args))

            if messages:
                self.__error_msg = '\n'.join(messages)

            return all(verified)

        elif not self.verification and self.options:
            return all(response.strip().upper() in self.options.keys() for response in self.__responses)

        else:
            return True

    def draw(self):

        if self.multiple_selection:
            self.__responses = input(f"{str(self)}\n>> ").split(',')
        else:
            self.__responses = [input(f"{str(self)}\n>> ")]

        while not self._verify():
            if self.multiple_selection:
                self.__responses = input(f"{str(self)}\n{self.__error_msg}\n>> ").split(',')
            else:
                self.__responses = [input(f"{str(self)}\n{self.__error_msg}\n>> ")]

        if self.options:
            for r in self.__responses:
                if isinstance(self.options[r], Command):
                    self.options[r].execute()

    def execute(self):
        if isinstance(self.command, Command):
            self.command.execute()

    def __str__(self):

        if self.multiple_selection:
            question = self.question + cli.format.Text.ITALIC + " [multiple selection]" + cli.format.Text.END
        else:
            question = self.question

        options_msg = "Please enter one of the options above"
        options_str = '\n'.join([f'\t({str(k)}) {str(v)}' for k, v in self.options.items()]) if self.options else ''

        return f"{question}\n{options_str}\n{options_msg}" if self.options else question


class SimpleTable(CliObject):
    """
    The purpose of this table object is to tabulate a __matrix (2D array).

    Attributes
    __________
    title: str
        Defines what the table is about
    description: str
        Describes the contents in the table
    header: bool
        Gives the first row or column of table a rough border and bolded text

    Properties
    __________
    matrix: [[]]
        A 2D-array that defines the rows and columns of table
    by_rows:
        Determines which elements are drawn as headers
        if True, the elements in the first inner list are drawn as headers
        if False, the first element in each inner list are drawn as headers
    as_rows:
        Draws the table by the rows or if not by columns
    table_padding: int
        Provide white space surrounding the string; table-wide change
    table_alignment: 'R', 'L', 'C'
        Aligns the string to the right, left or center given the whitespace
    column_alignment: dict
        Individual column can be assigned a alignment
    column_paddings: dict
        Individual column is adjustable

    Methods
    _______
    draw():
        Draws the table together with title and description
    execute():
        Executes a command attached to the table
    reset():
        Resets any customized columns and assigned all columns with same padding and alignment
    refresh()
        Refreshes the table by keeping alignment and padding while allowing new items to append to matrix
    _transpose()
        Transposes the matrix when the matrix is arranged by rows
    _fill_blanks
        Fixes the matrix if it is of unequal length
    _cell_border
        generates a horizontal border around a cell
    _cell_wrap
        generates a cell with padded and aligned string
    _row_border
        generates a row of border based on the cell
    _row_wrap
        generates a row of wrapped cells
    """

    alignments = {'C': str.center, 'L': str.ljust, 'R': str.rjust}

    def __init__(self, matrix, by_rows=True, as_rows=True, header=True, command=None):

        super().__init__(name='table', command=command, exe_seq='before')

        self.title = ''
        self.description = ''
        self.header = header

        self.__matrix = [list(map(str, i)) for i in matrix]
        self.__by_rows = by_rows
        self.__as_rows = as_rows
        self.__original_shape = by_rows

        self._fill_blanks()

        self.__table_padding = 0
        self.__table_alignment = 'C'
        self.__column_widths = {i: len(max(col, key=len)) for i, col in enumerate(self.__matrix)}
        self.__column_alignments = {i: self.__table_alignment for i in range(len(self.__matrix))}
        self.__column_paddings = {i: self.__table_padding for i in range(len(self.__matrix))}

    def draw(self):
        print(cli.format.Presets.header(self.title.upper()))
        print(str(self))
        print(self.description)

    def execute(self):
        if isinstance(self.command, Command):
            self.command.execute()

    def reset(self):
        self._fill_blanks()

        self.__column_widths = {i: len(max(col, key=len)) for i, col in enumerate(self.__matrix)}
        self.__column_alignments = {i: self.__table_alignment for i in range(len(self.__matrix))}
        self.__column_paddings = {i: self.__table_padding for i in range(len(self.__matrix))}

        self.__by_rows = self.__original_shape

    def refresh(self):
        self._fill_blanks()

        a = len(self.__column_alignments) - 1 or len(self.__column_paddings) - 1 or len(self.column_widths) - 1
        b = len(self.__matrix)

        self.__column_widths = {i: len(max(col, key=len)) for i, col in enumerate(self.__matrix)}
        self.__column_alignments.update(
            {i: self.__table_alignment for i in range(a, b) if i not in self.__column_alignments.items()})
        self.__column_paddings.update(
            {i: self.__table_padding for i in range(a, b) if i not in self.__column_paddings.items()})

    @property
    def matrix(self):
        if self.__by_rows != self.__original_shape:
            self._transpose()

        return self.__matrix

    @matrix.setter
    def matrix(self, matrix):
        self.__matrix = [list(map(str, i)) for i in matrix]
        self._fill_blanks()
        self.reset()

    @property
    def by_rows(self):
        return self.__original_shape

    @by_rows.setter
    def by_rows(self, by_rows):
        self.__by_rows = by_rows
        self.__original_shape = by_rows

    @property
    def as_rows(self):
        return self.__as_rows

    @as_rows.setter
    def as_rows(self, as_row):
        if as_row != self.__as_rows:
            self.__as_rows = as_row
            self._transpose()

    @property
    def table_padding(self):
        return self.__table_padding

    @table_padding.setter
    def table_padding(self, length: int):
        self.__table_padding = length
        self.reset()

    @property
    def table_alignment(self):
        return self.__table_alignment

    @table_alignment.setter
    def table_alignment(self, alignment: str):
        if alignment in SimpleTable.alignments.keys():
            self.__table_alignment = alignment
            self.reset()
        else:
            raise Exception("Alignment has to be 'R' for right, 'L' for left and 'C' for center")

    @property
    def column_paddings(self):
        return self.__column_paddings

    @column_paddings.setter
    def column_paddings(self, padding: dict):
        self.__column_paddings.update(padding)

    @property
    def column_alignments(self):
        return self.__column_alignments

    @column_alignments.setter
    def column_alignments(self, alignment: dict):
        if set(alignment.values()).issubset(SimpleTable.alignments.keys()):
            self.__column_alignments.update(alignment)
        else:
            raise Exception("Alignment has to be 'R' for right, 'L' for left and 'C' for center")

    @property
    def column_widths(self):
        return self.__column_widths

    def _transpose(self):
        self.__by_rows = False if self.__by_rows else True
        self.__matrix = list(map(list, [*zip(*self.__matrix)]))
        self.refresh()

    def _fill_blanks(self):
        max_length = max(map(len, self.__matrix))

        for col in self.__matrix:
            for _ in range(max_length - len(col)):
                col.append(" ")

    def _cell_border(self, char, col_index):
        total_column_width = self.column_widths[col_index] + 2 * self.__column_paddings[col_index]

        return char * total_column_width

    def _cell_wrap(self, string, col_index):
        alignment = self.__column_alignments[col_index]
        total_column_width = self.column_widths[col_index] + 2 * self.__column_paddings[col_index]

        return SimpleTable.alignments[alignment](string, total_column_width)

    def _row_wrap(self, index):
        return [self._cell_wrap(str(cell), index) for cell in self.__matrix[index]]

    def _row_border(self, index):
        return [self._cell_border('═', index) if i < 1 and self.header else self._cell_border('─', index)
                for i in range(len(self.__matrix[index]))]

    def __str__(self):

        if self.__by_rows:
            self._transpose()

        wrapped_matrix = np.array([self._row_wrap(index) for index in range(len(self.__matrix))])
        horizontal_borders = np.array([self._row_border(index) for index in range(len(self.__matrix))])

        if (self.__original_shape and self.__as_rows) or (not self.__original_shape and not self.__as_rows):
            wrapped_matrix = wrapped_matrix.T
            horizontal_borders = horizontal_borders.T

        table = ['│{0}│'.format('│'.join(horizontal_borders[0]))]

        for i in range(len(wrapped_matrix)):
            table.append('│{0}│'.format('│'.join(wrapped_matrix[i])))
            table.append('│{0}│'.format('│'.join(horizontal_borders[i])))

        return '\n'.join(table)
