"""
SSD Theory Extensions

拡張モジュール - 社会的相互作用と高度な機能

このパッケージには、SSD理論を社会システムや複雑な相互作用に
拡張するためのモジュールが含まれています。
"""

from .ssd_social_dynamics import SocialAgent, SocialNetwork
from .ssd_subjective_social_pressure import SubjectiveSocialPressure
from .ssd_subjective_society import SubjectiveSociety
from .ssd_dynamic_interpretation import DynamicInterpreter
from .ssd_memory_structure import MemoryStructure, MemoryLayer

__all__ = [
    # Social Dynamics
    'SocialAgent',
    'SocialNetwork',
    
    # Subjective Social
    'SubjectiveSocialPressure',
    'SubjectiveSociety',
    
    # Advanced Features
    'DynamicInterpreter',
    'MemoryStructure',
    'MemoryLayer',
]

__version__ = '1.0.0'
