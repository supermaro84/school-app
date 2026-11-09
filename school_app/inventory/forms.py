from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from media.forms import MultipleImageField
from school_app.forms import UserChoiceLabelsMixin

from .models import Book, Item


class BookForm(forms.ModelForm):
    images = MultipleImageField(label=_("Photos"))

    class Meta:
        model = Book
        fields = ["title", "author", "isbn", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
            "isbn": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "autocomplete": "off"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        help_texts = {"isbn": _("Optional. 10 or 13 digits; hyphens are fine.")}


# One form per category; the add page offers these
CATEGORY_FORMS = {Item.Category.BOOK: BookForm}


class LendForm(UserChoiceLabelsMixin, forms.Form):
    borrower = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True), label=_("Borrower"))
    due_date = forms.DateField(
        label=_("Due date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        # Lending to yourself makes no sense
        self.fields["borrower"].queryset = self.fields["borrower"].queryset.exclude(pk=owner.pk)

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < timezone.localdate():
            raise forms.ValidationError(_("The due date can't be in the past."))
        return due_date
