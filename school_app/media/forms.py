from django import forms
from django.utils.translation import gettext_lazy as _

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


def save_images(model, files, **owner):
    """Create one ``model`` row per cleaned file, e.g.
    ``save_images(AnnouncementImage, files, announcement=announcement)``."""
    for f in files:
        model.objects.create(file=f, **owner)
