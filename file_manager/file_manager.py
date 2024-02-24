import os
from pathlib import Path
import shutil
from functools import wraps
import re
import bisect
from django.conf import settings


def _check_parents(p):
    for path in p.parents:
        if path.is_symlink() or not path.exists():
            return False
    return True


def is_valid_filename(name) -> bool:
    if type(name) is not str:
        return False
    s = re.fullmatch(r"[-\w. ]+", name)
    if s is None or name in {"", ".", ".."}:
        return False
    return True


def _list_files(path):
    res = [list(), list()]
    for i in os.scandir(path):
        stat = i.stat(follow_symlinks=False)
        name = i.name
        if i.is_dir(follow_symlinks=False):
            bisect.insort(res[0], [name, stat.st_mtime, 'folder', stat.st_size], key=lambda x: x[0])
        else:
            t = Path(i.name).suffix
            t = t if t != "" else 'file'
            bisect.insort(res[1], [name, stat.st_mtime, t, stat.st_size], key=lambda x: x[0])
    return res


def _resolve_path(should_exist, idxes=(1,)):
    """
    Returns a decorator.
    args[0] should be self which is a Filemanager.
    should_exit should be iterable of bool, corresponding to idx in idxes, which should be path in args.
    args[idx] should be path
    Will replace path with None if path is not valid(not a sub path of the root path or contain invalid characters)
    will return False if should_exit != args[idx].exists()
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if settings.DEBUG:
                print(args)
            self = args[0]
            if 0 in idxes:
                raise ValueError(f"0 shouldn't be in idxes: {idxes}")
            args = list(args)
            for i, idx in enumerate(idxes):
                partial = Path(str(args[idx]))
                for j in partial.parts:
                    if not is_valid_filename(j):
                        return False, f"Invalid filename: '{j}'"
                p = self.root / partial
                if should_exist[i] != p.exists():
                    return False, f"Path '{str(partial)}' existence should be {should_exist[i]}"

                if not should_exist and _check_parents(p):
                    return f"Path '{str(partial)}' contains invalid item(symlink or didn't exist"

                args[idx] = p
                if settings.DEBUG:
                    assert Path('/home/vagente/djangoWeb_media') in p.parents
            try:
                res = func(*args, **kwargs)
            except PermissionError:
                return False, 'Permission denied'
            except OSError:
                return False, 'OSError'
            return res

        return wrapper

    return decorator


class FileManager(object):
    def __init__(self, root_path=settings.FILE_MANAGER_ROOT_PATH):
        self.root = Path(str(root_path)).resolve()
        if not self.root.is_absolute() or not self.root.exists() or not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("Invalid root path")

    def list_files(self, path):
        if str(path) == '':
            return True, _list_files(self.root)
        else:
            return self._list_files(path)

    @_resolve_path((True,))
    def _list_files(self, path: Path):
        if not path.is_dir() or path.is_symlink():
            return False, f"Not a directory: {path.name}"
        return True, _list_files(path)

    @_resolve_path((False,))
    def touch(self, path: Path) -> (bool, str):
        try:
            path.touch(exist_ok=False)
        except FileExistsError:
            return False, f'File {path.name} exists'
        return True, None

    @_resolve_path((True, True), (1, 2))
    def copy_file(self, src: Path, dest: Path) -> (bool, str):
        if not dest.is_dir() or dest.is_symlink():
            return False, f"dest is not a directory: {dest.name}"
        shutil.copy(src, dest, follow_symlinks=False)
        return True, None

    @_resolve_path((True,))
    def delete_file(self, path: Path):
        path.unlink(missing_ok=True)
        return True, None

    @_resolve_path((True, False), (1, 2))
    def move(self, old_path: Path, new_path: Path) -> (bool, str):
        shutil.move(old_path, new_path)
        return True, None

    @_resolve_path((True, False), (1, 2))
    def copy_dir(self, src_path: Path, dest_path: Path) -> (bool, str):
        if not src_path.is_dir() or not dest_path.is_dir() or src_path.is_symlink() or dest_path.is_symlink():
            return False, f"src or dest is not directory"
        shutil.copytree(src_path, dest_path, symlinks=True)
        return True, None

    @_resolve_path((False,))
    def mkdir(self, path: Path) -> (bool, str):
        try:
            path.mkdir()
        except FileNotFoundError:
            return False, f"path parent didn't exist"
        return True, None

    @_resolve_path((True,))
    def delete_folder(self, path: Path) -> (bool, str):
        if not shutil.rmtree.avoids_symlink_attacks:
            return False, f"Platform is vulnerable to symlink attacks"
        shutil.rmtree(path, True)
        return True, None
