from django.conf import settings
from rest_framework import serializers

from ml.risk.severity import assess

from .health_service import asset_health
from .models import Infrastructure, Inspection


class InspectionRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    infrastructure_id = serializers.IntegerField(required=False)

    def validate_image(self, image):
        if image.size > settings.MAX_UPLOAD_BYTES:
            limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
            raise serializers.ValidationError(f"Image must be under {limit_mb} MB.")
        return image

    def validate_infrastructure_id(self, value):
        if not Infrastructure.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Unknown infrastructure id.")
        return value


class InspectionSerializer(serializers.ModelSerializer):
    num_detections = serializers.SerializerMethodField()
    assessment = serializers.SerializerMethodField()
    inspector = serializers.SerializerMethodField()
    infrastructure = serializers.SerializerMethodField()
    asset_health = serializers.SerializerMethodField()

    class Meta:
        model = Inspection
        fields = [
            "id",
            "inspector",
            "image",
            "latitude",
            "longitude",
            "image_width",
            "image_height",
            "num_detections",
            "assessment",
            "infrastructure",
            "asset_health",
            "detections",
            "created_at",
        ]

    def get_num_detections(self, inspection):
        return len(inspection.detections)

    def get_assessment(self, inspection):
        return assess(
            inspection.detections, inspection.image_width, inspection.image_height
        )

    def get_inspector(self, inspection):
        return inspection.inspector.username if inspection.inspector else None

    def get_infrastructure(self, inspection):
        asset = inspection.infrastructure
        if asset is None:
            return None
        return {"id": asset.id, "name": asset.name, "auto_created": asset.auto_created}

    def get_asset_health(self, inspection):
        if inspection.infrastructure is None:
            return None
        return asset_health(inspection.infrastructure)


class InfrastructureSerializer(serializers.ModelSerializer):
    health = serializers.SerializerMethodField()
    recent_inspections = serializers.SerializerMethodField()

    class Meta:
        model = Infrastructure
        fields = [
            "id",
            "name",
            "asset_type",
            "latitude",
            "longitude",
            "construction_year",
            "auto_created",
            "health",
            "recent_inspections",
            "created_at",
        ]

    def get_health(self, asset):
        return asset_health(asset)

    def get_recent_inspections(self, asset):
        rows = []
        for i in asset.inspections.order_by("-created_at")[:5]:
            a = assess(i.detections, i.image_width, i.image_height)
            rows.append(
                {
                    "id": i.id,
                    "created_at": i.created_at,
                    "severity_score": a["severity_score"],
                    "priority": a["priority"],
                }
            )
        return rows