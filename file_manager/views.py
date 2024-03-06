from pathlib import Path

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django_otp.decorators import otp_required

from file_manager import *
from file_manager.file_manager import FileManager
from .forms import UploadFileForm


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
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return handle_uploaded_file(request.FILES['file'], form.cleaned_data['path'])
        else:
            return JsonResponse({'message': "Invalid form"}, status=400)
    context = {
        'list_file': LIST_FILE,
        'create_file': CREATE_FILE,
        'delete_file': DELETE_FILE,
        'copy_file': COPY_FILE,
        'move_file': MOVE_FILE,
        'make_dir': MAKE_DIR,
        'form': UploadFileForm()
    }
    return render(request, 'file_manager/index.html', context)


@otp_required
def file_download(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    path = request.GET.get('path', '')
    if path == '':
        raise Http404
    manager = FileManager()
    path = Path(path)
    if not manager.path_exists(path):
        raise Http404
    path = manager.get_path(path)
    if path.is_dir():
        return JsonResponse({'message': "can't download folder"}, status=400)
    return FileResponse(open(path, 'rb'), as_attachment=True)
