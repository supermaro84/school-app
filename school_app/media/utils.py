import os
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_SIDE = 1920
JPEG_QUALITY = 80


def compress_image(uploaded_file):
    """Return ``uploaded_file`` as a smaller JPEG ``ContentFile``.

    The image is rotated upright from its EXIF orientation, scaled down so its
    longest side is at most ``MAX_IMAGE_SIDE`` and saved without metadata (no
    GPS location). Transparency is flattened onto white; animations keep only
    their first frame.
    """
    try:
        image = Image.open(uploaded_file)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(
            _("%(name)s is not a valid image.") % {"name": uploaded_file.name}
        ) from exc

    image = ImageOps.exif_transpose(image)
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.LANCZOS)

    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    name = os.path.splitext(os.path.basename(uploaded_file.name))[0] or "image"
    return ContentFile(buffer.getvalue(), name=f"{name}.jpg")
