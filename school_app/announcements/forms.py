from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Announcement, AnnouncementComment, AnnouncementDocument, AnnouncementImage
from groups.models import GroupProfile
from media.forms import MultipleDocumentField, MultipleImageField
from school_app.forms import GroupsOrUsersRequiredMixin


class AnnouncementForm(GroupsOrUsersRequiredMixin, forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=GroupProfile.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # optional: renders as checkboxes
        required=False,
    )
    exp_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )

    images = MultipleImageField()
    remove_images = forms.ModelMultipleChoiceField(
        queryset=AnnouncementImage.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Remove images"),
    )
    documents = MultipleDocumentField()
    remove_documents = forms.ModelMultipleChoiceField(
        queryset=AnnouncementDocument.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Remove documents"),
    )

    class Meta:
        model = Announcement
        fields = ["title", "text", "groups", "users", "exp_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["remove_images"].queryset = self.instance.images.all()
            self.fields["remove_documents"].queryset = self.instance.documents.all()


class AnnouncementCommentForm(forms.ModelForm):
    class Meta:
        model = AnnouncementComment
        fields = ["text"]
