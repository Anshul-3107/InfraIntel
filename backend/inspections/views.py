import logging
import tempfile
from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .detector_service import run_detection
from .geo import find_nearest
from .models import Infrastructure, Inspection
from .serializers import (
    InfrastructureSerializer,
    InspectionRequestSerializer,
    InspectionSerializer,
)

logger = logging.getLogger(__name__)


class InspectView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        request_serializer = InspectionRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        image = data["image"]
        lat, lon = data["latitude"], data["longitude"]

        suffix = Path(image.name).suffix.lower() or ".jpg"
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / f"upload{suffix}"
                with open(tmp_path, "wb") as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                result = run_detection(tmp_path)
        except Exception:
            logger.exception("Damage detection failed")
            return Response(
                {"detail": "Could not process the image."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        asset_id = data.get("infrastructure_id")
        if asset_id is not None:
            asset = Infrastructure.objects.get(pk=asset_id)
        else:
            asset, _ = find_nearest(
                Infrastructure.objects.all(), lat, lon, settings.ASSET_MATCH_RADIUS_M
            )
            if asset is None:
                asset = Infrastructure.objects.create(
                    latitude=lat, longitude=lon, auto_created=True
                )

        inspection = Inspection.objects.create(
            infrastructure=asset,
            image=image,
            latitude=lat,
            longitude=lon,
            image_width=result["image_size"]["width"],
            image_height=result["image_size"]["height"],
            detections=result["detections"],
        )

        response_serializer = InspectionSerializer(inspection, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class InspectionDetailView(RetrieveAPIView):
    queryset = Inspection.objects.select_related("infrastructure")
    serializer_class = InspectionSerializer


class InspectionListView(ListAPIView):
    serializer_class = InspectionSerializer

    def get_queryset(self):
        qs = Inspection.objects.select_related("infrastructure")
        asset_id = self.request.query_params.get("infrastructure")
        if asset_id and asset_id.isdigit():
            qs = qs.filter(infrastructure_id=int(asset_id))
        return qs


class InfrastructureListView(ListAPIView):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer


class InfrastructureDetailView(RetrieveAPIView):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer