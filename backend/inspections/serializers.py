from django.conf import settings
from rest_framework import serializers

from ml.risk.severity import assess

from .models import Inspection


class InspectionRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)

    def validate_image(self, image):
        if image.size > settings.MAX_UPLOAD_BYTES:
            limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
            raise serializers.ValidationError(f"Image must be under {limit_mb} MB.")
        return image


class InspectionSerializer(serializers.ModelSerializer):
    num_detections = serializers.SerializerMethodField()
    assessment = serializers.SerializerMethodField()

    class Meta:
        model = Inspection
        fields = [
            "id",
            "image",
            "latitude",
            "longitude",
            "image_width",
            "image_height",
            "num_detections",
            "assessment",
            "detections",
            "created_at",
        ]

    def get_num_detections(self, inspection):
        return len(inspection.detections)

    def get_assessment(self, inspection):
        return assess(
            inspection.detections,
            inspection.image_width,
            inspection.image_height,
        )