"""Pure, stateless compatibility rule functions.

Each function takes model instances and returns either None (compatible)
or a dict {"reason_code": str, "message": str} describing the violation.
"""

# Approximates the combined power draw of motherboard, RAM, storage, and
# case fans/pump -- none of which have their own tdp field in the schema.
BASELINE_OVERHEAD_WATTS = 75

# The real-world PSU-sizing standard: never load a PSU past 80% of its
# rated wattage, to leave headroom for transient spikes and efficiency.
PSU_SAFETY_MARGIN = 0.8


def check_socket_compatibility(cpu, motherboard):
    if cpu.socket == motherboard.socket:
        return None
    return {
        "reason_code": "SOCKET_MISMATCH",
        "message": f"{cpu.name} ({cpu.socket}) does not fit {motherboard.name} ({motherboard.socket}).",
    }


def check_ram_cpu_compatibility(ram, cpu):
    if ram.ddr_type in cpu.ddr_support_list():
        return None
    return {
        "reason_code": "RAM_CPU_DDR_MISMATCH",
        "message": f"{cpu.name} does not support {ram.ddr_type} memory.",
    }


def check_ram_motherboard_compatibility(ram, motherboard):
    if ram.ddr_type == motherboard.ddr_support:
        return None
    return {
        "reason_code": "RAM_MOBO_DDR_MISMATCH",
        "message": f"{motherboard.name} requires {motherboard.ddr_support}, but {ram.name} is {ram.ddr_type}.",
    }


def check_cooler_tdp_compatibility(cooler, cpu):
    if cooler.tdp_support >= cpu.tdp:
        return None
    return {
        "reason_code": "COOLER_TDP_INSUFFICIENT",
        "message": f"{cooler.name} supports up to {cooler.tdp_support}W, but {cpu.name} has a TDP of {cpu.tdp}W.",
    }


def check_cooler_socket_compatibility(cooler, cpu):
    if cpu.socket in cooler.socket_support_list():
        return None
    return {
        "reason_code": "COOLER_SOCKET_MISMATCH",
        "message": f"{cooler.name} does not support the {cpu.socket} socket.",
    }


def check_gpu_case_compatibility(gpu, case):
    if gpu.length_mm <= case.max_gpu_length_mm:
        return None
    return {
        "reason_code": "GPU_TOO_LONG",
        "message": f"{gpu.name} is {gpu.length_mm}mm long, but {case.name} only fits up to {case.max_gpu_length_mm}mm.",
    }


def check_motherboard_case_compatibility(motherboard, case):
    if motherboard.form_factor in case.supported_form_factors_list():
        return None
    return {
        "reason_code": "MOBO_FORM_FACTOR_MISMATCH",
        "message": f"{case.name} does not support the {motherboard.form_factor} form factor.",
    }


def check_radiator_case_compatibility(cooler, case):
    # Air coolers have no radiator, so this rule simply does not apply to
    # them -- always compatible, regardless of the case.
    if cooler.type != "AIO":
        return None
    if cooler.radiator_size_mm <= case.max_radiator_size_mm:
        return None
    return {
        "reason_code": "RADIATOR_TOO_LARGE",
        "message": f"{cooler.name}'s {cooler.radiator_size_mm}mm radiator does not fit {case.name} (max {case.max_radiator_size_mm}mm).",
    }


def check_psu_compatibility(cpu, gpu, psu):
    total_draw = cpu.tdp + gpu.tdp + BASELINE_OVERHEAD_WATTS
    safe_capacity = psu.wattage * PSU_SAFETY_MARGIN
    if total_draw <= safe_capacity:
        return None
    return {
        "reason_code": "PSU_INSUFFICIENT",
        "message": (
            f"Estimated draw ({total_draw}W) exceeds {psu.name}'s safe capacity "
            # ":.0f" means round up and showing as a non float like 420.9 will be 421 and 500.0 will be 500
            f"({safe_capacity:.0f}W at {int(PSU_SAFETY_MARGIN * 100)}% of {psu.wattage}W rated)."
        ),
    }


from components.models import GPU, CPU, Motherboard, CPUCooler, RAM, PSU, Case

CATEGORY_MODELS = {
    "gpu": GPU,
    "cpu": CPU,
    "motherboard": Motherboard,
    "cooler": CPUCooler,
    "ram": RAM,
    "psu": PSU,
    "case": Case,
}


def check_compatibility(selection):
    """selection: dict mapping category name -> primary key, e.g.
    {"cpu": 3, "gpu": 1, "motherboard": 5, ...}. Only categories present
    in the dict are considered "chosen" -- a rule only runs when every
    component it needs is present; an incomplete build simply produces no
    violation for the missing side (expected mid-wizard state, not a
    compatibility failure).

    Deliberately category-keyed (not a flat set of PKs) so components
    from different categories can never be confused with each other, even
    if their numeric PKs happen to coincide.
    """
    parts = {
        category: model.objects.get(pk=selection[category])
        for category, model in CATEGORY_MODELS.items()
        if category in selection
    }

    violations = []

    if "cpu" in parts and "motherboard" in parts:
        result = check_socket_compatibility(parts["cpu"], parts["motherboard"])
        if result:
            violations.append(result)

    if "ram" in parts and "cpu" in parts:
        result = check_ram_cpu_compatibility(parts["ram"], parts["cpu"])
        if result:
            violations.append(result)

    if "ram" in parts and "motherboard" in parts:
        result = check_ram_motherboard_compatibility(parts["ram"], parts["motherboard"])
        if result:
            violations.append(result)

    if "cooler" in parts and "cpu" in parts:
        result = check_cooler_tdp_compatibility(parts["cooler"], parts["cpu"])
        if result:
            violations.append(result)
        result = check_cooler_socket_compatibility(parts["cooler"], parts["cpu"])
        if result:
            violations.append(result)

    if "gpu" in parts and "case" in parts:
        result = check_gpu_case_compatibility(parts["gpu"], parts["case"])
        if result:
            violations.append(result)

    if "motherboard" in parts and "case" in parts:
        result = check_motherboard_case_compatibility(parts["motherboard"], parts["case"])
        if result:
            violations.append(result)

    if "cooler" in parts and "case" in parts:
        result = check_radiator_case_compatibility(parts["cooler"], parts["case"])
        if result:
            violations.append(result)

    if "cpu" in parts and "gpu" in parts and "psu" in parts:
        result = check_psu_compatibility(parts["cpu"], parts["gpu"], parts["psu"])
        if result:
            violations.append(result)

    return {"compatible": len(violations) == 0, "violations": violations}


from django.db.models import Max

# 10 percent bottleneck
MINOR_THRESHOLD = 10
# 25 percent bottleneck
MAJOR_THRESHOLD = 25

# In 1080p resoluttion there is more pressure on cpu and less pressure on gpu
# In 1440p resoluttion there is a ballance pressure on cpu and gpu
# In 4k resoluttion there is more pressure on gpu and less pressure on cpu
RESOLUTION_SENSITIVITY = {
    "1080p": {"gpu_weak_multiplier": 0.8, "cpu_weak_multiplier": 1.2},
    "1440p": {"gpu_weak_multiplier": 1.0, "cpu_weak_multiplier": 1.0},
    "4K": {"gpu_weak_multiplier": 1.3, "cpu_weak_multiplier": 0.7},
}


def compute_bottleneck(cpu, gpu, resolution):
    """Purely informational -- never blocks a build selection.

    This is a heuristic, not a physical performance simulation: no
    official industry-standard bottleneck formula exists. The resolution
    sensitivity multipliers below are reasoned estimates (games lean more
    CPU-bound at 1080p and more GPU-bound at 4K), not measured constants.
    The formula also assumes a roughly linear relationship between
    benchmark score and real-world FPS impact -- it does not model
    diminishing returns at the high end, and it ignores VRAM capacity,
    RAM speed, and the specific game/engine being played.
    """
    max_cpu_score = CPU.objects.aggregate(Max("benchmark_score_single_thread"))[
        "benchmark_score_single_thread__max"
    ]
    max_gpu_score = GPU.objects.aggregate(Max("benchmark_score_3d"))["benchmark_score_3d__max"]

    cpu_percent = (cpu.benchmark_score_single_thread / max_cpu_score) * 100
    gpu_percent = (gpu.benchmark_score_3d / max_gpu_score) * 100

    # Computed before any resolution weighting: a perfectly matched pair
    # (both at 100% of their category) always starts from a diff of 0.
    raw_diff = cpu_percent - gpu_percent

    sensitivity = RESOLUTION_SENSITIVITY[resolution]
    if raw_diff > 0:
        # CPU relatively stronger than GPU -> GPU is the weaker link.
        adjusted_diff = raw_diff * sensitivity["gpu_weak_multiplier"]
    elif raw_diff < 0:
        # GPU relatively stronger than CPU -> CPU is the weaker link.
        adjusted_diff = raw_diff * sensitivity["cpu_weak_multiplier"]
    else:
        adjusted_diff = 0

    magnitude = abs(adjusted_diff)

    if magnitude < MINOR_THRESHOLD:
        return "Balanced"
    if adjusted_diff > 0:
        return "Major GPU Bottleneck" if magnitude >= MAJOR_THRESHOLD else "Minor GPU Bottleneck"
    return "Major CPU Bottleneck" if magnitude >= MAJOR_THRESHOLD else "Minor CPU Bottleneck"