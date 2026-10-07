from django.conf import settings
from django.db import models


class Infrastructure(models.Model):
    class AssetType(models.TextChoices):
        ROAD = "road", "Road"
        BRIDGE = "bridge", "Bridge"
        OTHER = "other", "Other"

    # Set by staff in the dashboard; always wins over location_name.
    name = models.CharField(max_length=200, blank=True)
    # Place name from the phone's geocoder at the first inspection.
    location_name = models.CharField(max_length=255, blank=True, default="")
    asset_type = models.CharField(
        max_length=20, choices=AssetType.choices, default=AssetType.ROAD
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    construction_year = models.PositiveIntegerField(null=True, blank=True)
    auto_created = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def display_name(self):
        return self.name or self.location_name or f"Asset #{self.pk}"

    def __str__(self):
        return f"{self.display_name} ({self.latitude:.5f}, {self.longitude:.5f})"


class Inspection(models.Model):
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inspections",
    )
    infrastructure = models.ForeignKey(
        Infrastructure,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inspections",
    )
    image = models.ImageField(upload_to="inspections/%Y/%m/")
    latitude = models.FloatField()
    longitude = models.FloatField()
    # Where this photo was taken, as reported by the app. May be empty.
    location_name = models.CharField(max_length=255, blank=True, default="")
    image_width = models.PositiveIntegerField()
    image_height = models.PositiveIntegerField()
    detections = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inspection {self.pk} ({self.latitude}, {self.longitude})"