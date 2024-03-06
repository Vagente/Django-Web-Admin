from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField()
    path = forms.CharField(widget=forms.HiddenInput)
    file.widget.attrs.update({'class': 'form-control'})
    path.widget.attrs.update({'id': 'upload_path', 'value': '.'})

