from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    GPUViewSet, CPUViewSet, MotherboardViewSet,
    CPUCoolerViewSet, RAMViewSet, StorageViewSet,
    PSUViewSet, CaseViewSet
)

router = DefaultRouter()
router.register(r'gpus', GPUViewSet, basename='gpu')
router.register(r'cpus', CPUViewSet, basename='cpu')
router.register(r'motherboards', MotherboardViewSet, basename='motherboard')
router.register(r'coolers', CPUCoolerViewSet, basename='cooler')
router.register(r'rams', RAMViewSet, basename='ram')
router.register(r'storages', StorageViewSet, basename='storage')
router.register(r'psus', PSUViewSet, basename='psu')
router.register(r'cases', CaseViewSet, basename='case')

urlpatterns = [
    path('', include(router.urls)),
]