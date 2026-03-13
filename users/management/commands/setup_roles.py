from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from alerts.models import Alert
from cameras.models import Camera
from traffic.models import Traffic, TrafficPrediction
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = "Create default role groups and assign model permissions"

    def handle(self, *args, **options):
        model_map = {
            "camera": Camera,
            "traffic": Traffic,
            "vehicle": Vehicle,
            "alert": Alert,
            "trafficprediction": TrafficPrediction,
        }

        permission_map = self._build_permission_map(model_map)

        role_permissions = {
            "viewer": [
                "view_camera",
                "view_traffic",
                "view_vehicle",
                "view_alert",
                "view_trafficprediction",
            ],
            "operator": [
                "view_camera",
                "change_camera",
                "view_traffic",
                "add_traffic",
                "change_traffic",
                "view_vehicle",
                "add_vehicle",
                "change_vehicle",
                "view_alert",
                "add_alert",
                "change_alert",
                "view_trafficprediction",
                "add_trafficprediction",
            ],
            "admin": [
                "view_camera",
                "add_camera",
                "change_camera",
                "delete_camera",
                "view_traffic",
                "add_traffic",
                "change_traffic",
                "delete_traffic",
                "view_vehicle",
                "add_vehicle",
                "change_vehicle",
                "delete_vehicle",
                "view_alert",
                "add_alert",
                "change_alert",
                "delete_alert",
                "view_trafficprediction",
                "add_trafficprediction",
                "change_trafficprediction",
                "delete_trafficprediction",
            ],
        }

        for role_name, codenames in role_permissions.items():
            group, created = Group.objects.get_or_create(name=role_name)
            permissions = [permission_map[codename] for codename in codenames]
            group.permissions.set(permissions)
            group.save()
            state = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"{role_name} group {state}"))

        self.stdout.write(self.style.SUCCESS("Role setup completed."))

    def _build_permission_map(self, model_map):
        permission_map = {}
        for model_key, model_cls in model_map.items():
            content_type = ContentType.objects.get_for_model(model_cls)
            for action in ("view", "add", "change", "delete"):
                codename = f"{action}_{model_key}"
                permission_map[codename] = Permission.objects.get(
                    content_type=content_type,
                    codename=codename,
                )
        return permission_map
