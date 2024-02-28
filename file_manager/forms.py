from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField()
    file.widget.attrs.update({'class': 'form-control'})
