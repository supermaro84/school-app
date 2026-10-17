from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Gallery
from .utils import compress_image

MAX_IMAGES = 10


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Image field that accepts several files at once (see Django docs on
    uploading multiple files). Cleans to a list of compressed JPEG files."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleImageInput(attrs={"accept": "image/*"}))
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", _("Images"))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [f for f in files if f]
        if len(files) > MAX_IMAGES:
            raise forms.ValidationError(
                _("You can attach at most %(max)d images.") % {"max": MAX_IMAGES}
            )
        if not files and self.required:
            raise forms.ValidationError(self.error_messages["required"])
        return [compress_image(super(MultipleImageField, self).clean(f, initial)) for f in files]


DOCUMENT_EXTENSIONS = [
    "pdf", "doc", "docx", "odt", "rtf", "txt",
    "xls", "xlsx", "ods", "csv", "ppt", "pptx", "odp",
]
MAX_DOCUMENTS = 10
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB


class MultipleDocumentInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleDocumentField(forms.FileField):
    """Accepts several documents at once; cleans to a list of uploaded files.

    Only office/text formats (DOCUMENT_EXTENSIONS) up to MAX_DOCUMENT_SIZE each.
    """

    def __init__(self, *args, **kwargs):
        accept = ",".join(f".{ext}" for ext in DOCUMENT_EXTENSIONS)
        kwargs.setdefault("widget", MultipleDocumentInput(attrs={"accept": accept}))
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", _("Documents"))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [f for f in files if f]
        if len(files) > MAX_DOCUMENTS:
            raise forms.ValidationError(
                _("You can attach at most %(max)d documents.") % {"max": MAX_DOCUMENTS}
            )
        cleaned = []
        for f in files:
            f = super(MultipleDocumentField, self).clean(f, initial)
            extension = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
            if extension not in DOCUMENT_EXTENSIONS:
                raise forms.ValidationError(
                    _("%(name)s is not a supported document type.") % {"name": f.name}
                )
            if f.size > MAX_DOCUMENT_SIZE:
                raise forms.ValidationError(
                    _("%(name)s is larger than %(max)d MB.") % {"name": f.name, "max": MAX_DOCUMENT_SIZE // (1024 * 1024)}
                )
            cleaned.append(f)
        return cleaned


def save_images(model, files, **owner):
    """Create one ``model`` row per cleaned file, e.g.
    ``save_images(AnnouncementImage, files, announcement=announcement)``.
    Works the same for documents."""
    for f in files:
        model.objects.create(file=f, **owner)


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ["name", "description", "users", "groups"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class GalleryUploadForm(forms.Form):
    images = MultipleImageField(required=True)
