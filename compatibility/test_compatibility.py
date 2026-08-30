from django.test import TestCase

from components.models import GPU, CPU, Motherboard, CPUCooler, RAM, PSU, Case
from compatibility.services import (
    check_socket_compatibility,
    check_ram_cpu_compatibility,
    check_ram_motherboard_compatibility,
    check_cooler_tdp_compatibility,
    check_cooler_socket_compatibility,
    check_gpu_case_compatibility,
    check_motherboard_case_compatibility,
    check_radiator_case_compatibility,
    check_psu_compatibility,
    check_compatibility,
    compute_bottleneck,
)


class SocketCompatibilityTests(TestCase):
    # Creating a temporary database with our data of components
    fixtures = ["components_data.json"]

    # Compatible motherboard and cpu socket test
    def test_matching_sockets_pass(self):
        cpu = CPU.objects.get(name="Intel Core i5-14600K")
        motherboard = Motherboard.objects.get(name="ROG STRIX Z790-A GAMING WIFI")
        # If it is compatible the check_socket_compatibility return None
        self.assertIsNone(check_socket_compatibility(cpu, motherboard))

    def test_mismatched_sockets_fail(self):
        cpu = CPU.objects.get(name="Intel Core i5-14600K")
        motherboard = Motherboard.objects.get(name="ROG STRIX X670E-F GAMING WIFI")
        result = check_socket_compatibility(cpu, motherboard)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "SOCKET_MISMATCH")


class RamCpuCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_ddr4_ram_with_dual_support_cpu_passes(self):
        """Intel 14th Gen supports both DDR4 and DDR5 -- this is a set
        membership check, not an equality check, so DDR4 RAM must pass
        even though DDR5 is also valid for this CPU."""
        cpu = CPU.objects.get(name="Intel Core i5-14600K")
        ram = RAM.objects.get(name="Corsair Vengeance DDR4 3200 16GB")
        self.assertIsNone(check_ram_cpu_compatibility(ram, cpu))

    def test_ddr4_ram_with_ddr5_only_cpu_fails(self):
        cpu = CPU.objects.get(name="Intel Core Ultra 5 245K")
        ram = RAM.objects.get(name="Kingston Fury Beast DDR4 3200 16GB")
        result = check_ram_cpu_compatibility(ram, cpu)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "RAM_CPU_DDR_MISMATCH")


class RamMotherboardCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_matching_ddr_type_passes(self):
        motherboard = Motherboard.objects.get(name="ASUS PRIME B760M-A AX DDR4")
        ram = RAM.objects.get(name="Kingston Fury Beast DDR4 3200 16GB")
        self.assertIsNone(check_ram_motherboard_compatibility(ram, motherboard))

    def test_mismatched_ddr_type_fails(self):
        motherboard = Motherboard.objects.get(name="ASUS PRIME B760M-A AX DDR4")
        ram = RAM.objects.get(name="Corsair Vengeance DDR5 5600 32GB")
        result = check_ram_motherboard_compatibility(ram, motherboard)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "RAM_MOBO_DDR_MISMATCH")


class CoolerTdpCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_sufficient_tdp_passes(self):
        cooler = CPUCooler.objects.get(name="Noctua NH-D15")
        cpu = CPU.objects.get(name="Intel Core i5-14600K")
        self.assertIsNone(check_cooler_tdp_compatibility(cooler, cpu))

    def test_insufficient_tdp_fails(self):
        cooler = CPUCooler.objects.get(name="Noctua NH-L9i")
        cpu = CPU.objects.get(name="AMD Ryzen 9 9950X")
        result = check_cooler_tdp_compatibility(cooler, cpu)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "COOLER_TDP_INSUFFICIENT")


class CoolerSocketCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_supported_socket_passes(self):
        cooler = CPUCooler.objects.get(name="Noctua NH-D15")
        cpu = CPU.objects.get(name="AMD Ryzen 5 7600X")
        self.assertIsNone(check_cooler_socket_compatibility(cooler, cpu))

    def test_unsupported_socket_fails(self):
        """NH-L9i's socket list has no AM5 -- it's an LGA-only low-profile
        cooler."""
        cooler = CPUCooler.objects.get(name="Noctua NH-L9i")
        cpu = CPU.objects.get(name="AMD Ryzen 5 7600X")
        result = check_cooler_socket_compatibility(cooler, cpu)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "COOLER_SOCKET_MISMATCH")


class GpuCaseCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_gpu_fits_passes(self):
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5070")
        case = Case.objects.get(name="NZXT H7 Flow")
        self.assertIsNone(check_gpu_case_compatibility(gpu, case))

    def test_oversized_gpu_fails(self):
        """No GPU in our real catalog is too long for any case in stock, so
        an oversized GPU is constructed here purely in memory (never saved)
        to exercise the failure path."""
        oversized_gpu = GPU(
            name="Hypothetical Oversized GPU",
            brand="NVIDIA",
            vram=24,
            tdp=450,
            benchmark_score_3d=9000,
            length_mm=999,
        )
        case = Case.objects.get(name="NZXT H210")
        result = check_gpu_case_compatibility(oversized_gpu, case)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "GPU_TOO_LONG")


class MotherboardCaseCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_supported_form_factor_passes(self):
        motherboard = Motherboard.objects.get(name="ROG STRIX Z790-A GAMING WIFI")
        case = Case.objects.get(name="NZXT H7 Flow")
        self.assertIsNone(check_motherboard_case_compatibility(motherboard, case))

    def test_unsupported_form_factor_fails(self):
        """Lian Li Dan A3 only supports Micro-ATX and Mini-ITX -- no ATX."""
        motherboard = Motherboard.objects.get(name="ROG STRIX Z790-A GAMING WIFI")
        case = Case.objects.get(name="Lian Li Dan A3")
        result = check_motherboard_case_compatibility(motherboard, case)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "MOBO_FORM_FACTOR_MISMATCH")


class RadiatorCaseCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_air_cooler_always_passes_regardless_of_case(self):
        """Air coolers have no radiator, so this rule must be skipped
        entirely for them -- never a violation, no matter the case."""
        cooler = CPUCooler.objects.get(name="Noctua NH-D15")
        case = Case.objects.get(name="NZXT H210")
        self.assertIsNone(check_radiator_case_compatibility(cooler, case))

    def test_fitting_radiator_passes(self):
        cooler = CPUCooler.objects.get(name="NZXT Kraken 240")
        case = Case.objects.get(name="NZXT H210")
        self.assertIsNone(check_radiator_case_compatibility(cooler, case))

    def test_oversized_radiator_fails(self):
        cooler = CPUCooler.objects.get(name="NZXT Kraken 360")
        case = Case.objects.get(name="NZXT H210")
        result = check_radiator_case_compatibility(cooler, case)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "RADIATOR_TOO_LARGE")


class PsuCompatibilityTests(TestCase):
    fixtures = ["components_data.json"]

    def test_sufficient_wattage_passes(self):
        cpu = CPU.objects.get(name="AMD Ryzen 5 9600X")
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5060")
        psu = PSU.objects.get(name="Corsair RM750e")
        self.assertIsNone(check_psu_compatibility(cpu, gpu, psu))

    def test_insufficient_wattage_fails(self):
        cpu = CPU.objects.get(name="Intel Core i9-14900K")
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5090")
        psu = PSU.objects.get(name="Corsair RM750e")
        result = check_psu_compatibility(cpu, gpu, psu)
        self.assertIsNotNone(result)
        self.assertEqual(result["reason_code"], "PSU_INSUFFICIENT")


class CheckCompatibilityDispatcherTests(TestCase):
    fixtures = ["components_data.json"]

    def test_fully_compatible_selection_reports_no_violations(self):
        selection = {
            "cpu": CPU.objects.get(name="Intel Core i5-14600K").pk,
            "gpu": GPU.objects.get(name="NVIDIA GeForce RTX 5070").pk,
            "motherboard": Motherboard.objects.get(name="ROG STRIX Z790-A GAMING WIFI").pk,
            "cooler": CPUCooler.objects.get(name="Noctua NH-D15").pk,
            "ram": RAM.objects.get(name="Corsair Vengeance DDR5 6000 32GB").pk,
            "psu": PSU.objects.get(name="Corsair RM850x").pk,
            "case": Case.objects.get(name="NZXT H7 Flow").pk,
        }
        result = check_compatibility(selection)
        self.assertTrue(result["compatible"])
        self.assertEqual(result["violations"], [])

    def test_multiple_incompatibilities_all_reported(self):
        selection = {
            "cpu": CPU.objects.get(name="Intel Core i9-14900K").pk,
            "gpu": GPU.objects.get(name="NVIDIA GeForce RTX 5090").pk,
            # Wrong socket on purpose: AM5 board with an LGA1700 CPU.
            "motherboard": Motherboard.objects.get(name="ROG STRIX X670E-F GAMING WIFI").pk,
            # Too small for a 14900K + 5090 combined draw.
            "psu": PSU.objects.get(name="Corsair RM750e").pk,
        }
        result = check_compatibility(selection)

        self.assertFalse(result["compatible"])
        reason_codes = {v["reason_code"] for v in result["violations"]}
        self.assertIn("SOCKET_MISMATCH", reason_codes)
        self.assertIn("PSU_INSUFFICIENT", reason_codes)

    def test_incomplete_selection_reports_no_violation_for_missing_side(self):
        """An in-progress wizard selection (only CPU + GPU chosen so far)
        must not report a violation for parts not picked yet."""
        selection = {
            "cpu": CPU.objects.get(name="Intel Core i5-14600K").pk,
            "gpu": GPU.objects.get(name="NVIDIA GeForce RTX 5070").pk,
        }
        result = check_compatibility(selection)
        self.assertTrue(result["compatible"])
        self.assertEqual(result["violations"], [])

    def test_empty_selection_is_trivially_compatible(self):
        result = check_compatibility({})
        self.assertTrue(result["compatible"])
        self.assertEqual(result["violations"], [])


class ComputeBottleneckTests(TestCase):
    fixtures = ["components_data.json", "bottleneck_exceptions.json"]

    def test_untested_combo_defaults_to_balanced(self):
        cpu = CPU.objects.get(name="AMD Ryzen 5 7600X")
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5070")
        self.assertEqual(compute_bottleneck(cpu, gpu, "1080p"), "Balanced")

    def test_rtx5090_1080p_always_major(self):
        """Even the catalog's strongest CPU never breaks 84% GPU
        utilization against the RTX 5090 at 1080p."""
        cpu = CPU.objects.get(name="AMD Ryzen 9 9950X")
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5090")
        self.assertEqual(compute_bottleneck(cpu, gpu, "1080p"), "Major")

    def test_dual_ccd_9900x_regression(self):
        """Ryzen 9 9900X (asymmetric dual-CCD, 6 active cores/CCD) tests
        worse than both weaker (9700X) and stronger (9950X) neighbors due
        to documented Zen 5 cross-CCD scheduling behavior. This is real
        data, not an error -- guards against 'cleaning up' it away."""
        cpu = CPU.objects.get(name="AMD Ryzen 9 9900X")
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5080")
        self.assertEqual(compute_bottleneck(cpu, gpu, "1080p"), "Minor")

    def test_arrow_lake_minor_on_rx9070(self):
        cpu = CPU.objects.get(name="Intel Core Ultra 5 245K")
        gpu = GPU.objects.get(name="AMD Radeon RX 9070")
        self.assertEqual(compute_bottleneck(cpu, gpu, "1080p"), "Minor")

    def test_resolution_shifts_result_toward_balanced(self):
        """Same pair: bottleneck at 1080p, resolves by 4K."""
        cpu = CPU.objects.get(name="Intel Core Ultra 5 245K")
        gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5090")
        self.assertEqual(compute_bottleneck(cpu, gpu, "1080p"), "Major")
        self.assertEqual(compute_bottleneck(cpu, gpu, "1440p"), "Major")
        self.assertEqual(compute_bottleneck(cpu, gpu, "4K"), "Balanced")