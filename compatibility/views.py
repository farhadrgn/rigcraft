import json

from django.http import HttpResponseNotAllowed, JsonResponse

from components.models import CPU, GPU
from .services import check_compatibility, compute_bottleneck

VALID_CATEGORIES = {"gpu", "cpu", "motherboard", "cooler", "ram", "storage", "psu", "case"}


def builder_check(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    selection = {k: v for k, v in payload.items() if k in VALID_CATEGORIES}
    result = check_compatibility(selection)

    bottleneck_status = None
    resolution = payload.get("target_resolution")
    if "cpu" in selection and "gpu" in selection and resolution:
        cpu = CPU.objects.get(pk=selection["cpu"])
        gpu = GPU.objects.get(pk=selection["gpu"])
        bottleneck_status = compute_bottleneck(cpu, gpu, resolution)

    result["bottleneck_status"] = bottleneck_status
    return JsonResponse(result)