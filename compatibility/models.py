from django.db import models

# Create your models here.
from components.models import CPU, GPU, GPUBenchmark


class BottleneckException(models.Model):
    """Empirically observed CPU/GPU/resolution results below 100% GPU
    utilization.

    Populated via manual testing of the full RigCraft CPU x GPU x
    resolution catalog, recording the actual observed GPU utilization
    percentage per combination rather than deriving it from benchmark
    scores. Any (cpu, gpu, resolution) combination with no matching row
    was measured directly during testing at 100% GPU utilization. See
    the README's "Design Decisions" section for the full reasoning
    behind this approach.

    Balanced / Minor / Major are derived from `gpu_utilization_percent`
    via the `level` property below, rather than stored separately, so
    the two can never drift out of sync.
    """

    BALANCED_MIN = 94
    MINOR_MIN = 84

    cpu = models.ForeignKey(CPU, on_delete=models.CASCADE)
    gpu = models.ForeignKey(GPU, on_delete=models.CASCADE)
    resolution = models.CharField(max_length=10, choices=GPUBenchmark.Resolution.choices)
    gpu_utilization_percent = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("cpu", "gpu", "resolution")

    @property
    def level(self):
        if self.gpu_utilization_percent >= self.BALANCED_MIN:
            return "Balanced"
        if self.gpu_utilization_percent >= self.MINOR_MIN:
            return "Minor"
        return "Major"

    def __str__(self):
        return f"{self.cpu} + {self.gpu} @ {self.resolution}: {self.gpu_utilization_percent}% ({self.level})"