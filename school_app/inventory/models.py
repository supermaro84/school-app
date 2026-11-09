"""Personal inventories: things users own and lend to each other.

Every thing is an ``Item`` (id, category, title, description, owner). Each
category adds its own fields in a model that extends ``Item`` (multi-table
inheritance); books are the first one. To add a category, add a subclass, a
``Category`` choice and an entry in ``CATEGORY_MODELS`` (and a form in
forms.py).

Lending is recorded as ``Loan`` rows, so there is a history. An item has at
most one open loan (``returned_at`` empty); its borrower is the item's current
holder. Ownership never changes by lending.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from media.models import AttachedImage, delete_attached_file


class Item(models.Model):
    class Category(models.TextChoices):
        BOOK = "book", _("Book")

    category = models.CharField(_("category"), max_length=20, choices=Category.choices)
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    owner = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="inventory_items", verbose_name=_("owner")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "pk"]

    def __str__(self):
        return self.title

    @cached_property
    def details(self):
        """The category-specific object (e.g. the Book) for this item."""
        model = CATEGORY_MODELS.get(self.category)
        if model is None or isinstance(self, model):
            return self
        return getattr(self, model._meta.model_name)

    @cached_property
    def active_loan(self):
        """The open loan, or None. Lists prefetch it into ``open_loans``."""
        if hasattr(self, "open_loans"):
            return self.open_loans[0] if self.open_loans else None
        return self.loans.filter(returned_at__isnull=True).select_related("borrower").first()

    @property
    def holder(self):
        """Who has the item now: the borrower while lent, else the owner."""
        loan = self.active_loan
        return loan.borrower if loan else self.owner

    @property
    def is_available(self):
        return self.active_loan is None


def isbn_digits(value):
    return "".join(c for c in value if c.isalnum()).upper()


def validate_isbn(value):
    """ISBN-10 or ISBN-13 with a correct check digit (hyphens and spaces allowed)."""
    digits = isbn_digits(value)
    if len(digits) == 10 and digits[:9].isdigit() and (digits[9].isdigit() or digits[9] == "X"):
        total = sum((10 - i) * int(d) for i, d in enumerate(digits[:9]))
        total += 10 if digits[9] == "X" else int(digits[9])
        if total % 11 == 0:
            return
    elif len(digits) == 13 and digits.isdigit():
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
        if total % 10 == 0:
            return
    raise ValidationError(_("Enter a valid ISBN-10 or ISBN-13."), code="invalid_isbn")


class Book(Item):
    author = models.CharField(_("author"), max_length=200)
    # Optional: older books have none. Several copies may share one ISBN.
    isbn = models.CharField(_("ISBN"), max_length=17, blank=True, validators=[validate_isbn])

    def save(self, *args, **kwargs):
        self.category = Item.Category.BOOK
        self.isbn = isbn_digits(self.isbn)
        super().save(*args, **kwargs)


CATEGORY_MODELS = {Item.Category.BOOK: Book}


def item_image_path(instance, filename):
    # inventory/<owner username>/<item id>/<filename>
    return f"inventory/{instance.item.owner.username}/{instance.item_id}/{filename}"


class ItemImage(AttachedImage):
    item = models.ForeignKey(Item, related_name="images", on_delete=models.CASCADE)
    file = models.ImageField(_("image"), upload_to=item_image_path)

    class Meta(AttachedImage.Meta):
        pass


post_delete.connect(delete_attached_file, sender=ItemImage)


class Loan(models.Model):
    item = models.ForeignKey(Item, related_name="loans", on_delete=models.CASCADE)
    borrower = models.ForeignKey(
        "auth.User", related_name="borrowed_items", on_delete=models.CASCADE, verbose_name=_("borrower")
    )
    lent_at = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(_("due date"), null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-lent_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["item"], condition=Q(returned_at__isnull=True), name="one_open_loan_per_item"
            )
        ]

    def __str__(self):
        return f"{self.item} → {self.borrower}"

    @property
    def is_overdue(self):
        return self.returned_at is None and self.due_date is not None and self.due_date < timezone.localdate()
