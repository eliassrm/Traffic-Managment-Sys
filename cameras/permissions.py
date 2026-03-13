from rest_framework.permissions import BasePermission


class CanIngestCameraData(BasePermission):
    message = 'You do not have permission to ingest camera data.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_perm('traffic.add_traffic') and user.has_perm('vehicles.add_vehicle')
