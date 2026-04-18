from django import forms
from .models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'asset_tag', 'asset_type', 'status', 'location', 'serial_number', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class MoveAssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['location']


class AttachAssetForm(forms.Form):
    child_id = forms.ChoiceField(label='Asset to attach')
    notes = forms.CharField(required=False, max_length=200, label='Notes')

    def __init__(self, *args, attachable_assets=None, **kwargs):
        super().__init__(*args, **kwargs)
        if attachable_assets is not None:
            self.fields['child_id'].choices = [
                (a.pk, f"{a.name} ({a.get_asset_type_display()})") for a in attachable_assets
            ]
