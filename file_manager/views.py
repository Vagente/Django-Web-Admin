from django.shortcuts import render
from file_manager.file_manager import FileManager
import json
from file_manager import *


def file_manager(request):
    manager = FileManager()
    # status, files = manager.list_root_files()
    context = {
        # 'all_files': json.dumps(files),
        'list_file': LIST_FILE,
        'create_file': CREATE_FILE,
        'delete_file': DELETE_FILE,
        'copy_file': COPY_FILE,
        'move_file': MOVE_FILE,
        'make_dir': MAKE_DIR,
        # 'all_func': json.dumps(ALL_FUNCTIONS)
    }
    return render(request, 'file_manager/index.html', context)
