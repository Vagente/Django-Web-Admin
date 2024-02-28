from django.shortcuts import render
from django_otp.decorators import otp_required
from django.http import JsonResponse

from file_manager import *
from .file_manager import FileManager
from .forms import UploadFileForm
from pathlib import Path


def handle_uploaded_file(file, path):
    manager = FileManager()
    path = Path(path)
    path /= file.name
    res, message = manager.touch(path)
    if not res:
        return JsonResponse({'message': message}, status=400)
    path = manager.get_path(path)
    with open(path, 'wb') as dest:
        for chunk in file.chunks():
            dest.write(chunk)
    return JsonResponse({'message': message}, status=201)


@otp_required
def file_manager(request):
    if request.method == 'POST' and request.FILES != dict():
        path = request.headers["Current-Path"]
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # return JsonResponse({'message': "hi"})
            return handle_uploaded_file(request.FILES['file'], path)
    # status, files = manager.list_root_files()
    context = {
        # 'all_files': json.dumps(files),
        'list_file': LIST_FILE,
        'create_file': CREATE_FILE,
        'delete_file': DELETE_FILE,
        'copy_file': COPY_FILE,
        'move_file': MOVE_FILE,
        'make_dir': MAKE_DIR,
        'form': UploadFileForm()
        # 'all_func': json.dumps(ALL_FUNCTIONS)
    }
    return render(request, 'file_manager/index.html', context)
