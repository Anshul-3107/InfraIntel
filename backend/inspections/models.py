from django.db import models


class Infrastructure(models.Model):
    class AssetType(models.TextChoices):
        ROAD = "road", "Road"
        BRIDGE = "bridge", "Bridge"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200, blank=True)
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

    def __str__(self):
        label = self.name or f"Asset {self.pk}"
        return f"{label} ({self.latitude:.5f}, {self.longitude:.5f})"


class Inspection(models.Model):
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
    image_width = models.PositiveIntegerField()
    image_height = models.PositiveIntegerField()
    detections = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inspection {self.pk} ({self.latitude}, {self.longitude})"