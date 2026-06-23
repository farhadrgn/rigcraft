from rest_framework import serializers
from .models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case, GPUBenchmark


class GPUBenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPUBenchmark
        fields = ['id', 'game', 'resolution', 'setting', 'fps']


class GPUSerializer(serializers.ModelSerializer):
    benchmarks = GPUBenchmarkSerializer(many=True, read_only=True)

    class Meta:
        model = GPU
        fields = ['id', 'name', 'brand', 'vram', 'tdp', 'benchmark_score',
                  'length_mm', 'price', 'shop_url', 'benchmarks']


class CPUSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPU
        fields = ['id', 'name', 'brand', 'socket', 'tdp', 'ddr_support',
                  'benchmark_score', 'price', 'shop_url']


class MotherboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motherboard
        fields = ['id', 'name', 'brand', 'socket', 'ddr_support',
                  'form_factor', 'price', 'shop_url']


class CPUCoolerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPUCooler
        fields = ['id', 'name', 'brand', 'cooler_type', 'tdp_support',
                  'socket_support', 'radiator_size_mm', 'price', 'shop_url']


class RAMSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAM
        fields = ['id', 'name', 'brand', 'capacity_gb', 'ddr_type',
                  'price', 'shop_url']


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ['id', 'name', 'brand', 'capacity_gb', 'storage_type',
                  'price', 'shop_url']


class PSUSerializer(serializers.ModelSerializer):
    class Meta:
        model = PSU
        fields = ['id', 'name', 'brand', 'wattage', 'efficiency_rating',
                  'price', 'shop_url']


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'name', 'brand', 'supported_form_factors',
                  'max_gpu_length_mm', 'max_radiator_size_mm', 'price', 'shop_url']