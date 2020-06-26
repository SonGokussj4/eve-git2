"""Command Line Interface (CLI) Class"""

import argparse
import eve_git  # circular import...
import getpass
from colorama import Style, Fore


# =================================
# =           CONSTANTS           =
# =================================
__author__ = "Jan Verner"
__email__ = "jverner@"
__date__ = "2020-06-26"
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
        print(f"\n[ {BRed}ERROR{RCol} ] Please read usage above.")
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
    parser.add_argument('--token', nargs='?', default=None, const='', help='Add or Update your GITEA_TOKEN')
    parser.add_argument('--bighelp', action='store_true', help='Show every possible command')

    # ==================================
    # =           SUBPARSERS           =
    # ==================================
    # https://pymotw.com/2/argparse/#nesting-parsers
    subparsers = parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # -----------  CLONE  -----------
    parser_clone = subparsers.add_parser('clone', parents=[common], help='Clone selected repo into current folder')
    parser_clone.add_argument('repository', help='Repository name')
    parser_clone.add_argument('username', nargs='?', help='Specify User/Org')
    parser_clone.formatter_class = CustomHelpFormatter
    parser_clone.set_defaults(func=eve_git.clone_repo)

    # -----------  LIST  -----------
    list_parser = subparsers.add_parser('list', help='List {repo/org}. Max 50 items displayed.', parents=[common])
    list_parser.formatter_class = CustomHelpFormatter
    list_parser.set_defaults(func=eve_git.list_arg)

    # {repo, org}
    list_subparsers = list_parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # list --> repo
    list_repo_parser = list_subparsers.add_parser('repo', help='List remote Repositories. Max 50 items displayed.', parents=[common])
    list_repo_parser.formatter_class = CustomHelpFormatter
    list_repo_parser.set_defaults(func=eve_git.list_repo_arg)
    list_repo_parser.add_argument('repository', nargs='?', default='', help='Help for <repository>')
    list_repo_parser.add_argument('username', nargs='?', default='', help='Specify User/Org')

    # list --> org
    list_org_parser = list_subparsers.add_parser('org', help='List remote Organizations. (Admin only)', parents=[common])
    list_org_parser.formatter_class = CustomHelpFormatter
    list_org_parser.set_defaults(func=eve_git.list_org_arg)

    # -----------  CREATE  -----------
    create_parser = subparsers.add_parser('create', help='Create {repo/org}', parents=[common])
    create_parser.formatter_class = CustomHelpFormatter
    create_parser.set_defaults(func=eve_git.create_arg)

    # {repo, org}
    create_subparsers = create_parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # create --> repo
    create_repo_parser = create_subparsers.add_parser('repo', help='Create Repository (and clone it to current dir)', parents=[common])
    create_repo_parser.add_argument('reponame', nargs='?', default='', help='Repository name')
    create_repo_parser.add_argument('description', nargs='?', default=f'TODO: <Write project description>', help='New repo description')
    create_repo_parser.add_argument('username', nargs='?', default=getpass.getuser(), help='Specify User/Org under which will it be created')
    create_repo_parser.formatter_class = CustomHelpFormatter
    create_repo_parser.set_defaults(func=eve_git.create_repo_arg)

    # create --> org
    create_org_parser = create_subparsers.add_parser('org', help='Create Organization', parents=[common])
    create_org_parser.add_argument('organization', nargs='?', default='', help='Specify Organization')
    create_org_parser.add_argument('description', nargs='?', default=f'TODO: <Write organization description>', help='Help for <description>')
    create_org_parser.add_argument('fullname', nargs='?', default='', help='Help for <fullname>')
    create_org_parser.add_argument('visibility', nargs='?', default='public', help='Help for <visibility>')
    create_org_parser.formatter_class = CustomHelpFormatter
    create_org_parser.set_defaults(func=eve_git.create_org_arg)

    # -----------  REMOVE  -----------
    remove_parser = subparsers.add_parser('remove', help='Remove {repo/org}', parents=[common])
    remove_parser.formatter_class = CustomHelpFormatter
    remove_parser.set_defaults(func=eve_git.remove_arg)

    # {repo, org}
    remove_subparsers = remove_parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # remove --> repo
    remove_repo_parser = remove_subparsers.add_parser('repo', help='Remove Repository', parents=[common])
    remove_repo_parser.add_argument('repository', nargs='?', help='Help for <repository>')
    remove_repo_parser.add_argument('username', nargs='?', help='Specify User/Org')
    remove_repo_parser.formatter_class = CustomHelpFormatter
    remove_repo_parser.set_defaults(func=eve_git.remove_repo_arg)

    # remove --> org
    remove_org_parser = remove_subparsers.add_parser('org', help='Remove Organization. Has to be empty.', parents=[common])
    remove_org_parser.add_argument('organization', nargs='?', help='Specify Organization')
    remove_org_parser.formatter_class = CustomHelpFormatter
    remove_org_parser.set_defaults(func=eve_git.remove_org_arg)

    # -----------  EDIT  -----------
    parser_edit = subparsers.add_parser('edit', help='Edit remote repo Description', parents=[common])
    parser_edit.add_argument('repository', nargs='?', help='Help for <repository>')
    parser_edit.add_argument('username', nargs='?', help='Specify User/Org')
    parser_edit.formatter_class = CustomHelpFormatter
    parser_edit.set_defaults(func=eve_git.edit_desc)

    # -----------  TRANSFER  -----------
    parser_transfer = subparsers.add_parser('transfer', help='Transfer repository to different owner (User/Org)', parents=[common])
    parser_transfer.add_argument('repository', nargs='?', default='', help='Specify Repository for transfer')
    parser_transfer.add_argument('username', nargs='?', default='', help='Specify owner (User/Org)')
    parser_transfer.add_argument('new_owner', nargs='?', default='', help='Specify target owner (User/Org)')
    parser_transfer.formatter_class = CustomHelpFormatter
    parser_transfer.set_defaults(func=eve_git.transfer_repo)

    # -----------  CONNECT  -----------
    parser_connect = subparsers.add_parser('connect', help='Connect current repository to remote one', parents=[common])
    parser_connect.add_argument('repository', nargs='?', default='', help='Specify repository name to connect to')
    parser_connect.add_argument('remote_name', nargs='?', default='gitea', help='Specify new <remote_name>')
    parser_connect.formatter_class = CustomHelpFormatter
    parser_connect.set_defaults(func=eve_git.connect_here)

    # -----------  DEPLOY  -----------
    parser_deploy = subparsers.add_parser('deploy', help='Deploy selected repository to production', parents=[common])
    parser_deploy.add_argument('repository', help='Repository name')
    parser_deploy.add_argument('username', nargs='?', help='Specify User/Org')
    parser_deploy.add_argument('branch', nargs='?', default='master', help='Branch to deploy')
    parser_deploy.formatter_class = CustomHelpFormatter
    parser_deploy.set_defaults(func=eve_git.deploy)

    # -----------  TEMPLATE  -----------
    parser_template = subparsers.add_parser('template', help='Choose one of the templates and copy here.', parents=[common])
    # parser_template.add_argument('repository', help='Help for <repository>')
    # parser_template.add_argument('username', nargs='?', help='Specify User/Org')
    # parser_template.add_argument('branch', nargs='?', default='master', help='Help for <branch>')
    parser_template.formatter_class = CustomHelpFormatter
    parser_template.set_defaults(func=eve_git.templates)

    # -----------  PYTHON  -----------
    python_parser = subparsers.add_parser('python', help='Python {teplate/venv}', parents=[common])
    python_parser.formatter_class = CustomHelpFormatter
    # parser_python.set_defaults(func=eve_git.python)

    # {template, venv}
    python_subparsers = python_parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # python --> template
    python_template_parser = python_subparsers.add_parser('template', help='Managing templates', parents=[common])
    python_template_parser.formatter_class = CustomHelpFormatter
    python_template_parser.set_defaults(func=eve_git.templates)
    # python_template_parser.add_argument('list', action="store_true", help='List possible python templates to download')

    # python --> venv
    python_venv_parser = python_subparsers.add_parser('venv', help='Manipulating with environments', parents=[common])
    python_venv_parser.formatter_class = CustomHelpFormatter
    # python_venv_parser.set_defaults(func=eve_git.python_venv)
    # python_venv_parser.add_argument('new', nargs='?', default='', help='Create new Virtual Environment')
    # python_venv_parser.add_argument('change', nargs='?', default='', help='Modify Virtual Environment')
    python_venv_subparsers = python_venv_parser.add_subparsers(title='commands', dest='command', metavar="<command>")

    # python --> venv --> new
    python_venv_new_parser = python_venv_subparsers.add_parser('new', help='Create new Venv', parents=[common])
    python_venv_new_parser.formatter_class = CustomHelpFormatter
    python_venv_new_parser.set_defaults(func=eve_git.python_venv)
    python_venv_new_parser.add_argument('foldername', default='.env', nargs='?', help='Specify folder name')

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


# eve-git
#   clone            Clone selected repo into current folder
#       repository       Repository name
#       [username]       Specify User/Org (default: None)
#   list             List remote Repositories. Max 50 items displayed.
#       [repository]     Help for <repository> (default: )
#       [username]       Specify User/Org (default: )
#   list_org         List remote Oranizations. (Admin only)
#   create           Create remote Repository (and clone it to current dir)
#       [reponame]       Repository name (default: )
#       [description]    New repo description (default: TODO: <Write project description>)
#       [username]       Specify User/Org under which will it be created (default: jverner)
#   create_org       Create remote Organization
#       [organization]   Specify Organization (default: )
#       [description]    Help for <description> (default: TODO: <Write organization description>)
#       [fullname]       Help for <fullname> (default: )
#       [visibility]     Help for <visibility> (default: public)
#   remove           Remove remote Repository
#   repository     Help for <repository>
#       [username]       Specify User/Org (default: None)
#   remove_org       Remove remote Organization. Has to be empty.
#       [organization]   Specify Organization (default: None)
#   edit             Edit remote repo Description
#       repository       Help for <repository>
#       [username]       Specify User/Org (default: None)
#   transfer         Transfer repository to different User/Group
#       [repository]     Specify Repository for transfer (default: )
#       [username]       Specify User/Org (default: )
#       [new_owner]      Specify target User/Org (default: )
#   connect          Connect current repository to remote one
#       [repository]     Specify Repository to connect to (default: )
#       [remote_name]    git remote add <remote_name> (default: gitea)
#   deploy           Deploy selected repository to production
#   repository     Repository name
#       [username]       Specify User/Org (default: None)
#       [branch]         Branch to deploy (default: master)
#   template         Choose one of the templates and copy here.
#   python           Python stuff.
#       venv           Manipulating with environments
#           new            Create new Virtual Environment
#       template       Managing templates
#           list           List possible python templates to download
