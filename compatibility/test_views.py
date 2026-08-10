import json

from django.test import TestCase
from django.urls import reverse

from components.models import GPU, CPU, Motherboard, PSU


class BuilderCheckViewTests(TestCase):
    fixtures = ["components_data.json"]

    def setUp(self):
        self.cpu = CPU.objects.get(name="Intel Core i5-14600K")
        self.gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5070")
        self.motherboard = Motherboard.objects.get(name="ROG STRIX Z790-A GAMING WIFI")
        self.wrong_motherboard = Motherboard.objects.get(name="ROG STRIX X670E-F GAMING WIFI")
        self.psu = PSU.objects.get(name="Corsair RM750e")

    def test_get_method_not_allowed(self):
        response = self.client.get(reverse("builder_check"))
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            reverse("builder_check"), data="not valid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_compatible_selection_reports_no_violations(self):
        payload = {
            "cpu": self.cpu.pk,
            "gpu": self.gpu.pk,
            "motherboard": self.motherboard.pk,
            "psu": self.psu.pk,
            "target_resolution": "1440p",
        }
        response = self.client.post(
            reverse("builder_check"), data=json.dumps(payload), content_type="application/json"
        )
        data = response.json()
        self.assertTrue(data["compatible"])
        self.assertEqual(data["violations"], [])

    def test_incompatible_selection_reports_violations(self):
        payload = {"cpu": self.cpu.pk, "motherboard": self.wrong_motherboard.pk}
        response = self.client.post(
            reverse("builder_check"), data=json.dumps(payload), content_type="application/json"
        )
        data = response.json()
        self.assertFalse(data["compatible"])
        reason_codes = {v["reason_code"] for v in data["violations"]}
        self.assertIn("SOCKET_MISMATCH", reason_codes)

    def test_bottleneck_is_null_without_target_resolution(self):
        payload = {"cpu": self.cpu.pk, "gpu": self.gpu.pk}
        response = self.client.post(
            reverse("builder_check"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertIsNone(response.json()["bottleneck_status"])

    def test_bottleneck_is_null_with_incomplete_cpu_gpu_pair(self):
        payload = {"cpu": self.cpu.pk, "target_resolution": "1440p"}
        response = self.client.post(
            reverse("builder_check"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertIsNone(response.json()["bottleneck_status"])

    def test_endpoint_is_stateless(self):
        """Same input posted twice must give the exact same output, and
        must never write anything to the database."""
        from builds.models import Build

        payload = {"cpu": self.cpu.pk, "gpu": self.gpu.pk, "target_resolution": "1440p"}
        response1 = self.client.post(
            reverse("builder_check"), data=json.dumps(payload), content_type="application/json"
        )
        response2 = self.client.post(
            reverse("builder_check"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response1.json(), response2.json())
        self.assertEqual(Build.objects.count(), 0)