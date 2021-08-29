import os
import sys

sys.path.append(os.path.dirname(os.path.abspath("../")))

from interface import cli
from tools.pdext import pdext


class ConfigureMatchMainMenu(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):
        name = 'configure-match-menu'
        self.pandas_matcher = controller

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Configuration Menu")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, clear_screen=True)
        self.__node_0 = ConfigureMatchBasic(self.pandas_matcher, parent=self.__node_F)
        self.__node_1 = ConfigureMatchAdvanced(self.pandas_matcher, parent=self.__node_F)
        self.__node_L = self.__node_F

        # CONFIGURATIONS
        self.__prompt.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Basic configurations",
                                     next_node=self.__node_0.first_node()),
            '2': cli.objects.Command(self.__node_F.set_next, value="Advanced configurations",
                                     next_node=self.__node_1.first_node()),
            '3': cli.objects.Command(self.__node_F.set_next, value="Save Changes", next_node=parent),
            '4': cli.objects.Command(self.__node_F.set_next, value="Discard all changes", next_node=parent)}

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt.options.update(
                {'R': cli.objects.Command(self.__node_F.set_next, value='Return', next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)


class ConfigureMatchBasic(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'configure-match-basic'
        self.pandas_matcher = controller

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Basic Configurations")

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, clear_screen=True)
        self.__node_0 = ConfigureMatchThreshold(self.pandas_matcher, parent=self.__node_F)
        self.__node_L = self.__node_F

        self.__node_F.adopt(self.__node_L)
        self.__node_0.last_node().adopt_node(self.__node_L)

        # CONFIGURATIONS
        optimize_status = "Toggle Optimization (ON)" if self.pandas_matcher.optimize else \
            "Toggle Optimization (OFF)"

        auto_optimize_status = "Toggle Auto Optimization (ON)" if self.pandas_matcher.auto_optimize else \
            "Toggle Auto Optimization (OFF)"

        self.__prompt.options = {'1': cli.objects.Command(self.__node_F.set_next, value="Set Threshold",
                                                          next_node=self.__node_0.first_node()),
                                 '2': cli.objects.Command(self._toggle_optimization, value=optimize_status),
                                 '3': cli.objects.Command(self._toggle_auto_optimization, value=auto_optimize_status),
                                 }

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt.options.update(
                {'R': cli.objects.Command(self.__node_F.set_next, value="Return", next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent=parent)

    def _toggle_optimization(self):
        self.__node_F.set_next(self.__node_F)

        if self.pandas_matcher.optimize:
            self.pandas_matcher.optimize = False
            self.__prompt.options['2'].value = "Toggle Optimization (OFF)"
            return 'Optimization has been turned OFF'
        else:
            self.pandas_matcher.optimize = True
            self.__prompt.options['2'].value = "Toggle Optimization (ON)"
            return 'Optimization has been turned ON'

    def _toggle_auto_optimization(self):
        self.__node_F.set_next(self.__node_F)

        if self.pandas_matcher.auto_optimize:
            self.pandas_matcher.auto_optimize = False
            self.__prompt.options['3'].value = "Toggle Auto Optimization (OFF)"
            return 'Auto-optimization has been turned OFF'
        else:
            self.pandas_matcher.auto_optimize = True
            self.__prompt.options['3'].value = "Toggle Auto Optimization (ON)"
            if not self.pandas_matcher.optimize:
                self._toggle_optimization()
            return 'Auto-optimization has been turned ON'


class ConfigureMatchAdvanced(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'configure-match-advanced'
        self.pandas_matcher = controller

        # OBJECTS
        self.__prompt = cli.objects.Prompt("Advanced Configurations", command=cli.objects.Command(self._feature_access))

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt, clear_screen=True)
        self.__node_0 = ConfigureMatchOrder(self.pandas_matcher, self.__node_F)
        self.__node_1 = ConfigureMatchColumnOrder(self.pandas_matcher, self.__node_F)
        self.__node_L = self.__node_F

        self.__node_0.last_node().adopt_node(self.__node_L)
        self.__node_1.last_node().adopt_node(self.__node_L)

        # CONFIGURATIONS
        self.__prompt.exe_seq = 'before'
        self.__prompt.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Configure default match order",
                                     next_node=self.__node_0.first_node()),
            '2': cli.objects.Command(self.__node_F.set_next,
                                     value="Configure match order by column",
                                     next_node=self.__node_1.first_node())
        }

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt.options.update(
                {'R': cli.objects.Command(self.__node_F.set_next, value="Return", next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _feature_access(self):
        if not self.pandas_matcher.match_to.empty:
            self.__prompt.options.update({'2': cli.objects.Command(self.__node_F.set_next,
                                                                   value="Configure match order by column",
                                                                   next_node=self.__node_1.first_node())})
        else:
            if '2' in self.__prompt.options.keys():
                self.__prompt.options.pop('2')


class ConfigureMatchThreshold(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'configure-match-threshold'
        self.pandas_matcher = controller

        # OBJECTS
        self.__table = cli.objects.SimpleTable([[' ']], command=cli.objects.Command(self._update_table), header=False)
        self.__prompt_0 = cli.objects.Prompt("Which threshold would you like to change?")
        self.__prompt_1 = cli.objects.Prompt("Enter new threshold value", verification=self._verify_threshold,
                                             command=cli.objects.Command(self._execute))

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt_0, name=f"{name}_choose", clear_screen=True)
        self.__node_0 = cli.LinkNode(self.__table, self.__node_F, name=name, acknowledge=True, clear_screen=True)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_0, name=f"{name}_set")
        self.__node_L = self.__node_F

        self.__node_F.adopt(self.__node_L)
        self.__node_0.adopt(self.__node_F)
        self.__node_1.adopt(self.__node_0)
        self.__node_1.adopt(self.__node_L)

        # CONFIGURATIONS
        self.__table.table_padding = 2
        self.__prompt_0.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value='Fuzzy', next_node=self.__node_0),
            '2': cli.objects.Command(self.__node_F.set_next, value='Partial Fuzzy', next_node=self.__node_0),
            '3': cli.objects.Command(self.__node_F.set_next, value='Token Set', next_node=self.__node_0),
            '4': cli.objects.Command(self.__node_F.set_next, value='Total', next_node=self.__node_0),
            '5': cli.objects.Command(self.__node_F.set_next, value='Optimized', next_node=self.__node_0),
        }
        self.__prompt_0.command = cli.objects.Command(self.__node_0.set_next, next_node=self.__node_1)

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt_0.options.update({'R': cli.objects.Command(self.__node_F.set_next, value="Return", next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):

        threshold_types = {'1': 'fuzzy_threshold',
                           '2': 'partial_fuzzy_threshold',
                           '3': 'token_set_threshold',
                           '4': 'total_threshold',
                           '5': 'optimize_threshold'}

        threshold_type = threshold_types[self.__prompt_0.get_user_response()]
        new_threshold = float(self.__prompt_1.get_user_response())

        exec("self.pandas_matcher.{0} = {1}".format(threshold_type, new_threshold))

        self.__node_0.set_next(self.__node_F)
        self.__node_1.set_next(self.__node_0)

    @cli.objects.Command
    def _verify_threshold(self, x):
        try:
            return True if 1 >= float(x) > 0 else False,
        except ValueError:
            return False,

    def _update_table(self):

        self.__table.matrix = [['Fuzzy', self.pandas_matcher.fuzzy_threshold],
                               ['Partial Fuzzy', self.pandas_matcher.partial_fuzzy_threshold],
                               ['Token Set', self.pandas_matcher.token_set_threshold],
                               ['Total', self.pandas_matcher.total_threshold],
                               ['Optimized', self.pandas_matcher.optimize_threshold]]

        self.__node_F.set_next(self.__node_L)


class ConfigureMatchOrder(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):

        name = 'configure-match-order'
        self.pandas_matcher = controller

        # OBJECTS
        self.__table = cli.objects.SimpleTable([[' ']], command=cli.objects.Command(self._update_table))
        self.__prompt_0 = cli.objects.Prompt("Select one of the following")
        self.__prompt_1 = cli.objects.Prompt("Select two positions to swap separated by a comma",
                                             command=cli.objects.Command(self._execute),
                                             verification=self._verify_swap)

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt_0, name=f"{name}_choose", clear_screen=True)
        self.__node_0 = cli.LinkNode(self.__table, self.__node_F, name=name, acknowledge=True, clear_screen=True)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_0, name=f"{name}_swap")
        self.__node_L = self.__node_F

        self.__node_F.adopt(self.__node_L)
        self.__node_0.adopt(self.__node_F)
        self.__node_1.adopt(self.__node_0)

        # CONFIGURATIONS
        self.__prompt_0.options = {
            '1': cli.objects.Command(self.__node_F.set_next, value="Swap match order", next_node=self.__node_0)}
        self.__prompt_0.command = cli.objects.Command(self.__node_0.set_next, next_node=self.__node_1)

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt_0.options.update({'R': cli.objects.Command(self.__node_F.set_next, value="Return", next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):
        swap_from, swap_to = map(int, self.__prompt_1.get_user_response().split('>'))
        self.pandas_matcher.swap_priority(swap_from - 1, swap_to - 1)

        self.__node_0.set_next(self.__node_F)
        self.__node_1.set_next(self.__node_0)

    @cli.objects.Command()
    def _verify_swap(self, x):
        swap_values = x.split('>')
        verification = ['1', '2', '3', '4']

        if 1 < len(swap_values) <= 2:
            if swap_values[0] in verification and swap_values[1] in verification:
                return True,
            elif swap_values[0] not in verification:
                return False, f"Swap from: {swap_values[0]} cannot be found."
            elif swap_values[1] not in verification:
                return False, f"Swap to: {swap_values[1]} cannot be found."

        elif len(swap_values) > 2:
            return False, "Too many swap values, only enter two value swap from and swap to separated by '>'. "
        else:
            return False, "Require both swap from and swap to values."

    def _update_table(self):
        p_list = self.pandas_matcher.match_priority_default
        self.__table.matrix = [['Match Order', 'Match Type']] + \
                              [[str(o), t] for o, t in enumerate(p_list, 1)]
        self.__node_F.set_next(self.__node_L)


class ConfigureMatchColumnOrder(cli.LinkNodeBundle):

    def __init__(self, controller, parent=None):
        name = 'configure-match-column-order'
        self.pandas_matcher = controller

        # OBJECTS
        self.__table = cli.objects.SimpleTable([[' ']], by_rows=False, as_rows=False,
                                               command=cli.objects.Command(self._update_table))
        self.__prompt_0 = cli.objects.Prompt("Select a column", command=cli.objects.Command(self._update_options))
        self.__prompt_1 = cli.objects.Prompt("Select two positions to swap separated by '>'",
                                             command=cli.objects.Command(self._execute),
                                             verification=self._verify_swap)

        # NODES
        self.__node_F = cli.LinkNode(self.__prompt_0, name=f"{name}_choose", clear_screen=True)
        self.__node_0 = cli.LinkNode(self.__table, self.__node_F, name=name, acknowledge=True, clear_screen=True)
        self.__node_1 = cli.LinkNode(self.__prompt_1, self.__node_0, name=f"{name}_swap")
        self.__node_L = self.__node_F

        self.__node_F.adopt(self.__node_L)
        self.__node_0.adopt(self.__node_F)
        self.__node_1.adopt(self.__node_0)

        # CONFIGURATIONS
        self.__prompt_0.options = {}
        self.__prompt_0.exe_seq = 'before'

        if parent:
            self.__node_F.adopt(parent)
            self.__prompt_0.options.update(
                {'R': cli.objects.Command(self.__node_F.set_next, value="Return", next_node=parent)})

        super().__init__(name, self.__node_F, self.__node_L, parent)

    def _execute(self):
        column = str(self.__prompt_0.options[self.__prompt_0.get_user_response()])

        swap_from, swap_to = map(int, self.__prompt_1.get_user_response().split('>'))
        self.pandas_matcher.swap_priority(swap_from - 1, swap_to - 1, column)

        self.__node_0.set_next(self.__node_F)
        self.__node_1.set_next(self.__node_0)

    @cli.objects.Command()
    def _verify_swap(self, x):
        swap_values = x.split('>')
        verification = ['1', '2', '3', '4']

        if 1 < len(swap_values) <= 2:
            if swap_values[0] in verification and swap_values[1] in verification:
                return True,
            elif swap_values[0] not in verification:
                return False, f"Swap from: {swap_values[0]} cannot be found."
            elif swap_values[1] not in verification:
                return False, f"Swap to: {swap_values[1]} cannot be found."

        elif len(swap_values) > 2:
            return False, "Too many swap values, only enter two value swap from and swap to separated by '>'. "
        else:
            return False, "Require both swap from and swap to values."

    def _update_options(self):
        option = {}

        for i, col in enumerate(self.pandas_matcher.match_to.columns, 1):
            option[str(i)] = cli.objects.Command(self.__node_F.set_next, value=col, next_node=self.__node_0)

        if option:
            self.__prompt_0.options.update(option)

        self.__node_0.set_next(self.__node_1)

    def _update_table(self):
        column = str(self.__prompt_0.options[self.__prompt_0.get_user_response()])
        if column not in self.pandas_matcher.match_priority_by_column.keys():
            self.pandas_matcher.match_priority_by_column.update(
                {column: list(self.pandas_matcher.match_priority_default)})

        p_tuples = self.pandas_matcher.match_priority_by_column.items()

        self.__table.matrix = [["Match Order", '1', '2', '3', '4']] + \
                              [[k] + v for k, v in p_tuples]

        self.__node_F.set_next(self.__node_L)


if __name__ == "__main__":
    pm = pdext.PandasMatcher()
    # pm.match_to = pandas.DataFrame([['1234', 'Smith']], columns=['candidate_id', 'lastname'])
    n_1 = ConfigureMatchMainMenu(pm)

    e = cli.Engine(n_1.first_node())
    e.run()
