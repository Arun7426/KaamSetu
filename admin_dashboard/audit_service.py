from .models import AuditLog


def create_audit_log(
    admin=None,
    action="OTHER",
    module="",
    description="",
    target_user=None,
    target_id=None,
    ip_address=None,
):
    """
    Create an audit log entry.

    This helper keeps audit-log creation consistent
    across the admin dashboard.
    """

    return AuditLog.objects.create(
        admin=admin,
        action=action,
        module=module,
        description=description,
        target_user=target_user,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=ip_address,
    )


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")