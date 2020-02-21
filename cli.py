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
        super(CustomHelpFormatter, self).__init__(
            prog, max_help_position=80, width=80)


# =================================
# =           FUNCTIONS           =
# =================================
def get_parser():
    """Return parser with arguments."""
    parser = argparse.ArgumentParser()
    parser.formatter_class = CustomHelpFormatter
    parser.description = """
Description:
   <Ideally one line description of the program>

"""
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s: {__version__}')

    parser.add_argument('--details', dest='details', action='store_true',
                        help="Optional... Show details when listing repos/orgs")

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--list', dest='list_repo', nargs='*', type=str,
                       action=required_length(0, 1),
                       metavar=('username'),
                       help='Show all repositories [of entered <user>]')
    
    group.add_argument('--list_org', dest='list_org',
                       action="store_true",
                       help='Show all organizations')

    # group.add_argument('--list_org_repo', dest='list_org_repo', metavar='organization',
    #                    nargs=1, help='Show <organization> repositories.')

    # group.add_argument('--info', dest='info', action='store_true',
    #                    help='Show one-line description of <project_name>')

    # group.add_argument('--description', dest='description', action='store_true',
    #                    help='Edit description file of <project_name>')

    group.add_argument('--create', dest='create', nargs='*', type=str,
                       action=required_length(0, 3),
                       metavar=('repository', 'description'),
                       help='Create new remote [repository], [description], [user]')

    group.add_argument('--remove', dest='remove', nargs='+', type=str,
                       action=required_length(1, 2),
                       metavar=('repository', 'user'),
                       help='Remove remote <repository> [user]')

    group.add_argument('--create_org', dest='create_org', nargs='*', type=str,
                       action=required_length(0, 2),
                       metavar=('organization', 'description'),
                       help='Create new [organization], [description]')
    
    group.add_argument('--remove_org', dest='remove_org', nargs='+', type=str,
                       action=required_length(1, 1),
                       metavar=('organization'),
                       help='Remove remote <organization>')
    
    group.add_argument('--clone', dest='clone', nargs='+', type=str,
                       action=required_length(1, 2),
                       metavar=('repository', 'user'),
                       help='Clone existing <repository> [user] into current directory')

    # group.add_argument('--deploy', dest='deploy', action='store_true',
    #                    help='Deploy <project_name> to folder')

    # group.add_argument('--transfer', dest='transfer', action='store_true',
    #                    help='Transfer <project_name> to organization')

    return parser


def required_length(nmin, nmax):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin <= len(values) <= nmax:
                msg = f'argument "{self.dest}" requires between {nmin} and {nmax} arguments'
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
            # If user writes just: 'eve-git --create', return 'empty' string as argument
            if nmin == 0 and len(values) == 0:
                setattr(args, self.dest, 'empty')
    return RequiredLength
