import tempfile
from pathlib import Path

from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .detector_service import run_detection
from .serializers import InspectionRequestSerializer


class InspectView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = InspectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data["image"]
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]

        suffix = Path(image.name).suffix.lower() or ".jpg"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / f"upload{suffix}"
            with open(tmp_path, "wb") as f:
                for chunk in image.chunks():
                    f.write(chunk)
            result = run_detection(tmp_path)

        result["image"] = Path(image.name).name  # detector saw "upload.jpg"
        result["location"] = {"latitude": latitude, "longitude": longitude}
        return Response(result)