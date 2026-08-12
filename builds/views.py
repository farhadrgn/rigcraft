from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from components.models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case, GPUBenchmark
from .models import Build
from compatibility.services import compute_bottleneck

CATEGORY_FIELDS = ["gpu", "cpu", "motherboard", "cooler", "ram", "storage", "psu", "case"]


def home(request):
    return render(request, "home.html")


def builder(request):
    # First check if this build does exist, if does it means user want to edit it
    initial_build = None
    build_id = request.GET.get("build")
    if build_id and request.user.is_authenticated:
        initial_build = Build.objects.filter(pk=build_id, user=request.user).first()

    initial_selection = {}
    # If the build already exist prefill the build components so user can see what they choose before
    if initial_build:
        initial_selection = {
            "resolution": initial_build.target_resolution,
            "gpu": initial_build.gpu_id,
            "cpu": initial_build.cpu_id,
            "motherboard": initial_build.motherboard_id,
            "cooler": initial_build.cooler_id,
            "ram": initial_build.ram_id,
            "storage": initial_build.storage_id,
            "psu": initial_build.psu_id,
            "case": initial_build.case_id,
        }
    # Getting all components data from database as json format
    context = {
        "gpus_json": list(GPU.objects.values()),
        "cpus_json": list(CPU.objects.values()),
        "motherboards_json": list(Motherboard.objects.values()),
        "coolers_json": list(CPUCooler.objects.values()),
        "rams_json": list(RAM.objects.values()),
        "storages_json": list(Storage.objects.values()),
        "psus_json": list(PSU.objects.values()),
        "cases_json": list(Case.objects.values()),
        "gpu_benchmarks_json": list(GPUBenchmark.objects.values()),
        "initial_build": initial_build,
        "initial_selection_json": initial_selection,
    }
    return render(request, "builds/builder.html", context)


def builder_save(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.is_authenticated:
        messages.info(request, "Please log in to save your build.")
        return redirect("login")

    build_id = request.POST.get("build_id")
    if build_id:
        build = get_object_or_404(Build, pk=build_id, user=request.user)
    else:
        build = Build(user=request.user)

    build.name = request.POST.get("name", "My Build")
    build.target_resolution = request.POST.get("target_resolution")

    for category in CATEGORY_FIELDS:
        pk = request.POST.get(category)
        # Using setattr() witch stands for "set attribute" we can change the pk of components using one line
        # instead i writing so many line each for a component
        setattr(build, f"{category}_id", pk or None)

    # Every field (base fields + all 8 component FKs) is set on one
    # in-memory instance, then .save() is called exactly once -- for both
    # the create and the update path -- so component selections are never
    # silently discarded on creation.
    build.save()

    return redirect("build_detail", build_id=build.pk)


def build_list(request):
    if not request.user.is_authenticated:
        return redirect("login")
    builds = Build.objects.filter(user=request.user)
    return render(request, "builds/list.html", {"builds": builds})


def build_detail(request, build_id):
    if not request.user.is_authenticated:
        return redirect("login")
    build = get_object_or_404(Build, pk=build_id, user=request.user)
    components = [
        ("GPU", build.gpu),
        ("CPU", build.cpu),
        ("Motherboard", build.motherboard),
        ("Cooler", build.cooler),
        ("RAM", build.ram),
        ("Storage", build.storage),
        ("PSU", build.psu),
        ("Case", build.case),
    ]

    fps_rows = None
    if build.gpu and build.target_resolution:
        fps_rows = build.gpu.benchmarks.filter(resolution=build.target_resolution).order_by("-fps")

    bottleneck_status = None
    if build.cpu and build.gpu and build.target_resolution:
        bottleneck_status = compute_bottleneck(build.cpu, build.gpu, build.target_resolution)

    return render(
        request,
        "builds/detail.html",
        {
            "build": build,
            "components": components,
            "fps_rows": fps_rows,
            "bottleneck_status": bottleneck_status,
        },
    )


# Just check if the user is loged in and the build belongs to user or not
# and then redirect user to builder page
def build_edit(request, build_id):
    if not request.user.is_authenticated:
        return redirect("login")
    get_object_or_404(Build, pk=build_id, user=request.user)
    return redirect(f"/builder/?build={build_id}")


def build_delete(request, build_id):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    build = get_object_or_404(Build, pk=build_id, user=request.user)
    build.delete()
    return redirect("build_list")