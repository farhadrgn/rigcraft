from rest_framework import viewsets, filters
from .models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case
from .serializers import (
    GPUSerializer, CPUSerializer, MotherboardSerializer,
    CPUCoolerSerializer, RAMSerializer, StorageSerializer,
    PSUSerializer, CaseSerializer
)


class GPUViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GPU.objects.all()
    serializer_class = GPUSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price', 'vram', 'benchmark_score']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        brand = self.request.query_params.get('brand')
        max_price = self.request.query_params.get('max_price')
        min_vram = self.request.query_params.get('min_vram')

        if brand:
            queryset = queryset.filter(brand__icontains=brand)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if min_vram:
            queryset = queryset.filter(vram__gte=min_vram)

        return queryset


class CPUViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CPU.objects.all()
    serializer_class = CPUSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price', 'benchmark_score']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        brand = self.request.query_params.get('brand')
        socket = self.request.query_params.get('socket')
        max_price = self.request.query_params.get('max_price')

        if brand:
            queryset = queryset.filter(brand__icontains=brand)
        if socket:
            queryset = queryset.filter(socket__iexact=socket)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class MotherboardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Motherboard.objects.all()
    serializer_class = MotherboardSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        socket = self.request.query_params.get('socket')
        form_factor = self.request.query_params.get('form_factor')
        ddr_support = self.request.query_params.get('ddr_support')

        if socket:
            queryset = queryset.filter(socket__iexact=socket)
        if form_factor:
            queryset = queryset.filter(form_factor__iexact=form_factor)
        if ddr_support:
            queryset = queryset.filter(ddr_support__icontains=ddr_support)

        return queryset


class CPUCoolerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CPUCooler.objects.all()
    serializer_class = CPUCoolerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price', 'tdp_support']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        cooler_type = self.request.query_params.get('cooler_type')
        min_tdp_support = self.request.query_params.get('min_tdp_support')

        if cooler_type:
            queryset = queryset.filter(cooler_type__iexact=cooler_type)
        if min_tdp_support:
            queryset = queryset.filter(tdp_support__gte=min_tdp_support)

        return queryset


class RAMViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RAM.objects.all()
    serializer_class = RAMSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price', 'capacity_gb']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        ddr_type = self.request.query_params.get('ddr_type')
        min_capacity = self.request.query_params.get('min_capacity')

        if ddr_type:
            queryset = queryset.filter(ddr_type__iexact=ddr_type)
        if min_capacity:
            queryset = queryset.filter(capacity_gb__gte=min_capacity)

        return queryset


class StorageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price', 'capacity_gb']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        storage_type = self.request.query_params.get('storage_type')

        if storage_type:
            queryset = queryset.filter(storage_type__iexact=storage_type)

        return queryset


class PSUViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PSU.objects.all()
    serializer_class = PSUSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price', 'wattage']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        min_wattage = self.request.query_params.get('min_wattage')

        if min_wattage:
            queryset = queryset.filter(wattage__gte=min_wattage)

        return queryset


class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand']
    ordering_fields = ['price']
    ordering = ['price']

    def get_queryset(self):
        queryset = super().get_queryset()
        form_factor = self.request.query_params.get('form_factor')

        if form_factor:
            queryset = queryset.filter(supported_form_factors__icontains=form_factor)

        return queryset