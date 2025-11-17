from django import forms
from .models import GroupProfile,Group
from groups.models import GroupProfile

class GroupForm(forms.ModelForm):
    
    name = forms.CharField(max_length=150, required=True, label="Group Name")
    class Meta:
        model = GroupProfile
        fields = ['name', 'description', 'admins', 'members']

class GroupEditForm(forms.ModelForm):
    
    class Meta:
        model = GroupProfile
        fields = [ 'description', 'admins', 'members']