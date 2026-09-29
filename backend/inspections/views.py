import tempfile
from pathlib import Path

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .detector_service import run_detection
from .models import Inspection
from .serializers import InspectionRequestSerializer, InspectionSerializer


class InspectView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        request_serializer = InspectionRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        image = data["image"]

        suffix = Path(image.name).suffix.lower() or ".jpg"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / f"upload{suffix}"
            with open(tmp_path, "wb") as f:
                for chunk in image.chunks():
                    f.write(chunk)
            result = run_detection(tmp_path)

        inspection = Inspection.objects.create(
            image=image,
            latitude=data["latitude"],
            longitude=data["longitude"],
            image_width=result["image_size"]["width"],
            image_height=result["image_size"]["height"],
            detections=result["detections"],
        )

        response_serializer = InspectionSerializer(
            inspection, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class InspectionDetailView(RetrieveAPIView):
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer