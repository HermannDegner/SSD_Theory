"""
SSD Theory Core Modules

コアモジュール - SSD理論の基本要素

このパッケージには、SSD理論の最も基本的な構成要素が含まれています。
すべてのSSD実装はこれらのコアモジュールの上に構築されます。
"""

from .ssd_core_engine import SSDAgent, SSDState
from .ssd_human_module import HumanAgent, HumanLayer, HumanPressure
from .ssd_pressure_system import PressureType, PressureSource
from .ssd_nonlinear_transfer import TransferFunction, TransferType

__all__ = [
    # Core Engine
    'SSDAgent',
    'SSDState',
    
    # Human Module
    'HumanAgent',
    'HumanLayer',
    'HumanPressure',
    
    # Pressure System
    'PressureType',
    'PressureSource',
    
    # Transfer Functions
    'TransferFunction',
    'TransferType',
]

__version__ = '1.0.0'
