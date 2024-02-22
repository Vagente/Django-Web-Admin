import os
from pathlib import Path
import shutil
from functools import wraps
import re
import bisect
from django.conf import settings


def is_valid_filename(name) -> bool:
    if type(name) is not str:
        return False
    s = re.fullmatch(r"[-\w.]+", name)
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
            self = args[0]
            if 0 in idxes:
                raise ValueError(f"0 shouldn't be in idxes: {idxes}")
            args = list(args)
            for i, idx in enumerate(idxes):
                p = Path(str(args[idx]))
                for j in p.parts:
                    if not is_valid_filename(j):
                        return False
                if should_exist[i] != p.exists():
                    return False
                p = self.root / p
                args[idx] = p
                if settings.DEBUG:
                    assert Path('/home/vagente/djangoWeb_media') in p.parents
            return func(*args, **kwargs)

        return wrapper

    return decorator


class FileManager(object):
    def __init__(self, root_path=settings.FILE_MANAGER_ROOT_PATH):
        self.root = Path(str(root_path))
        if not self.root.is_absolute() or not self.root.exists() or not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("Invalid root path")

    def list_root_files(self):
        return _list_files(self.root)

    @_resolve_path((True,))
    def list_files(self, path: Path):
        if not path.is_dir() or path.is_symlink():
            return False
        return _list_files(path)

    @_resolve_path((False,))
    def touch(self, path: Path) -> bool:
        if not path.parent.exists():
            return False
        try:
            path.touch(exist_ok=False)
        except FileExistsError:
            return False
        return True

    @_resolve_path((True, True), (1, 2))
    def copy_file(self, src: Path, dest: Path) -> bool:
        if not dest.is_dir() or dest.is_symlink():
            return False
        shutil.copy(src, dest, follow_symlinks=False)
        return True

    @_resolve_path((True,))
    def delete_file(self, path: Path):
        try:
            path.unlink(missing_ok=True)
        except PermissionError:
            return False

    @_resolve_path((True, False), (1, 2))
    def move(self, old_path: Path, new_path: Path) -> bool:
        if not new_path.is_dir() or new_path.is_symlink() or old_path.is_symlink():
            return False
        try:
            shutil.move(old_path, new_path)
        except OSError:
            return False
        return True

    @_resolve_path((True, False), (1, 2))
    def copy_dir(self, src_path: Path, dest_path: Path) -> bool:
        if not src_path.is_dir() or not dest_path.is_dir() or src_path.is_symlink() or dest_path.is_symlink():
            return False
        shutil.copytree(src_path, dest_path, symlinks=True)
        return True

    @_resolve_path((False,))
    def mkdir(self, path: Path) -> bool:
        try:
            path.mkdir()
        except FileNotFoundError:
            return False
        return True

    @_resolve_path((True,))
    def delete_folder(self, path: Path) -> bool:
        if not shutil.rmtree.avoids_symlink_attacks:
            return False
        shutil.rmtree(path, True)
        return True
