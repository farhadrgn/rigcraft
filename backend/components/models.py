from django.db import models

# Create your models here.
class GPU(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    vram = models.IntegerField(help_text="e.g 8 is equall to 8 gigabyte VRAM")
    tdp = models.IntegerField(help_text="Power usage base in watt")
    benchmark_score = models.IntegerField(help_text="Approximate benchmark score")
    length_mm = models.IntegerField(help_text="Physical length in millimeters")
    price = models.IntegerField(help_text="Approximate price in iran market")
    shop_url = models.URLField(help_text="Link to the shop")

    def __str__(self):
        return self.name
    

class CPU(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    socket = models.CharField(max_length=50)
    tdp = models.IntegerField(help_text="Power usage in watt")
    ddr_support = models.CharField(max_length=20, help_text="e.g. DDR4 or DDR5")
    benchmark_score = models.IntegerField(help_text="Approximate score")
    price = models.IntegerField(help_text="Approximate price in iran market")
    shop_url = models.URLField()

def __str__(self):
    return self.name


class Motherboard(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    socket = models.CharField(max_length=50)
    ddr_support = models.CharField(max_length=20)
    form_factor = models.CharField(max_length=20, help_text="e.g. ATX")
    price = models.IntegerField()
    shop_url = models.URLField()

    def __str__(self):
        return self.name


class CPUCooler(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    cooler_type = models.CharField(max_length=20, help_text="AIO or Air")
    tdp_support = models.IntegerField(help_text="Max TDP that it can cool")
    socket_support = models.CharField(max_length=200, help_text="List of supported sockets comma seperated, e.g. 'LGA-1700, AM5'")
    radiator_size_mm = models.IntegerField(null=True, blank=True, help_text="AIO models only")
    price = models.IntegerField()
    shop_url = models.URLField()

    def __str__(self):
        return self.name


class RAM(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    capacity_gb = models.IntegerField()
    ddr_type = models.CharField(max_length=20)
    price = models.IntegerField()
    shop_url = models.URLField()

    def __str__(self):
        return self.name


class Storage(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    capacity_gb = models.IntegerField()
    storage_type = models.CharField(max_length=20, help_text="NVMe or SATA")
    price = models.IntegerField()
    shop_url = models.URLField()

    def __str__(self):
        return self.name


class PSU(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    wattage = models.IntegerField()
    efficiency_rating = models.CharField(max_length=30, help_text="e.g. 80+ Gold")
    price = models.IntegerField()
    shop_url = models.URLField()

    def __str__(self):
        return self.name


class Case(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    supported_form_factors = models.CharField(max_length=100, help_text="e.g. ATX")
    max_gpu_length_mm = models.IntegerField()
    max_radiator_size_mm = models.IntegerField(null=True, blank=True)
    price = models.IntegerField()
    shop_url = models.URLField()

    def __str__(self):
        return self.name
    

class GPUBenchmark(models.Model):
    RESOLUTION_CHOICES = [
        ('1080p', '1080p'),
        ('1440p', '1440p'),
        ('4K', '4K'),
    ]

    SETTING_CHOICES = [
        ('High', 'High'),
        ('Ultra', 'Ultra'),
    ]

    gpu = models.ForeignKey(GPU, on_delete=models.CASCADE, related_name='benchmarks')
    game = models.CharField(max_length=100)
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)
    setting = models.CharField(max_length=10, choices=SETTING_CHOICES)
    fps = models.IntegerField()

    def __str__(self):
        return f"{self.gpu.name} | {self.game} | {self.resolution} | {self.setting} | {self.fps} FPS"