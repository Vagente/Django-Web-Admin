from django.shortcuts import render
from django_otp.decorators import otp_required

from file_manager import *
from .forms import UploadFileForm


@otp_required
def file_manager(request):
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


def upload_file(request):
    print(request)
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            print("valid")
