from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .compatibility import check_compatibility


class CompatibilityCheckView(APIView):

    def post(self, request):
        data = request.data

        # بررسی اینکه حداقل یه قطعه انتخاب شده باشه
        component_ids = [
            'gpu_id', 'cpu_id', 'motherboard_id',
            'cooler_id', 'ram_id', 'storage_id',
            'psu_id', 'case_id'
        ]
        if not any(data.get(key) for key in component_ids):
            return Response(
                {'error': 'حداقل یک قطعه باید انتخاب شده باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = check_compatibility(data)
        return Response(result, status=status.HTTP_200_OK)