from django.db import models
from django.contrib.auth.models import User


class Asset(models.Model):
    TYPE_CHOICES = [
        ('tester', 'Tester'),
        ('station', 'Station'),
        ('board', 'Board'),
        ('chip', 'Chip'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('repair', 'In Repair'),
        ('retired', 'Retired'),
    ]

    name = models.CharField(max_length=120, unique=True)
    asset_tag = models.CharField(max_length=60, unique=True, blank=True)
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    checked_out_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='checked_out_assets'
    )
    checked_out_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['asset_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_asset_type_display()})"

    @property
    def is_available(self):
        return self.status == 'available'


class AssetRelationship(models.Model):
    """Tracks parent-child relationships: chip-on-board, board-on-station, etc."""
    parent = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='children')
    child = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='parents')
    attached_at = models.DateTimeField(auto_now_add=True)
    attached_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('parent', 'child')

    def __str__(self):
        return f"{self.child.name} → {self.parent.name}"


class AuditLog(models.Model):
    """Immutable audit trail for every action on every asset."""
    ACTION_CHOICES = [
        ('checkout', 'Checked Out'),
        ('checkin', 'Checked In'),
        ('status_change', 'Status Changed'),
        ('created', 'Created'),
        ('attached', 'Attached'),
        ('detached', 'Detached'),
        ('moved', 'Moved'),
        ('edited', 'Edited'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    previous_value = models.CharField(max_length=200, blank=True)
    new_value = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.asset.name} — {self.action} at {self.timestamp:%Y-%m-%d %H:%M}"
