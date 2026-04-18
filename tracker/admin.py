from django.contrib import admin
from .models import Asset, AssetRelationship, AuditLog


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_tag', 'asset_type', 'status', 'location', 'checked_out_by']
    list_filter = ['asset_type', 'status']
    search_fields = ['name', 'asset_tag', 'serial_number', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AssetRelationship)
class AssetRelationshipAdmin(admin.ModelAdmin):
    list_display = ['child', 'parent', 'attached_by', 'attached_at']
    raw_id_fields = ['parent', 'child', 'attached_by']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['asset', 'action', 'performed_by', 'timestamp']
    list_filter = ['action']
    search_fields = ['asset__name', 'performed_by__username']
    readonly_fields = ['asset', 'action', 'performed_by', 'timestamp', 'notes', 'previous_value', 'new_value']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
