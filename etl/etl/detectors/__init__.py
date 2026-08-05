"""Detecção automática do marketplace de origem, a partir do cabeçalho do arquivo."""

from etl.detectors.base import MarketplaceDetector
from etl.detectors.registry import detect_marketplace

__all__ = ["MarketplaceDetector", "detect_marketplace"]
