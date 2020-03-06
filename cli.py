"""Command Line Interface (CLI) Class"""

import argparse
import utils
import eve_git
import getpass
# from eve_git import RCol, BWhi


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
            prog, max_help_position=80, width=120)

    # Remove unnecessary '<Commands>' line in '-h'
    # Source: https://stackoverflow.com/a/48051233/4574809
    def _format_action(self, action):
            result = super()._format_action(action)
            if isinstance(action, argparse._SubParsersAction):
                # fix indentation on first line
                return f"{self._current_indent * ' '}{result.lstrip()}"
            return result

    def _format_action_invocation(self, action):
        if isinstance(action, argparse._SubParsersAction):
            # remove metavar and help line
            return ""
        return super()._format_action_invocation(action)

    def _iter_indented_subactions(self, action):
        if isinstance(action, argparse._SubParsersAction):
            try:
                get_subactions = action._get_subactions
            except AttributeError:
                pass
            else:
                # remove indentation
                yield from get_subactions()
        else:
            yield from super()._iter_indented_subactions(action)


# =================================
# =           FUNCTIONS           =
# =================================
def get_parser():
    """Return parser with arguments."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('-v', action='count', default=None, help='Verbal')
    common.add_argument('-V', '--version', action='version', version=__version__)
#     # common.add_argument('--details', dest='details', action='store_true',
#     #                     help="Optional... Show details when listing repos/orgs")

    parser = argparse.ArgumentParser(parents=[common])
    subparsers = parser.add_subparsers(title='commands', dest='command', metavar="<command>")
    parser.formatter_class = CustomHelpFormatter

    parser.version = __version__
    parser.description = """
Description:
   <Ideally one line description of the program>

"""
    # https://pymotw.com/2/argparse/#nesting-parsers

    # ==================================
    # =           SUBPARSERS           =
    # ==================================

    # DEPLOY
    parser_deploy = subparsers.add_parser('deploy', help='Deploy all the things!!!', parents=[common])
    parser_deploy.add_argument('repository', help='Help for <repository>')
    parser_deploy.add_argument('username', nargs="?", default=getpass.getuser(), help='Help for <username>')
    parser_deploy.add_argument('branch', nargs="?", default='master', help='Help for <branch>')
    parser_deploy.formatter_class = CustomHelpFormatter

    # LIST
    parser_list = subparsers.add_parser('list', help='List all the things!!!', parents=[common])
    parser_list.add_argument('repository', nargs="?", default='', help='Help for <repository>')
    parser_list.add_argument('username', nargs="?", default='', help='Specify user/org')
    parser_list.formatter_class = CustomHelpFormatter
    parser_list.set_defaults(func=eve_git.list_repo)

    # REMOVE
    parser_remove = subparsers.add_parser('remove', help='Remove one thing!!!', parents=[common])
    parser_remove.add_argument('repository', help='Help for <repository>')
    parser_remove.add_argument('username', nargs="?", help='Specify user/org')
    # parser_remove.add_argument('username', nargs="?", default=getpass.getuser(), help='Specify user/org')
    parser_remove.formatter_class = CustomHelpFormatter
    parser_remove.set_defaults(func=eve_git.remove_repo)

    # LIST_ORG
    parser_list_org = subparsers.add_parser('list_org', help='List all the Orgs!!!', parents=[common])
    parser_list_org.set_defaults(func=eve_git.list_org)

    # CREATE
    parser_create = subparsers.add_parser('create', help='Create one thing!!!', parents=[common])
    parser_create.add_argument('reponame', help='Help for <repository>')
    parser_create.add_argument('description', nargs="?", default=f'TODO: <Write project description>', help='Help for <description>')
    parser_create.add_argument('username', nargs="?", default=getpass.getuser(), help='Help for <username>')
    parser_create.formatter_class = CustomHelpFormatter
    parser_create.set_defaults(func=eve_git.create_repo)

    group = parser.add_mutually_exclusive_group()

    # group.add_argument('--info', dest='info', action='store_true',
    #                    help='Show one-line description of <project_name>')

    # group.add_argument('--description', dest='description', action='store_true',
    #                    help='Edit description file of <project_name>')

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

    group.add_argument('--edit', dest='edit', nargs='+', type=str,
                       action=required_length(1, 2),
                       metavar=('repository', 'user'),
                       help='Edit description in existing <repository> [user].')

    parser.epilog = "--- Arguments common to all sub-parsers ---" \
        + common.format_help().replace(common.format_usage(), '')

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


# class VerboseStore(argparse.Action):
#     def __init__(self, option_strings, dest, nargs=None, **kwargs):
#         if nargs is not None:
#             raise ValueError('nargs not allowed')
#         super(VerboseStore, self).__init__(option_strings, dest, **kwargs)

#     def __call__(self, parser, namespace, values, option_string=None):
#         print('Here I am, setting the ' \
#               'values %r for the %r option...' % (values, option_string))
#         setattr(namespace, self.dest, values)
