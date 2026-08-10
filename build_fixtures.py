"""Convert raw component JSON files into a single Django fixture file.

Output: components/fixtures/components_data.json
"""
import json
from pathlib import Path

DATA_DIR = Path("components-data")
OUTPUT_PATH = Path("components/fixtures/components_data.json")

RESOLUTION_KEY_MAP = {
    "fhd_fps": "1080p",
    "2k_fps": "1440p",
    "4k_fps": "4K",
}

# Maps each per-GPU benchmark file to nothing extra -- the file's own "gpu"
# field already holds the exact full GPU name, so no manual mapping is needed.
GPU_BENCHMARK_FILES = [
    "rtx5060.json",
    "rtx5060ti.json",
    "rtx5070.json",
    "rtx5070ti.json",
    "rtx5080.json",
    "rtx5090.json",
    "rx9060xt.json",
    "rx9070.json",
    "rx9070xt.json",
]


# Open json file and convert it to dajngo dictionary or list or etc
def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def build_gpu_fixtures():
    specs = load_json("gpu-specs.json")
    scores_3d = load_json("gpu-benchmarks.json")

    entries = []
    name_to_pk = {}

    # "enumerate" is like a for loop but it make index, it means that with each eaterate
    # on the loop it create a primary key for each gpu
    for index, spec in enumerate(specs, start=1):
        pk = index
        # A list of all gpus names attached to their primary keys
        name_to_pk[spec["name"]] = pk

        # Match the short benchmark name (e.g. "RTX 5090") against the end
        # of the full spec name (e.g. "NVIDIA GeForce RTX 5090"). Using
        # endswith rather than substring avoids "RTX 5070" wrongly matching
        # inside "RTX 5070 Ti".
        matched_score = None
        for score_entry in scores_3d:
            if spec["name"].endswith(score_entry["name"]):
                matched_score = score_entry["benchmark"]
                break
        if matched_score is None:
            raise ValueError(f"No 3D benchmark score found for GPU: {spec['name']}")

        entries.append(
            {
                "model": "components.gpu",
                "pk": pk,
                "fields": {
                    "name": spec["name"],
                    "brand": spec["brand"],
                    "vram": spec["vram"],
                    "tdp": spec["tdp"],
                    "benchmark_score_3d": matched_score,
                    "length_mm": spec["length_mm"],
                },
            }
        )

    return entries, name_to_pk


def build_cpu_fixtures():
    items = load_json("cpu.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.cpu",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "socket": item["socket"],
                    "tdp": item["tdp"],
                    "ddr_support": ",".join(item["ddr_support"]),
                    "benchmark_score_single_thread": item["benchmark_score_single_thread"],
                },
            }
        )
    return entries


def build_motherboard_fixtures():
    items = load_json("motherboard.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.motherboard",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "socket": item["socket"],
                    "ddr_support": item["ddr_support"],
                    "form_factor": item["form_factor"],
                    "chipset_tier_number": item["chipset_tier_number"],
                },
            }
        )
    return entries


def build_cooler_fixtures():
    items = load_json("cooler.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.cpucooler",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "type": item["type"],
                    "tdp_support": item["tdp_support"],
                    "socket_support": ",".join(item["socket_support"]),
                    "radiator_size_mm": item["radiator_size_mm"],
                },
            }
        )
    return entries


def build_ram_fixtures():
    items = load_json("ram.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.ram",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "capacity_gb": item["capacity_gb"],
                    "ddr_type": item["ddr_type"],
                    "frequency_mhz": item["frequency_mhz"],
                    "cas_latency": item["cas_latency"],
                },
            }
        )
    return entries


def build_storage_fixtures():
    items = load_json("storage.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.storage",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "capacity_gb": item["capacity_gb"],
                    "type": item["type"],
                    "interface_generation": item["interface_generation"],
                    "read_speed_mbps": item["read_speed_mbps"],
                    "write_speed_mbps": item["write_speed_mbps"],
                },
            }
        )
    return entries


def build_psu_fixtures():
    items = load_json("psu.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.psu",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "wattage": item["wattage"],
                    "efficiency_rating": item["efficiency_rating"],
                },
            }
        )
    return entries


def build_case_fixtures():
    items = load_json("case.json")
    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            {
                "model": "components.case",
                "pk": index,
                "fields": {
                    "name": item["name"],
                    "brand": item["brand"],
                    "supported_form_factors": ",".join(item["supported_form_factors"]),
                    "max_gpu_length_mm": item["max_gpu_length_mm"],
                    "max_radiator_size_mm": item["max_radiator_size_mm"],
                },
            }
        )
    return entries


def build_gpu_benchmark_fixtures(gpu_name_to_pk):
    entries = []
    pk = 1
    for filename in GPU_BENCHMARK_FILES:
        data = load_json(filename)
        gpu_name = data["gpu"]
        if gpu_name not in gpu_name_to_pk:
            raise ValueError(f"GPU name '{gpu_name}' in {filename} not found in gpu-specs.json")
        gpu_pk = gpu_name_to_pk[gpu_name]

        for benchmark in data["benchmarks"]:
            for source_key, resolution in RESOLUTION_KEY_MAP.items():
                entries.append(
                    {
                        "model": "components.gpubenchmark",
                        "pk": pk,
                        "fields": {
                            "gpu": gpu_pk,
                            "game": benchmark["game"],
                            "resolution": resolution,
                            "fps": benchmark[source_key],
                        },
                    }
                )
                pk += 1
    return entries


def main():
    all_entries = []

    gpu_entries, gpu_name_to_pk = build_gpu_fixtures()
    all_entries += gpu_entries
    all_entries += build_cpu_fixtures()
    all_entries += build_motherboard_fixtures()
    all_entries += build_cooler_fixtures()
    all_entries += build_ram_fixtures()
    all_entries += build_storage_fixtures()
    all_entries += build_psu_fixtures()
    all_entries += build_case_fixtures()
    all_entries += build_gpu_benchmark_fixtures(gpu_name_to_pk)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    # Print a per-model count summary so the count can be sanity-checked
    # against the expected 85 components + benchmark rows.
    counts = {}
    for entry in all_entries:
        counts[entry["model"]] = counts.get(entry["model"], 0) + 1

    print(f"Wrote {len(all_entries)} total fixture entries to {OUTPUT_PATH}")
    for model, count in counts.items():
        print(f"  {model}: {count}")


if __name__ == "__main__":
    main()