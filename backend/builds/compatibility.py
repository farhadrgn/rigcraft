from components.models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case


def check_compatibility(data):
    """
    ورودی: دیکشنری شامل id قطعات انتخاب‌شده
    خروجی: دیکشنری شامل نتایج بررسی سازگاری
    """
    results = []
    is_compatible = True

    # گرفتن آبجکت‌های قطعات از دیتابیس
    gpu = _get_component(GPU, data.get('gpu_id'))
    cpu = _get_component(CPU, data.get('cpu_id'))
    motherboard = _get_component(Motherboard, data.get('motherboard_id'))
    cooler = _get_component(CPUCooler, data.get('cooler_id'))
    ram = _get_component(RAM, data.get('ram_id'))
    psu = _get_component(PSU, data.get('psu_id'))
    case = _get_component(Case, data.get('case_id'))

    # اجرای rule ها
    rules = [
        _check_cpu_motherboard_socket(cpu, motherboard),
        _check_cpu_ram_ddr(cpu, ram),
        _check_motherboard_ram_ddr(motherboard, ram),
        _check_cooler_cpu_tdp(cooler, cpu),
        _check_cooler_cpu_socket(cooler, cpu),
        _check_gpu_case_length(gpu, case),
        _check_motherboard_case_form_factor(motherboard, case),
        _check_cooler_case_radiator(cooler, case),
        _check_psu_wattage(psu, gpu, cpu, cooler, ram),
    ]

    for rule_result in rules:
        if rule_result is not None:
            results.append(rule_result)
            if rule_result['status'] == 'error':
                is_compatible = False

    # محاسبه Bottleneck
    bottleneck = _check_bottleneck(cpu, gpu)

    # محاسبه TDP کل
    total_tdp = _calculate_total_tdp(gpu, cpu, cooler, ram)

    return {
        'is_compatible': is_compatible,
        'results': results,
        'total_tdp': total_tdp,
        'bottleneck': bottleneck,
    }


def _get_component(model, component_id):
    """گرفتن یه قطعه از DB — اگه id نبود None برمی‌گردونه"""
    if not component_id:
        return None
    try:
        return model.objects.get(id=component_id)
    except model.DoesNotExist:
        return None


def _make_result(rule, status, message):
    """ساخت یه آبجکت نتیجه استاندارد"""
    return {
        'rule': rule,
        'status': status,
        'message': message,
    }


def _check_cpu_motherboard_socket(cpu, motherboard):
    if not cpu or not motherboard:
        return None
    if cpu.socket != motherboard.socket:
        return _make_result(
            rule='سوکت CPU و مادربرد',
            status='error',
            message=f'CPU با سوکت {cpu.socket} با مادربردی که سوکت {motherboard.socket} دارد سازگار نیست'
        )
    return _make_result(
        rule='سوکت CPU و مادربرد',
        status='ok',
        message=f'سوکت CPU و مادربرد هر دو {cpu.socket} هستند'
    )


def _check_cpu_ram_ddr(cpu, ram):
    if not cpu or not ram:
        return None
    if ram.ddr_type not in cpu.ddr_support:
        return _make_result(
            rule='نوع RAM و CPU',
            status='error',
            message=f'CPU از {cpu.ddr_support} پشتیبانی می‌کند اما RAM انتخابی {ram.ddr_type} است'
        )
    return _make_result(
        rule='نوع RAM و CPU',
        status='ok',
        message=f'CPU و RAM هر دو از {ram.ddr_type} پشتیبانی می‌کنند'
    )


def _check_motherboard_ram_ddr(motherboard, ram):
    if not motherboard or not ram:
        return None
    if ram.ddr_type not in motherboard.ddr_support:
        return _make_result(
            rule='نوع RAM و مادربرد',
            status='error',
            message=f'مادربرد از {motherboard.ddr_support} پشتیبانی می‌کند اما RAM انتخابی {ram.ddr_type} است'
        )
    return _make_result(
        rule='نوع RAM و مادربرد',
        status='ok',
        message=f'مادربرد و RAM هر دو از {ram.ddr_type} پشتیبانی می‌کنند'
    )


def _check_cooler_cpu_tdp(cooler, cpu):
    if not cooler or not cpu:
        return None
    if cooler.tdp_support < cpu.tdp:
        return _make_result(
            rule='ظرفیت خنک‌کننده',
            status='error',
            message=f'خنک‌کننده حداکثر {cooler.tdp_support} وات را پشتیبانی می‌کند اما TDP پردازنده {cpu.tdp} وات است'
        )
    return _make_result(
        rule='ظرفیت خنک‌کننده',
        status='ok',
        message=f'خنک‌کننده برای TDP پردازنده ({cpu.tdp} وات) مناسب است'
    )


def _check_cooler_cpu_socket(cooler, cpu):
    if not cooler or not cpu:
        return None
    supported_sockets = [s.strip() for s in cooler.socket_support.split(',')]
    if cpu.socket not in supported_sockets:
        return _make_result(
            rule='سوکت خنک‌کننده',
            status='error',
            message=f'خنک‌کننده از سوکت {cpu.socket} پشتیبانی نمی‌کند'
        )
    return _make_result(
        rule='سوکت خنک‌کننده',
        status='ok',
        message=f'خنک‌کننده از سوکت {cpu.socket} پشتیبانی می‌کند'
    )


def _check_gpu_case_length(gpu, case):
    if not gpu or not case:
        return None
    if gpu.length_mm > case.max_gpu_length_mm:
        return _make_result(
            rule='طول GPU در کیس',
            status='error',
            message=f'طول GPU ({gpu.length_mm}mm) از حداکثر فضای کیس ({case.max_gpu_length_mm}mm) بیشتر است'
        )
    return _make_result(
        rule='طول GPU در کیس',
        status='ok',
        message=f'GPU با طول {gpu.length_mm}mm در کیس جا می‌شود'
    )


def _check_motherboard_case_form_factor(motherboard, case):
    if not motherboard or not case:
        return None
    supported = [f.strip() for f in case.supported_form_factors.split(',')]
    if motherboard.form_factor not in supported:
        return _make_result(
            rule='فرم‌فاکتور مادربرد و کیس',
            status='error',
            message=f'مادربرد {motherboard.form_factor} در این کیس جا نمی‌شود'
        )
    return _make_result(
        rule='فرم‌فاکتور مادربرد و کیس',
        status='ok',
        message=f'مادربرد {motherboard.form_factor} با این کیس سازگار است'
    )


def _check_cooler_case_radiator(cooler, case):
    if not cooler or not case:
        return None
    if cooler.cooler_type != 'AIO':
        return None
    if not case.max_radiator_size_mm:
        return _make_result(
            rule='سایز رادیاتور در کیس',
            status='error',
            message='این کیس از AIO پشتیبانی نمی‌کند'
        )
    if cooler.radiator_size_mm > case.max_radiator_size_mm:
        return _make_result(
            rule='سایز رادیاتور در کیس',
            status='error',
            message=f'رادیاتور {cooler.radiator_size_mm}mm در این کیس جا نمی‌شود (حداکثر {case.max_radiator_size_mm}mm)'
        )
    return _make_result(
        rule='سایز رادیاتور در کیس',
        status='ok',
        message=f'رادیاتور {cooler.radiator_size_mm}mm در این کیس جا می‌شود'
    )


def _check_psu_wattage(psu, gpu, cpu, cooler, ram):
    if not psu:
        return None
    total = _calculate_total_tdp(gpu, cpu, cooler, ram)
    required = int(total / 0.8)
    if psu.wattage < required:
        return _make_result(
            rule='توان PSU',
            status='error',
            message=f'مصرف تخمینی سیستم {total} وات است. PSU حداقل {required} وات نیاز دارد اما {psu.wattage} وات است'
        )
    if psu.wattage < total * 1.1:
        return _make_result(
            rule='توان PSU',
            status='warning',
            message=f'PSU کافی است اما فضای کمی دارد. مصرف تخمینی {total} وات، توان PSU {psu.wattage} وات'
        )
    return _make_result(
        rule='توان PSU',
        status='ok',
        message=f'توان PSU ({psu.wattage} وات) برای این سیستم ({total} وات) مناسب است'
    )


def _calculate_total_tdp(gpu, cpu, cooler, ram):
    total = 0
    if gpu:
        total += gpu.tdp
    if cpu:
        total += cpu.tdp
    if ram:
        total += 10
    return total


def _check_bottleneck(cpu, gpu):
    if not cpu or not gpu:
        return None
    ratio = cpu.benchmark_score / gpu.benchmark_score

    if ratio < 0.7:
        status = 'cpu_bottleneck'
        message = f'CPU گلوگاه دارد. امتیاز CPU ({cpu.benchmark_score}) نسبت به GPU ({gpu.benchmark_score}) پایین است'
    elif ratio > 1.4:
        status = 'cpu_overkill'
        message = f'CPU قوی‌تر از نیاز GPU است. می‌توانید CPU ضعیف‌تری انتخاب کنید'
    else:
        status = 'balanced'
        message = 'تعادل مناسب بین CPU و GPU'

    return {
        'cpu_score': cpu.benchmark_score,
        'gpu_score': gpu.benchmark_score,
        'ratio': round(ratio, 2),
        'status': status,
        'message': message,
    }