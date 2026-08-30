from django.db import models

# Create your models here.
from components.models import CPU, GPU, GPUBenchmark


class BottleneckException(models.Model):
    """Empirically observed non-Balanced CPU/GPU pairings.

    Populated via manual testing of the full RigCraft CPU x GPU x resolution
    catalog, recording actual observed bottleneck severity per combination
    rather than deriving it from benchmark scores. Any (cpu, gpu, resolution)
    combination with no matching row showed no meaningful bottleneck in
    testing -> Balanced. See the README's "Design Decisions" section for the
    full reasoning behind this approach.
    """

    class Level(models.TextChoices):
        MINOR = "Minor", "Minor"
        MAJOR = "Major", "Major"

    cpu = models.ForeignKey(CPU, on_delete=models.CASCADE)
    gpu = models.ForeignKey(GPU, on_delete=models.CASCADE)
    resolution = models.CharField(max_length=10, choices=GPUBenchmark.Resolution.choices)
    level = models.CharField(max_length=10, choices=Level.choices)

    class Meta:
        unique_together = ("cpu", "gpu", "resolution")

    def __str__(self):
        return f"{self.cpu} + {self.gpu} @ {self.resolution}: {self.level}"