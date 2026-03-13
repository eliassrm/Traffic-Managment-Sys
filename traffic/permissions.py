from rest_framework.permissions import BasePermission


class CanGenerateTrafficPrediction(BasePermission):
    message = 'You do not have permission to generate traffic predictions.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_perm('traffic.add_trafficprediction')
