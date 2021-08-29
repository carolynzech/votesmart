class Text:
    END = '\033[0m'
    BOLD = '\033[1m'
    GREYED_OUT = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    FLIP = '\033[7m'
    TRANSPARENT = '\033[8m'


class TextColor:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    GREY = '\033[37m'
    DARK_GREY = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    VIOLET = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    WHITE = '\033[97m'


class BGColor:
    BLACK = '\033[40m'
    RED = '\033[41m'
    GREEN = '\033[42m'
    YELLOW = '\033[43m'
    BLUE = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN = '\033[46m'
    GREY = '\033[47m'
    DARK_GREY = '\033[100m'
    BRIGHT_RED = '\033[101m'
    BRIGHT_GREEN = '\033[102m'
    BRIGHT_YELLOW = '\033[103m'
    BRIGHT_BLUE = '\033[104m'
    BRIGHT_MAGENTA = '\033[105m'
    BRIGHT_CYAN = '\033[106m'
    WHITE = '\033[107m'


class Presets:

    @staticmethod
    def header(string):
        return Text.BOLD + Text.UNDERLINE + string + Text.END

    @staticmethod
    def description(string):
        return Text.ITALIC + BGColor.BLACK + string + Text.END

    @staticmethod
    def warning(string):
        return BGColor.YELLOW + TextColor.BLACK + Text.ITALIC + Text.BOLD + string + Text.END

    @staticmethod
    def error(string):
        return Text.BOLD + TextColor.BRIGHT_RED + string + Text.END

    @staticmethod
    def success(string):
        return Text.BOLD + TextColor.GREEN + string + Text.END

    @staticmethod
    def instruction(string):
        return Text.ITALIC + BGColor.CYAN + string + Text.END

    @staticmethod
    def question(string):
        return Text.BOLD + TextColor.CYAN + string + Text.END

    @staticmethod
    def unavailable(string):
        return Text.ITALIC + Text.GREYED_OUT + string + Text.END


if __name__ == '__main__':

    def demo(cls):
        only_class_attributes = [attr for attr in dir(cls) if not attr.startswith('__')]

        for attr in only_class_attributes:
            print(vars(cls)[attr] + str(attr) + Text.END)

    demo(Text)
    print('\n')

    demo(TextColor)
    print('\n')

    demo(BGColor)
    print('\n')
