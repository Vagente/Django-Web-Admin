from django.shortcuts import render
from file_manager.file_manager import FileManager
import json


def file_manager(request):
    manager = FileManager()
    files = manager.list_root_files()
    context = {
        'all_files': json.dumps(files)
    }
    return render(request, 'file_manager/index.html', context)
