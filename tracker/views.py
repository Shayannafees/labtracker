from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse

from .models import Asset, AssetRelationship, AuditLog
from .forms import AssetForm, MoveAssetForm, AttachAssetForm


def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'tracker/login.html')


@login_required
def dashboard(request):
    assets = Asset.objects.all()
    context = {
        'total': assets.count(),
        'available': assets.filter(status='available').count(),
        'in_use': assets.filter(status='in_use').count(),
        'repair': assets.filter(status='repair').count(),
        'retired': assets.filter(status='retired').count(),
        'recent_logs': AuditLog.objects.select_related('asset', 'performed_by').all()[:10],
        'my_checkouts': Asset.objects.filter(checked_out_by=request.user),
        'type_counts': {t: assets.filter(asset_type=t).count() for t, _ in Asset.TYPE_CHOICES},
    }
    return render(request, 'tracker/dashboard.html', context)


@login_required
def asset_list(request):
    qs = Asset.objects.select_related('checked_out_by').all()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(asset_tag__icontains=q) |
            Q(location__icontains=q) |
            Q(serial_number__icontains=q) |
            Q(description__icontains=q)
        )

    asset_type = request.GET.get('type', '')
    if asset_type:
        qs = qs.filter(asset_type=asset_type)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    context = {
        'assets': qs,
        'query': q,
        'selected_type': asset_type,
        'selected_status': status,
        'type_choices': Asset.TYPE_CHOICES,
        'status_choices': Asset.STATUS_CHOICES,
    }
    return render(request, 'tracker/asset_list.html', context)


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    children = AssetRelationship.objects.filter(parent=asset).select_related('child')
    parents = AssetRelationship.objects.filter(child=asset).select_related('parent')
    logs = AuditLog.objects.filter(asset=asset).select_related('performed_by')[:30]
    attachable = Asset.objects.exclude(pk=pk).exclude(
        id__in=AssetRelationship.objects.filter(parent=asset).values('child_id')
    )
    context = {
        'asset': asset,
        'children': children,
        'parents': parents,
        'logs': logs,
        'attach_form': AttachAssetForm(attachable_assets=attachable),
        'move_form': MoveAssetForm(instance=asset),
    }
    return render(request, 'tracker/asset_detail.html', context)


@login_required
def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save()
            AuditLog.objects.create(
                asset=asset, action='created',
                performed_by=request.user,
                notes=f"Asset created via web interface"
            )
            messages.success(request, f'Asset "{asset.name}" created.')
            return redirect('asset_detail', pk=asset.pk)
    else:
        form = AssetForm()
    return render(request, 'tracker/asset_form.html', {'form': form, 'action': 'Create'})


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            old_status = asset.status
            asset = form.save()
            if old_status != asset.status:
                AuditLog.objects.create(
                    asset=asset, action='status_change',
                    performed_by=request.user,
                    previous_value=old_status,
                    new_value=asset.status
                )
            else:
                AuditLog.objects.create(
                    asset=asset, action='edited',
                    performed_by=request.user,
                )
            messages.success(request, f'Asset "{asset.name}" updated.')
            return redirect('asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
    return render(request, 'tracker/asset_form.html', {'form': form, 'action': 'Edit', 'asset': asset})


@login_required
def checkout(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if asset.status != 'available':
        messages.error(request, f'"{asset.name}" is not available for checkout.')
        return redirect('asset_detail', pk=pk)
    notes = request.POST.get('notes', '')
    asset.status = 'in_use'
    asset.checked_out_by = request.user
    asset.checked_out_at = timezone.now()
    asset.save()
    AuditLog.objects.create(
        asset=asset, action='checkout',
        performed_by=request.user,
        new_value=request.user.get_full_name() or request.user.username,
        notes=notes
    )
    messages.success(request, f'"{asset.name}" checked out to you.')
    return redirect('asset_detail', pk=pk)


@login_required
def checkin(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if asset.checked_out_by != request.user and not request.user.is_staff:
        messages.error(request, 'You can only check in assets you checked out.')
        return redirect('asset_detail', pk=pk)
    notes = request.POST.get('notes', '')
    prev_user = asset.checked_out_by.get_full_name() or asset.checked_out_by.username
    asset.status = 'available'
    asset.checked_out_by = None
    asset.checked_out_at = None
    asset.save()
    AuditLog.objects.create(
        asset=asset, action='checkin',
        performed_by=request.user,
        previous_value=prev_user,
        notes=notes
    )
    messages.success(request, f'"{asset.name}" checked back in.')
    return redirect('asset_detail', pk=pk)


@login_required
def move_asset(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = MoveAssetForm(request.POST, instance=asset)
        if form.is_valid():
            old_location = asset.location
            asset = form.save()
            AuditLog.objects.create(
                asset=asset, action='moved',
                performed_by=request.user,
                previous_value=old_location,
                new_value=asset.location
            )
            messages.success(request, f'"{asset.name}" moved to {asset.location}.')
    return redirect('asset_detail', pk=pk)


@login_required
def attach_asset(request, pk):
    parent = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        notes = request.POST.get('notes', '')
        child = get_object_or_404(Asset, pk=child_id)
        rel, created = AssetRelationship.objects.get_or_create(
            parent=parent, child=child,
            defaults={'attached_by': request.user, 'notes': notes}
        )
        if created:
            AuditLog.objects.create(asset=child, action='attached', performed_by=request.user,
                                    new_value=parent.name, notes=notes)
            AuditLog.objects.create(asset=parent, action='attached', performed_by=request.user,
                                    new_value=child.name, notes=notes)
            messages.success(request, f'"{child.name}" attached to "{parent.name}".')
        else:
            messages.warning(request, 'This relationship already exists.')
    return redirect('asset_detail', pk=pk)


@login_required
def detach_asset(request, rel_id):
    rel = get_object_or_404(AssetRelationship, pk=rel_id)
    parent_pk = rel.parent.pk
    AuditLog.objects.create(asset=rel.child, action='detached', performed_by=request.user,
                             previous_value=rel.parent.name)
    AuditLog.objects.create(asset=rel.parent, action='detached', performed_by=request.user,
                             previous_value=rel.child.name)
    rel.delete()
    messages.success(request, 'Relationship removed.')
    return redirect('asset_detail', pk=parent_pk)


@login_required
def audit_log(request):
    logs = AuditLog.objects.select_related('asset', 'performed_by').all()
    asset_filter = request.GET.get('asset', '')
    if asset_filter:
        logs = logs.filter(asset__name__icontains=asset_filter)
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    return render(request, 'tracker/audit_log.html', {
        'logs': logs[:200],
        'action_choices': AuditLog.ACTION_CHOICES,
        'asset_filter': asset_filter,
        'action_filter': action_filter,
    })
