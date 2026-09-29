from django.db import models


class Inspection(models.Model):
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