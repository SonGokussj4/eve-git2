"""Command Line Interface (CLI) Class"""

import argparse
# import utils
import eve_git  # circular import...
import getpass
from colorama import Style, Fore


# =================================
# =           CONSTANTS           =
# =================================
__author__ = "Jan Verner"
__email__ = "jverner@"
__date__ = "2020-02-07"
__version__ = "v0.0.0"


# ==============================
# =           COLORS           =
# ==============================
RCol = Style.RESET_ALL
Red, BRed = Fore.RED, f'{Fore.RED}{Style.BRIGHT}'


# ===============================
# =           CLASSES           =
# ===============================
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        print(f"\n[ {BRed}ERROR{RCol} ] Err message bellow. Please read usage above.")
        raise SystemExit(f"[ {BRed}ERROR{RCol} ] {message}")


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

    # parser = argparse.ArgumentParser(parents=[common])
    parser = MyParser(parents=[common])

    # ===================================
    # =           MAIN PARSER           =
    # ===================================
    parser.formatter_class = CustomHelpFormatter
    parser.version = __version__
    parser.description = """
Description:
   <Ideally one line description of the program>

"""
    # OPTIONS
    parser.add_argument('--token', nargs='?', default=None, const='',
                        help='Add or Update your GITEA_TOKEN')

    # ==================================
    # =           SUBPARSERS           =
    # ==================================
    # https://pymotw.com/2/argparse/#nesting-parsers
    subparsers = parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # CLONE
    parser_clone = subparsers.add_parser('clone', parents=[common], help='Clone selected repo into current folder')
    parser_clone.add_argument('repository', help='Repository name')
    parser_clone.add_argument('username', nargs='?', help='Specify User/Org')
    parser_clone.formatter_class = CustomHelpFormatter
    parser_clone.set_defaults(func=eve_git.clone_repo)

    # LIST
    parser_list = subparsers.add_parser('list', help='List remote Repositories. Max 50 items displayed.', parents=[common])
    parser_list.add_argument('repository', nargs='?', default='', help='Help for <repository>')
    parser_list.add_argument('username', nargs='?', default='', help='Specify User/Org')
    parser_list.formatter_class = CustomHelpFormatter
    parser_list.set_defaults(func=eve_git.list_repo)

    # LIST_ORG
    parser_list_org = subparsers.add_parser('list_org', help='List remote Oranizations. (Admin only)', parents=[common])
    parser_list_org.set_defaults(func=eve_git.list_org)

    # CREATE
    parser_create = subparsers.add_parser('create', help='Create remote Repository (and clone it to current dir)', parents=[common])
    parser_create.add_argument('reponame', nargs='?', default='', help='Repository name')
    parser_create.add_argument('description', nargs='?', default=f'TODO: <Write project description>', help='New repo description')
    parser_create.add_argument('username', nargs='?', default=getpass.getuser(), help='Specify User/Org under which will it be created')
    parser_create.formatter_class = CustomHelpFormatter
    parser_create.set_defaults(func=eve_git.create_repo)

    # CREATE_ORG
    parser_create = subparsers.add_parser('create_org', help='Create remote Organization', parents=[common])
    parser_create.add_argument('organization', nargs='?', default='', help='Specify Organization')
    parser_create.add_argument('description', nargs='?', default=f'TODO: <Write organization description>', help='Help for <description>')
    parser_create.add_argument('fullname', nargs='?', default='', help='Help for <fullname>')
    parser_create.add_argument('visibility', nargs='?', default='public', help='Help for <visibility>')
    parser_create.formatter_class = CustomHelpFormatter
    parser_create.set_defaults(func=eve_git.create_org)

    # REMOVE
    parser_remove = subparsers.add_parser('remove', help='Remove remote Repository', parents=[common])
    parser_remove.add_argument('repository', help='Help for <repository>')
    parser_remove.add_argument('username', nargs='?', help='Specify User/Org')
    parser_remove.formatter_class = CustomHelpFormatter
    parser_remove.set_defaults(func=eve_git.remove_repo)

    # REMOVE_ORG
    parser_remove_org = subparsers.add_parser('remove_org', help='Remove remote Organization. Has to be empty.', parents=[common])
    parser_remove_org.add_argument('organization', nargs='?', help='Specify Organization')
    parser_remove_org.formatter_class = CustomHelpFormatter
    parser_remove_org.set_defaults(func=eve_git.remove_org)

    # EDIT
    parser_edit = subparsers.add_parser('edit', help='Edit remote repo Description', parents=[common])
    parser_edit.add_argument('repository', help='Help for <repository>')
    parser_edit.add_argument('username', nargs='?', help='Specify User/Org')
    parser_edit.formatter_class = CustomHelpFormatter
    parser_edit.set_defaults(func=eve_git.edit_desc)

    # CONNECT
    parser_connect = subparsers.add_parser('connect', help='Connect current repository to remote one', parents=[common])
    parser_connect.add_argument('repository', nargs='?', default='', help='Specify Repository to connect to')
    parser_connect.add_argument('remote_name', nargs='?', default='gitea', help='git remote add <remote_name>')
    parser_connect.formatter_class = CustomHelpFormatter
    parser_connect.set_defaults(func=eve_git.connect_here)

    # DEPLOY
    parser_deploy = subparsers.add_parser('deploy', help='Deploy selected repository to production', parents=[common])
    parser_deploy.add_argument('repository', help='Repository name')
    parser_deploy.add_argument('username', nargs='?', help='Specify User/Org')
    parser_deploy.add_argument('branch', nargs='?', default='master', help='Branch to deploy')
    parser_deploy.formatter_class = CustomHelpFormatter
    parser_deploy.set_defaults(func=eve_git.deploy)

    # TEMPLATE
    parser_template = subparsers.add_parser('template', help='Choose one of the templates and copy here.', parents=[common])
    # parser_template.add_argument('repository', help='Help for <repository>')
    # parser_template.add_argument('username', nargs='?', help='Specify User/Org')
    # parser_template.add_argument('branch', nargs='?', default='master', help='Help for <branch>')
    parser_template.formatter_class = CustomHelpFormatter
    parser_template.set_defaults(func=eve_git.templates)

    # SUB-TEMPLATE?
    sub_template = parser_template.add_subparsers(title='commands', dest='command', metavar="<command>")
    sub_template_dev = sub_template.add_parser('dev', parents=[common], help='Clone selected repo into current folder')
    sub_template_dev.add_argument('file', nargs='?', const='templates-eve-git.settings', help='Get eve-git.settings')

    # group = parser.add_mutually_exclusive_group()

    # group.add_argument('--info', dest='info', action='store_true',
    #                    help='Show one-line description of <project_name>')

    parser.epilog = "--- Arguments common to all sub-parsers ---" \
        + common.format_help().replace(common.format_usage(), '')

    return parser


# def required_length(nmin, nmax):
#     class RequiredLength(argparse.Action):
#         def __call__(self, parser, args, values, option_string=None):
#             if not nmin <= len(values) <= nmax:
#                 msg = f'argument "{self.dest}" requires between {nmin} and {nmax} arguments'
#                 raise argparse.ArgumentTypeError(msg)
#             setattr(args, self.dest, values)
#             # If user writes just: 'eve-git --create', return 'empty' string as argument
#             if nmin == 0 and len(values) == 0:
#                 setattr(args, self.dest, 'empty')
#     return RequiredLength
