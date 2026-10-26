from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.extraction import ExtractionError
from .services.pipeline import analyze

MAX_TEXT_CHARS = 4000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class AnalyzeView(APIView):
    """POST /api/analyze/  -> JSON {"text": "..."}  or  multipart with an "image" file."""
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request):
        text = str(request.data.get("text") or "").strip()
        image = request.FILES.get("image")

        if not text and not image:
            return Response({"error": "Send prescription text or an image."},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(text) > MAX_TEXT_CHARS:
            return Response({"error": f"Text is too long (max {MAX_TEXT_CHARS} characters)."},
                            status=status.HTTP_400_BAD_REQUEST)

        image_bytes = mime_type = None
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                return Response({"error": "Image must be JPEG, PNG or WebP."},
                                status=status.HTTP_400_BAD_REQUEST)
            if image.size > MAX_IMAGE_BYTES:
                return Response({"error": "Image is too large (max 5 MB)."},
                                status=status.HTTP_400_BAD_REQUEST)
            image_bytes, mime_type = image.read(), image.content_type

        try:
            payload = analyze(text=text, image_bytes=image_bytes, mime_type=mime_type)
        except ExtractionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(payload)