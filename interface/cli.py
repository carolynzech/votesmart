import sys
import os
from interface import cli


class Engine:

    """
    The engine object manages the link nodes of cli objects as to make traversing between them possible.
    There are also some features which the Engine class provides, such as allowing the user to restart, quit, get
    helpful instructions and traverse to previous nodes.
    """

    def __init__(self, node):

        self.current_node = node
        self.node_selection = [node]
        self.clear = 'cls' if os.name == 'nt' else 'clear'

        self.hideout_menu = cli.objects.Prompt("Hideout Menu")
        self.hideout_menu.options = \
            {'1': "Return",
             '2': cli.objects.Command(self.show_help, value="Help", respond=True),
             '3': cli.objects.Command(self.go_back_one, value="Go back one", respond=True),
             '4': cli.objects.Command(self.go_back_last_prompt, value="Go back to last prompt", respond=True),
             'R': cli.objects.Command(self.restart, value="Restart", respond=True),
             'Q': cli.objects.Command(self.quit, value="Quit")
             }

        self.restart_menu = cli.objects.Prompt("You have reached the end, start over?")
        self.restart_menu.options = {'1': cli.objects.Command(self.restart, value="Yes", respond=True),
                                     '2': cli.objects.Command(self.quit, value="No")}

    def go_back_one(self):

        if len(self.node_selection) > 1:
            self.node_selection.pop()
            self.current_node = self.node_selection[-1]

        return "Going Back..."

    def go_back_last_prompt(self):

        while len(self.node_selection) > 1:
            self.node_selection.pop()
            self.current_node = self.node_selection[-1]
            if isinstance(self.current_node.object, cli.objects.Prompt):
                break

        return "Going Back to Last Prompt..."

    def restart(self):
        self.current_node = self.node_selection[0]
        self.node_selection = [self.current_node]
        return "Restarting..."

    def quit(self):
        print("Quitting...")
        os.system(self.clear)
        sys.exit()

    def show_help(self):
        os.system(self.clear)
        print(self.current_node.help)
        _ = input("\nPress ENTER to continue")

    def run(self):

        while True:

            if self.current_node:
                print()

                if self.current_node.clear_screen:
                    os.system(self.clear)
                if self.current_node.show_instructions:
                    print("To open hideout menu, press Ctrl + C")

                try:
                    if self.current_node.object.exe_seq == 'before':
                        self.current_node.object.execute()
                        self.current_node.object.draw()
                    elif self.current_node.object.exe_seq == 'after':
                        self.current_node.object.draw()
                        self.current_node.object.execute()
                    else:
                        self.current_node.object.draw()

                    if self.current_node.acknowledge:
                        _ = input("\nPress ENTER to continue.")

                    if len(self.current_node.children) == 1:
                        self.current_node.next = next(iter(self.current_node.children.values()))

                    if self.current_node.next.id != self.current_node.id:
                        self.node_selection.append(self.current_node.next)

                    self.current_node = self.current_node.next

                except KeyboardInterrupt:
                    print()
                    while True:
                        try:
                            self.hideout_menu.draw()
                            break
                        except KeyboardInterrupt:
                            pass
            else:
                print()
                self.restart_menu.draw()


class LinkNode:

    """ The purpose of this class is to link multiple CliObjects together, and to be traversed via the Engine.
    """

    def __init__(self, object, parent=None, name='node', show_instructions=True, clear_screen=False, acknowledge=False):

        self.id = id(self)
        self.object = object
        self.name = object.name + '_' + name

        self.next = None
        self.__children = {}

        self.show_instructions = show_instructions
        self.clear_screen = clear_screen
        self.acknowledge = acknowledge
        self.help = """
                    """
        if parent:
            parent.adopt_node(self)

    def adopt(self, node):
        if node:
            self.__children[node.id] = node
        else:
            self.__children[None] = None

    def set_next(self, next_node):
        try:
            self.next = self.__children[id(next_node)] if next_node else None
        except KeyError:
            raise Exception(f"Node: {next_node.name} is not adopted by Node: {self.name}")

    @property
    def children(self):
        return self.__children


class LinkNodeBundle:

    def __init__(self, first_node, last_node, parent=None, name='bundle'):

        self.name = name
        self.__node_F = first_node
        self.__node_L = last_node

        if parent:
            parent.adopt_node(self.__node_F)

    def adopt(self, bundle):
        self.adopt_node(bundle.first_node)

    def adopt_node(self, node):
        self.__node_L.adopt_node(node)

    @property
    def first_node(self):
        return self.__node_F

    @property
    def last_node(self):
        return self.__node_L


class DummyLinkNode(LinkNode):
    def __init__(self, name='dummy-node', parent=None):
        super().__init__(cli.objects.Command(), name=name, show_instructions=False, parent=parent)
        self.object.name = 'dummy'
