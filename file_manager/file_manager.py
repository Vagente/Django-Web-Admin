import bisect
import os
import pathlib
import re
import shutil
import time
from functools import wraps
from pathlib import Path

from django.conf import settings


def _parents_valid(p):
    if not p.parent.exists():
        return False
    for path in p.parents:
        if path.is_symlink():
            return False
    return True


def is_valid_filename(name) -> bool:
    s = re.fullmatch(r"[^/\x00]+", name)
    if s is None or name in {"", ".."}:
        return False
    return True


def get_files(path):
    res = [list(), list()]
    for i in os.scandir(path):
        stat = i.stat(follow_symlinks=False)
        name = i.name
        if i.is_dir(follow_symlinks=False):
            bisect.insort(res[0], [name, stat.st_mtime, 'folder', None], key=lambda x: x[0])
        else:
            t = Path(i.name).suffix
            t = t if t != "" else 'file'
            bisect.insort(res[1], [name, stat.st_mtime, t, stat.st_size], key=lambda x: x[0])
    return res


def _valid_path(path, path_should_exist, root):
    if type(path) is not str and type(path) is not pathlib.PosixPath:
        return False, "invalid path type"
    for j in path.parts:
        if not is_valid_filename(j):
            return False, f"Invalid filename: '{j}'"
    p = root / path
    if path_should_exist != p.exists() and path_should_exist is not None:
        return False, f"Path '{str(path)}' existence should be {path_should_exist}"

    if not path_should_exist and not _parents_valid(p):
        return False, f"Path '{str(path)}' contains invalid path(symlink or didn't exist)"

    if settings.DEBUG:
        root = Path(settings.FILE_MANAGER_ROOT_PATH)
        if root != p and not Path(settings.FILE_MANAGER_ROOT_PATH) in p.parents:
            return False, f"Path {p} not in root"
    return True, p


def _resolve_path(should_exist, idxes=(1,)):
    """
    Returns a decorator.
    args[0] should be self which is a Filemanager.
    should_exit should be iterable of bool, corresponding to idx in idxes, which should be the index of path in args.
    args[idx] should be path.
    Will return (False, message) if path is invalid(not a sub path of the root path or contain invalid characters).
    will return (False, message) if should_exist != args[idx].exists(), won't check for path existence if
    should_exist[i] is None.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            if 0 in idxes:
                raise ValueError(f"0 shouldn't be in idxes: {idxes}")
            args = list(args)
            for i, idx in enumerate(idxes):
                partial = Path(str(args[idx]))
                path_should_exist = should_exist[i]
                res, data = _valid_path(partial, path_should_exist, self.root)
                if not res:
                    return False, data
                args[idx] = data
            try:
                res = func(*args, **kwargs)
            except PermissionError:
                return False, 'Permission denied'
            except OSError as e:
                print(e)
                return False, 'OSError'
            return res

        return wrapper

    return decorator


def _copy_dir(src_path: Path, dest_path: Path) -> (bool, str):
    shutil.copytree(src_path, dest_path, symlinks=True)
    return True, 'success'


def _delete_folder(path: Path) -> (bool, str):
    if not shutil.rmtree.avoids_symlink_attacks:
        return False, f"Platform is vulnerable to symlink attacks"
    shutil.rmtree(path, True)
    return True, 'success'


def _delete_file(path: Path):
    path.unlink(missing_ok=True)
    return True, 'success'


def _copy_file(src: Path, dest: Path) -> (bool, str):
    if not dest.is_dir() or dest.is_symlink():
        return False, f"dest is not a directory: {dest.name}"
    shutil.copy(src, dest, follow_symlinks=False)
    return True, 'success'


def _get_dir_size(path: Path):
    if not path.is_dir() or path.is_symlink():
        return False, f"path is not a directory: {path.name}"
    size = 0
    last_count = 0
    current_count = 0
    start = time.time()
    for p, directory, files in os.walk(path):
        p = Path(p)
        for i in directory + files:
            current_count += 1
            size += (p / i).lstat().st_size
            if current_count - last_count < 10000:
                continue
            last_count = current_count
            tmp = time.time()
            if (tmp - start) > 0.5:
                start = tmp
                yield [size, current_count]

    yield [size, current_count]


class FileManager(object):
    def __init__(self):
        self.root = Path(str(settings.FILE_MANAGER_ROOT_PATH)).resolve()
        if not self.root.is_absolute() or not self.root.exists() or not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("Invalid root path")

    @_resolve_path((None,))
    def get_path(self, path):
        return path

    def path_exists(self, path):
        res, data = _valid_path(path, True, self.root)
        return res

    def list_files(self, path):
        if str(path) == '':
            return True, get_files(self.root)
        else:
            return self._list_files(path)

    @_resolve_path((True,))
    def _list_files(self, path: Path):
        if not path.is_dir() or path.is_symlink():
            return False, f"Not a directory: {path.name}"
        return True, get_files(path)

    @_resolve_path((False,))
    def touch(self, path: Path) -> (bool, str):
        try:
            path.touch(exist_ok=False)
        except FileExistsError:
            return False, f'File {path.name} exists'
        return True, 'success'

    @_resolve_path((True, True), (1, 2))
    def copy(self, src: Path, dest: Path):
        if dest.is_file() or dest.is_symlink():
            return False, f"destination if not a dir: {dest.name}"
        if src.is_dir():
            return _copy_dir(src, dest / src.name)
        else:
            return _copy_file(src, dest)

    @_resolve_path((True,))
    def delete(self, path: Path):
        if path.is_dir() and not path.is_symlink():
            return _delete_folder(path)
        else:
            return _delete_file(path)

    @_resolve_path((True, None), (1, 2))
    def move(self, old_path: Path, new_path: Path) -> (bool, str):
        if new_path.exists() and new_path.is_symlink():
            return False, f"new_path is a symlink"
        if new_path.exists() and not new_path.is_dir():
            return False, f"new_path exists"
        shutil.move(old_path, new_path)
        return True, 'success'

    @_resolve_path((False,))
    def mkdir(self, path: Path) -> (bool, str):
        path.mkdir()
        return True, 'success'

    @_resolve_path((True,))
    def get_dir_size(self, path):
        yield from _get_dir_size(path)
