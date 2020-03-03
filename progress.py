"""<DESCRIPTION OF THIS CLASS>"""

from git import RemoteProgress  # https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
from tqdm import tqdm
from colorama import Fore


# ===============================
# =           CLASSES           =
# ===============================
class Progress(RemoteProgress):
    """Show ProgressBar when clonning remote repo.

    Original code:
        https://github.com/hooyao/github-org-backup-tool/blob/master/utils.py
    """

    pbar_dict = dict()
    last_pbar = None

    last_op_code = None
    last_pos = None
    op_names = {RemoteProgress.COUNTING: 'Counting objects',
                RemoteProgress.COMPRESSING: 'Compressing objects',
                RemoteProgress.WRITING: 'Writing objects',
                RemoteProgress.RECEIVING: 'Receiving objects',
                RemoteProgress.RESOLVING: 'Resolving deltas',
                RemoteProgress.FINDING_SOURCES: 'Finding sources',
                RemoteProgress.CHECKING_OUT: 'Checking out files'}
    max_msg_len = 0
    for i, (key, value) in enumerate(op_names.items()):
        if len(value) > max_msg_len:
            max_msg_len = len(value)
    for i, (key, value) in enumerate(op_names.items()):
        if len(value) < max_msg_len:
            appended_value = value + (' ' * (max_msg_len - len(value)))
            op_names[key] = appended_value

    def update(self, op_code, cur_count, max_count=None, message=''):
        if op_code in self.op_names:
            op_name = self.op_names[op_code]
            if self.last_op_code is None or self.last_op_code != op_code:
                if self.last_pbar is not None:
                    self.last_pbar.close()
                self.last_pbar = tqdm(total=max_count, unit='item', desc=op_name,
                                      bar_format="%s{l_bar}%s%s{bar}%s{r_bar}" %
                                                 (Fore.GREEN, Fore.RESET, Fore.BLUE, Fore.RESET))
                self.last_pos = 0
                self.last_op_code = op_code
            pbar = self.last_pbar
            last_pos = self.last_pos
            diff = cur_count - last_pos
            pbar.update(diff)
            self.last_pbar = pbar
            self.last_op_code = op_code
            self.last_pos = cur_count


# TODO: Priklad decoratoru

# def authenticated_only(method):
#     def decorated(*args, **kwargs):
#         if check_authenticated(kwargs['user']):
#             return method(*args, **kwargs)
#         else:
#             raise UnauthenticatedError
#     return decorated

# def authorized_only(method):
#     def decorated(*args, **kwargs):
#         if check_authorized(kwargs['user'], kwargs['action']):
#             return method(*args, **kwargs)
#         else:
#             raise UnauthorizedError
#     return decorated


# @authorized_only
# @authenticated_only
# def execute(action, *args, **kwargs):
#     return action()
