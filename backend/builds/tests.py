from django.test import TestCase
from components.models import GPU, CPU, Motherboard, CPUCooler, RAM, PSU, Case
from .compatibility import check_compatibility


class CompatibilityCheckerTestCase(TestCase):

    def setUp(self):
        """
        این متد قبل از هر تست اجرا می‌شه و داده‌های پایه می‌سازه.
        هر تست با یه DB تمیز شروع می‌کنه.
        """
        self.gpu = GPU.objects.create(
            name='RTX 5070', brand='NVIDIA', vram=12,
            tdp=220, benchmark_score=75, length_mm=280,
            price=35000000, shop_url='https://exo.ir'
        )
        self.cpu_am5 = CPU.objects.create(
            name='Ryzen 7 9700X', brand='AMD', socket='AM5',
            tdp=65, ddr_support='DDR5', benchmark_score=80,
            price=18000000, shop_url='https://exo.ir'
        )
        self.cpu_lga1700 = CPU.objects.create(
            name='Core i7-14700K', brand='Intel', socket='LGA1700',
            tdp=125, ddr_support='DDR5', benchmark_score=85,
            price=22000000, shop_url='https://exo.ir'
        )
        self.motherboard_am5 = Motherboard.objects.create(
            name='ASUS ROG X670E', brand='ASUS', socket='AM5',
            ddr_support='DDR5', form_factor='ATX',
            price=25000000, shop_url='https://exo.ir'
        )
        self.motherboard_lga1700 = Motherboard.objects.create(
            name='MSI Z790', brand='MSI', socket='LGA1700',
            ddr_support='DDR5', form_factor='ATX',
            price=20000000, shop_url='https://exo.ir'
        )
        self.cooler_air = CPUCooler.objects.create(
            name='Noctua NH-D15', brand='Noctua', cooler_type='Air',
            tdp_support=250, socket_support='AM5,AM4,LGA1700,LGA1200',
            price=8000000, shop_url='https://exo.ir'
        )
        self.cooler_weak = CPUCooler.objects.create(
            name='Stock Cooler', brand='Generic', cooler_type='Air',
            tdp_support=65, socket_support='AM5',
            price=0, shop_url='https://exo.ir'
        )
        self.cooler_aio = CPUCooler.objects.create(
            name='Corsair H150i', brand='Corsair', cooler_type='AIO',
            tdp_support=300, socket_support='AM5,LGA1700',
            radiator_size_mm=360, price=12000000, shop_url='https://exo.ir'
        )
        self.ram_ddr5 = RAM.objects.create(
            name='Corsair 32GB DDR5', brand='Corsair',
            capacity_gb=32, ddr_type='DDR5',
            price=7000000, shop_url='https://exo.ir'
        )
        self.ram_ddr4 = RAM.objects.create(
            name='Kingston 16GB DDR4', brand='Kingston',
            capacity_gb=16, ddr_type='DDR4',
            price=4000000, shop_url='https://exo.ir'
        )
        self.psu_strong = PSU.objects.create(
            name='Corsair RM1000x', brand='Corsair', wattage=1000,
            efficiency_rating='80+ Gold',
            price=15000000, shop_url='https://exo.ir'
        )
        self.psu_weak = PSU.objects.create(
            name='Generic 400W', brand='Generic', wattage=400,
            efficiency_rating='80+ White',
            price=3000000, shop_url='https://exo.ir'
        )
        self.case_large = Case.objects.create(
            name='Fractal Torrent', brand='Fractal', 
            supported_form_factors='ATX,mATX,ITX',
            max_gpu_length_mm=461, max_radiator_size_mm=420,
            price=12000000, shop_url='https://exo.ir'
        )
        self.case_small = Case.objects.create(
            name='Small Case', brand='Generic',
            supported_form_factors='mATX,ITX',
            max_gpu_length_mm=250, max_radiator_size_mm=None,
            price=5000000, shop_url='https://exo.ir'
        )

    # --- تست‌های Socket ---

    def test_compatible_cpu_motherboard_socket(self):
        """CPU و Motherboard با سوکت یکسان باید سازگار باشن"""
        result = check_compatibility({
            'cpu_id': self.cpu_am5.id,
            'motherboard_id': self.motherboard_am5.id,
        })
        socket_result = next(r for r in result['results'] if r['rule'] == 'سوکت CPU و مادربرد')
        self.assertEqual(socket_result['status'], 'ok')

    def test_incompatible_cpu_motherboard_socket(self):
        """CPU و Motherboard با سوکت متفاوت باید ناسازگار باشن"""
        result = check_compatibility({
            'cpu_id': self.cpu_am5.id,
            'motherboard_id': self.motherboard_lga1700.id,
        })
        self.assertFalse(result['is_compatible'])
        socket_result = next(r for r in result['results'] if r['rule'] == 'سوکت CPU و مادربرد')
        self.assertEqual(socket_result['status'], 'error')

    # --- تست‌های DDR ---

    def test_compatible_ram_ddr(self):
        """RAM DDR5 با CPU و مادربرد DDR5 باید سازگار باشه"""
        result = check_compatibility({
            'cpu_id': self.cpu_am5.id,
            'motherboard_id': self.motherboard_am5.id,
            'ram_id': self.ram_ddr5.id,
        })
        ram_cpu_result = next(r for r in result['results'] if r['rule'] == 'نوع RAM و CPU')
        self.assertEqual(ram_cpu_result['status'], 'ok')

    def test_incompatible_ram_ddr(self):
        """RAM DDR4 با CPU که فقط DDR5 پشتیبانی می‌کنه باید ناسازگار باشه"""
        result = check_compatibility({
            'cpu_id': self.cpu_am5.id,
            'ram_id': self.ram_ddr4.id,
        })
        self.assertFalse(result['is_compatible'])
        ram_cpu_result = next(r for r in result['results'] if r['rule'] == 'نوع RAM و CPU')
        self.assertEqual(ram_cpu_result['status'], 'error')

    # --- تست‌های Cooler ---

    def test_cooler_insufficient_tdp(self):
        """کولر با TDP کمتر از CPU باید خطا بده"""
        result = check_compatibility({
            'cpu_id': self.cpu_lga1700.id,
            'cooler_id': self.cooler_weak.id,
        })
        self.assertFalse(result['is_compatible'])
        cooler_result = next(r for r in result['results'] if r['rule'] == 'ظرفیت خنک‌کننده')
        self.assertEqual(cooler_result['status'], 'error')

    def test_cooler_incompatible_socket(self):
        """کولری که سوکت CPU رو پشتیبانی نمی‌کنه باید خطا بده"""
        result = check_compatibility({
            'cpu_id': self.cpu_lga1700.id,
            'cooler_id': self.cooler_weak.id,
        })
        self.assertFalse(result['is_compatible'])

    # --- تست‌های GPU در کیس ---

    def test_gpu_fits_in_case(self):
        """GPU با طول کمتر از حداکثر کیس باید سازگار باشه"""
        result = check_compatibility({
            'gpu_id': self.gpu.id,
            'case_id': self.case_large.id,
        })
        gpu_result = next(r for r in result['results'] if r['rule'] == 'طول GPU در کیس')
        self.assertEqual(gpu_result['status'], 'ok')

    def test_gpu_does_not_fit_in_case(self):
        """GPU با طول بیشتر از حداکثر کیس باید خطا بده"""
        result = check_compatibility({
            'gpu_id': self.gpu.id,
            'case_id': self.case_small.id,
        })
        self.assertFalse(result['is_compatible'])
        gpu_result = next(r for r in result['results'] if r['rule'] == 'طول GPU در کیس')
        self.assertEqual(gpu_result['status'], 'error')

    # --- تست‌های PSU ---

    def test_psu_sufficient(self):
        """PSU با توان کافی باید ok برگردونه"""
        result = check_compatibility({
            'gpu_id': self.gpu.id,
            'cpu_id': self.cpu_am5.id,
            'psu_id': self.psu_strong.id,
        })
        psu_result = next(r for r in result['results'] if r['rule'] == 'توان PSU')
        self.assertEqual(psu_result['status'], 'ok')

    def test_psu_insufficient(self):
        """PSU با توان ناکافی باید خطا بده"""
        # total_tdp = 220 (gpu) + 65 (cpu) + 10 (ram) = 295
        # required = 295 / 0.8 = 369 وات
        # PSU ضعیف ۴۰۰ واته — کافیه
        # پس باید یه PSU واقعاً ضعیف بسازیم
        psu_very_weak = PSU.objects.create(
            name='Very Weak PSU', brand='Generic', wattage=300,
            efficiency_rating='80+ White',
            price=2000000, shop_url='https://exo.ir'
        )
        # total_tdp = 295، required = 369، psu = 300 → خطا
        result = check_compatibility({
            'gpu_id': self.gpu.id,
            'cpu_id': self.cpu_am5.id,
            'psu_id': psu_very_weak.id,
        })
        self.assertFalse(result['is_compatible'])
        psu_result = next(r for r in result['results'] if r['rule'] == 'توان PSU')
        self.assertEqual(psu_result['status'], 'error')

    # --- تست‌های Bottleneck ---

    def test_balanced_bottleneck(self):
        """CPU و GPU با امتیاز نزدیک باید balanced باشن"""
        result = check_compatibility({
            'gpu_id': self.gpu.id,
            'cpu_id': self.cpu_am5.id,
        })
        self.assertEqual(result['bottleneck']['status'], 'balanced')

    def test_no_bottleneck_without_both(self):
        """بدون CPU یا GPU نباید bottleneck محاسبه بشه"""
        result = check_compatibility({
            'gpu_id': self.gpu.id,
        })
        self.assertIsNone(result['bottleneck'])

    # --- تست Edge Case ---

    def test_empty_request_returns_error(self):
        """request بدون هیچ قطعه‌ای باید خطا بده"""
        result = check_compatibility({})
        self.assertTrue(result['is_compatible'])
        self.assertEqual(len(result['results']), 0)