"""Command Line Interface (CLI) Class"""

import argparse

# =================================
# =           CONSTANTS           =
# =================================
__author__ = "Jan Verner"
__email__ = "jverner@"
__date__ = "2020-02-07"
__version__ = "v0.0.0"


# ===============================
# =           CLASSES           =
# ===============================
class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    """ArgParse custom formatter that has LONGER LINES and RAW DescriptionHelp formatting, shows default values."""

    def __init__(self, prog):
        super(CustomHelpFormatter, self).__init__(prog, max_help_position=80, width=80)


# =================================
# =           FUNCTIONS           =
# =================================
def get_parser():
    """Return parser with arguments."""
    parser = argparse.ArgumentParser()
    parser.formatter_class = CustomHelpFormatter
    parser.description = """
<Ideally one line description of the program>

<
More description
with more lines
or examples
>
"""
    parser.add_argument('--version', action='version', version=f'%(prog)s: {__version__}')

    parser.add_argument('--no-groups', dest='no_groups', action='store_true',
                        help="Optional... <Don't show groups>")

    parser.add_argument('--no-color', dest='no_color', action='store_true',
                        help="Optional... <Don't show colors>")

    group = parser.add_mutually_exclusive_group()

    group.add_argument(dest='users', nargs='*', type=str.lower, default=[],
                       help='Optional... <Users>')

    group.add_argument('--img', dest='user_img', metavar='username', type=str.lower, default=None,
                       help='Optional... <Username (one) to show picture>')

    group.add_argument('--tel', dest='user_tel', nargs='+', metavar='username', type=str.lower, default=None,
                       help='Optional... <Username (one) to show telephone>')

    group.add_argument('--id', dest='user_id', nargs='+', metavar='username', type=str.lower, default=None,
                       help='Optional... <Username (one) to show user ID number>')

    group.add_argument('--all', dest='all_users', action='store_true',
                       help='Optional... <Show all people>')

    group.add_argument('--write-db', dest='write_db', action='store_true',
                       help='Developer only... <Save people into Pickled database>')

    group.add_argument('--list', dest='list_repo', metavar='username',
                       help='Show <username> repositories.')

    group.add_argument('--info', dest='info', action='store_true',
                       help='Show one-line description of <project_name>')

    group.add_argument('--description', dest='description', action='store_true',
                       help='Edit description file of <project_name>')

    group.add_argument('--create', dest='create', action='store_true',
                       help='Create new remote <project_name>')

    group.add_argument('--open', dest='open', action='store_true',
                       help='Clone existing <project_name> into current folder')

    group.add_argument('--deploy', dest='deploy', action='store_true',
                       help='Deploy <project_name> to folder')

    group.add_argument('--remove', dest='remove', action='store_true',
                       help='Remove remoted <project_name>')

    group.add_argument('--transfer', dest='transfer', action='store_true',
                       help='Transfer <project_name> to organization')

    return parser
