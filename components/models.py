from django.db import models


# Graphic card database model
class GPU(models.Model):
    # Making a choice because there are only two graphic card brands that we have in our database and it is easier to use drop down in admin
    # Or just using Brand.NVIDIA or Brand.AMD in our codes
    class Brand(models.TextChoices):
        NVIDIA = "NVIDIA", "NVIDIA"
        AMD = "AMD", "AMD"

    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=10, choices=Brand.choices)
    vram = models.PositiveIntegerField(help_text="VRAM in GB")
    tdp = models.PositiveIntegerField(help_text="TDP in watts")
    benchmark_score_3d = models.PositiveIntegerField(
        help_text="3D Processing benchmark score from exo.ir"
    )
    length_mm = models.PositiveIntegerField(help_text="Physical card length in mm")

    # Using Meta class to create an ordering base of gpu benchmarks, using meta class makes that the gpu list order saves as this way as default
    class Meta:
        ordering = ["-benchmark_score_3d"]

    def __str__(self):
        return self.name


class CPU(models.Model):
    class Brand(models.TextChoices):
        INTEL = "Intel", "Intel"
        AMD = "AMD", "AMD"

    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=10, choices=Brand.choices)
    socket = models.CharField(max_length=20)
    tdp = models.PositiveIntegerField(help_text="TDP in watts")
    ddr_support = models.CharField(
        max_length=20, help_text="Comma-separated DDR types, e.g. 'DDR4,DDR5'"
    )
    benchmark_score_single_thread = models.PositiveIntegerField(
        help_text="PassMark single-thread rating from cpubenchmark.net"
    )

    class Meta:
        ordering = ["-benchmark_score_single_thread"]

    def __str__(self):
        return self.name

    def ddr_support_list(self):
        """Return ddr_support as a list, e.g. ['DDR4', 'DDR5']."""
        return [item.strip() for item in self.ddr_support.split(",")]


class Motherboard(models.Model):
    class FormFactor(models.TextChoices):
        ATX = "ATX", "ATX"
        MICRO_ATX = "Micro-ATX", "Micro-ATX"
        MINI_ITX = "Mini-ITX", "Mini-ITX"

    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=50)
    socket = models.CharField(max_length=20)
    ddr_support = models.CharField(max_length=10, help_text="Single value: DDR4 or DDR5")
    form_factor = models.CharField(max_length=20, choices=FormFactor.choices)
    chipset_tier_number = models.PositiveIntegerField(
        help_text="Numeric part of chipset name, e.g. Z790 -> 790"
    )

    class Meta:
        ordering = ["-chipset_tier_number"]

    def __str__(self):
        return self.name


class CPUCooler(models.Model):
    class CoolerType(models.TextChoices):
        AIR = "Air", "Air"
        AIO = "AIO", "AIO"

    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=CoolerType.choices)
    tdp_support = models.PositiveIntegerField(help_text="Max CPU TDP this cooler supports")
    socket_support = models.CharField(
        max_length=255, help_text="Comma-separated supported sockets, e.g. 'LGA1700,AM5'"
    )
    radiator_size_mm = models.PositiveIntegerField(
        null=True, blank=True, help_text="AIO only; null for Air coolers"
    )

    class Meta:
        ordering = ["-tdp_support"]

    def __str__(self):
        return self.name

    def socket_support_list(self):
        """Return socket_support as a list, e.g. ['LGA1700', 'AM5']."""
        return [item.strip() for item in self.socket_support.split(",")]


class RAM(models.Model):
    class DDRType(models.TextChoices):
        DDR4 = "DDR4", "DDR4"
        DDR5 = "DDR5", "DDR5"

    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=50)
    capacity_gb = models.PositiveIntegerField(help_text="16 or 32 GB only")
    ddr_type = models.CharField(max_length=10, choices=DDRType.choices)
    frequency_mhz = models.PositiveIntegerField()
    cas_latency = models.PositiveIntegerField()

    class Meta:
        ordering = ["-capacity_gb", "-frequency_mhz"]

    def __str__(self):
        return self.name


class Storage(models.Model):
    class InterfaceGeneration(models.TextChoices):
        GEN4 = "Gen4", "Gen4"
        GEN5 = "Gen5", "Gen5"

    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=50)
    capacity_gb = models.PositiveIntegerField()
    type = models.CharField(max_length=10, default="NVMe")
    interface_generation = models.CharField(max_length=10, choices=InterfaceGeneration.choices)
    read_speed_mbps = models.PositiveIntegerField()
    write_speed_mbps = models.PositiveIntegerField()

    class Meta:
        ordering = ["-read_speed_mbps"]

    def __str__(self):
        return self.name


class PSU(models.Model):
    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=50)
    wattage = models.PositiveIntegerField()
    efficiency_rating = models.CharField(max_length=30)

    class Meta:
        ordering = ["-wattage"]

    def __str__(self):
        return self.name


class Case(models.Model):
    name = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=50)
    supported_form_factors = models.CharField(
        max_length=100, help_text="Comma-separated, e.g. 'ATX,Micro-ATX,Mini-ITX'"
    )
    max_gpu_length_mm = models.PositiveIntegerField()
    max_radiator_size_mm = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    def supported_form_factors_list(self):
        """Return supported_form_factors as a list."""
        return [item.strip() for item in self.supported_form_factors.split(",")]


class GPUBenchmark(models.Model):
    class Resolution(models.TextChoices):
        FHD = "1080p", "1080p"
        QHD = "1440p", "1440p"
        UHD = "4K", "4K"

    gpu = models.ForeignKey(GPU, on_delete=models.CASCADE, related_name="benchmarks")
    game = models.CharField(max_length=100)
    resolution = models.CharField(max_length=10, choices=Resolution.choices)
    fps = models.PositiveIntegerField()

    class Meta:
        ordering = ["gpu", "game", "resolution"]

    def __str__(self):
        return f"{self.gpu.name} - {self.game} ({self.resolution})"