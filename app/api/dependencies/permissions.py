"""
Permission dependencies for role-based access control
"""
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.api.routes.auth import get_current_user


# Permission matrix based on roles
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        # User Management
        "can_view_users": True,
        "can_create_users": True,
        "can_edit_users": True,
        "can_delete_users": True,
        # Client Management
        "can_view_clients": True,
        "can_create_clients": True,
        "can_edit_clients": True,
        "can_delete_clients": True,
        # Shipment Management
        "can_view_shipments": True,
        "can_create_shipments": True,
        "can_edit_shipments": True,
        "can_delete_shipments": True,
        "can_update_shipment_status": True,
        # Analytics & Reports
        "can_view_analytics": True,
        "can_view_reports": True,
        "can_export_data": True,
        # Settings
        "can_manage_settings": True,
        "can_manage_integrations": True,
        "can_manage_automations": True,
        # Audit
        "can_view_audit_logs": True,
    },
    UserRole.MANAGER: {
        # User Management
        "can_view_users": False,
        "can_create_users": False,
        "can_edit_users": False,
        "can_delete_users": False,
        # Client Management
        "can_view_clients": True,
        "can_create_clients": True,
        "can_edit_clients": True,
        "can_delete_clients": False,
        # Shipment Management
        "can_view_shipments": True,
        "can_create_shipments": True,
        "can_edit_shipments": True,
        "can_delete_shipments": False,
        "can_update_shipment_status": True,
        # Analytics & Reports
        "can_view_analytics": True,
        "can_view_reports": True,
        "can_export_data": True,
        # Settings
        "can_manage_settings": False,
        "can_manage_integrations": True,
        "can_manage_automations": True,
        # Audit
        "can_view_audit_logs": True,
    },
    UserRole.OPERATOR: {
        # User Management
        "can_view_users": False,
        "can_create_users": False,
        "can_edit_users": False,
        "can_delete_users": False,
        # Client Management
        "can_view_clients": True,
        "can_create_clients": True,
        "can_edit_clients": True,
        "can_delete_clients": False,
        # Shipment Management
        "can_view_shipments": True,
        "can_create_shipments": True,
        "can_edit_shipments": True,
        "can_delete_shipments": False,
        "can_update_shipment_status": True,
        # Analytics & Reports
        "can_view_analytics": False,
        "can_view_reports": False,
        "can_export_data": False,
        # Settings
        "can_manage_settings": False,
        "can_manage_integrations": False,
        "can_manage_automations": False,
        # Audit
        "can_view_audit_logs": False,
    },
    UserRole.SELLER: {
        # User Management
        "can_view_users": False,
        "can_create_users": False,
        "can_edit_users": False,
        "can_delete_users": False,
        # Client Management
        "can_view_clients": True,
        "can_create_clients": True,
        "can_edit_clients": True,
        "can_delete_clients": False,
        # Shipment Management
        "can_view_shipments": True,  # Only their own shipments
        "can_create_shipments": True,
        "can_edit_shipments": True,  # Only their own shipments
        "can_delete_shipments": False,
        "can_update_shipment_status": True,  # Only their own shipments
        # Analytics & Reports
        "can_view_analytics": False,
        "can_view_reports": False,
        "can_export_data": False,
        # Settings
        "can_manage_settings": False,
        "can_manage_integrations": False,
        "can_manage_automations": False,
        # Audit
        "can_view_audit_logs": False,
    },
    UserRole.VIEWER: {
        # User Management
        "can_view_users": False,
        "can_create_users": False,
        "can_edit_users": False,
        "can_delete_users": False,
        # Client Management
        "can_view_clients": True,
        "can_create_clients": False,
        "can_edit_clients": False,
        "can_delete_clients": False,
        # Shipment Management
        "can_view_shipments": True,
        "can_create_shipments": False,
        "can_edit_shipments": False,
        "can_delete_shipments": False,
        "can_update_shipment_status": False,
        # Analytics & Reports
        "can_view_analytics": False,
        "can_view_reports": False,
        "can_export_data": False,
        # Settings
        "can_manage_settings": False,
        "can_manage_integrations": False,
        "can_manage_automations": False,
        # Audit
        "can_view_audit_logs": False,
    },
}


def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission"""
    permissions = ROLE_PERMISSIONS.get(user.role, {})
    return permissions.get(permission, False)


def require_permission(permission: str):
    """Dependency to require a specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    return permission_checker


# Common permission dependencies
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_admin_or_manager(current_user: User = Depends(get_current_user)) -> User:
    """Require admin or manager role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Manager access required"
        )
    return current_user


# Specific permission dependencies for common operations
def can_view_users(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can view users"""
    if not has_permission(current_user, "can_view_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users"
        )
    return current_user


def can_create_users(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can create users"""
    if not has_permission(current_user, "can_create_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create users"
        )
    return current_user


def can_edit_users(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can edit users"""
    if not has_permission(current_user, "can_edit_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit users"
        )
    return current_user


def can_delete_users(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can delete users"""
    if not has_permission(current_user, "can_delete_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete users"
        )
    return current_user


def can_create_clients(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can create clients"""
    if not has_permission(current_user, "can_create_clients"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create clients"
        )
    return current_user


def can_edit_clients(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can edit clients"""
    if not has_permission(current_user, "can_edit_clients"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit clients"
        )
    return current_user


def can_delete_clients(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can delete clients"""
    if not has_permission(current_user, "can_delete_clients"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete clients"
        )
    return current_user


def can_create_shipments(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can create shipments"""
    if not has_permission(current_user, "can_create_shipments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create shipments"
        )
    return current_user


def can_edit_shipments(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can edit shipments"""
    if not has_permission(current_user, "can_edit_shipments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit shipments"
        )
    return current_user


def can_delete_shipments(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can delete shipments"""
    if not has_permission(current_user, "can_delete_shipments"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete shipments"
        )
    return current_user


def can_export_data(current_user: User = Depends(get_current_user)) -> User:
    """Check if user can export data"""
    if not has_permission(current_user, "can_export_data"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to export data"
        )
    return current_user
