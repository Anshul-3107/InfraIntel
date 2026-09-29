from django.conf import settings
from rest_framework import serializers


class InspectionRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)

    def validate_image(self, image):
        if image.size > settings.MAX_UPLOAD_BYTES:
            limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
            raise serializers.ValidationError(f"Image must be under {limit_mb} MB.")
        return image