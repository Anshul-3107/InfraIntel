import logging
import tempfile
from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .detector_service import run_detection
from .geo import find_nearest
from .models import Infrastructure, Inspection
from .serializers import (
    InfrastructureSerializer,
    InspectionRequestSerializer,
    InspectionSerializer,
)
from .services import delete_inspection

logger = logging.getLogger(__name__)


def visible_inspections(user):
    """Staff see every inspection; inspectors see only their own."""
    qs = Inspection.objects.select_related("infrastructure", "inspector")
    return qs if user.is_staff else qs.filter(inspector=user)


class ThrottledTokenObtainPairView(TokenObtainPairView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "role": "staff" if user.is_staff else "inspector",
            }
        )


class InspectView(APIView):
    parser_classes = [MultiPartParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "inspect"

    def post(self, request):
        request_serializer = InspectionRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        image = data["image"]
        lat, lon = data["latitude"], data["longitude"]
        location_name = data.get("location_name", "")

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
                    latitude=lat,
                    longitude=lon,
                    auto_created=True,
                    location_name=location_name,
                )

        # An asset that has no place name yet takes the first one reported.
        # A name that is already there is never overwritten.
        if location_name and not asset.location_name:
            asset.location_name = location_name
            asset.save(update_fields=["location_name"])

        inspection = Inspection.objects.create(
            inspector=request.user,
            infrastructure=asset,
            image=image,
            latitude=lat,
            longitude=lon,
            location_name=location_name,
            image_width=result["image_size"]["width"],
            image_height=result["image_size"]["height"],
            detections=result["detections"],
        )

        response_serializer = InspectionSerializer(
            inspection, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class InspectionDetailView(RetrieveDestroyAPIView):
    """GET one inspection, or DELETE it (owner or staff only).

    The queryset is limited to what the user may see, so deleting someone
    else's inspection returns 404 and does not reveal that it exists.
    """

    serializer_class = InspectionSerializer

    def get_queryset(self):
        return visible_inspections(self.request.user)

    def perform_destroy(self, instance):
        delete_inspection(instance)


class InspectionListView(ListAPIView):
    serializer_class = InspectionSerializer

    def get_queryset(self):
        qs = visible_inspections(self.request.user)
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