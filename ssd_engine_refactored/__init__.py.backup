"""
SSD Engine Refactored
=====================

構造主観力学（SSD）の再構築版エンジン

モジュール構成:
- ssd_core_engine: 汎用計算エンジン (Phase 2)
- ssd_human_module: 人間心理特化モジュール (Phase 1+3)
- ssd_pressure_system: 多次元意味圧システム
- ssd_subjective_social_pressure: 主観的社会圧力計算 (Phase 6)
- ssd_nonlinear_transfer: 非線形層間変換 (Phase 7)
- ssd_subjective_society: 主観的社会システム (Phase 8/v8) ✨NEW

⚠️ DEPRECATED:
- ssd_social_dynamics: v5/v6の「神の視点」アプローチ（v8では廃止）
"""

__version__ = "8.0.0"
__author__ = "SSD Research Team"

# 汎用エンジン
from .ssd_core_engine import (
    SSDCoreEngine,
    SSDCoreParams,
    SSDCoreState,
    LeapType,
    create_default_state,
    create_custom_params
)

# 人間モジュール
from .ssd_human_module import (
    HumanAgent,
    HumanParams,
    HumanPressure,
    HumanLayer,
    HumanLeapType,
    NeurotransmitterMapper
)

# 社会ダイナミクス（v8で大幅更新）
# ⚠️ DEPRECATED: ssd_social_dynamics (v5/v6の「神の視点」アプローチ)
from .ssd_social_dynamics import (
    Society as _DeprecatedSociety,
    SocialCouplingParams as _DeprecatedSocialCouplingParams,
    RelationshipMatrix,  # v8でも使用
    RelationType,  # v8でも使用
    create_fear_contagion_scenario as _deprecated_fear_contagion,
    create_ideology_conflict_scenario as _deprecated_ideology_conflict,
    create_norm_propagation_scenario as _deprecated_norm_propagation
)

# ✨ NEW: v8 主観的社会圧力 (Phase 6)
from .ssd_subjective_social_pressure import (
    SubjectiveSocialPressureCalculator,
    ObservableSignal,
    ObservationContext,
    RelationshipType
)

# ✨ NEW: v8 非線形層間変換 (Phase 7)
from .ssd_nonlinear_transfer import (
    NonlinearInterlayerTransfer,
    TransferType
)

# ✨ NEW: v8 主観的社会システム (Phase 8)
from .ssd_subjective_society import (
    SubjectiveSociety,
    SignalGenerator,
    AgentState,
    create_subjective_fear_contagion_scenario,
    create_subjective_ideology_conflict_scenario
)

# 多次元意味圧システム
from .ssd_pressure_system import (
    MultiDimensionalPressure,
    PressureDimension,
    rank_pressure_calculator,
    score_pressure_calculator,
    time_pressure_calculator,
    survival_pressure_calculator,
    resource_pressure_calculator,
    social_pressure_calculator,
    physical_fatigue_calculator,
    ideological_pressure_calculator
)

__all__ = [
    # Core Engine (Phase 2)
    "SSDCoreEngine",
    "SSDCoreParams",
    "SSDCoreState",
    "LeapType",
    "create_default_state",
    "create_custom_params",
    
    # Human Module (Phase 1+3)
    "HumanAgent",
    "HumanParams",
    "HumanPressure",
    "HumanLayer",
    "HumanLeapType",
    "NeurotransmitterMapper",
    
    # ✨ v8 Subjective Society (Phase 8) - RECOMMENDED
    "SubjectiveSociety",
    "SignalGenerator",
    "AgentState",
    "create_subjective_fear_contagion_scenario",
    "create_subjective_ideology_conflict_scenario",
    
    # ✨ v8 Subjective Social Pressure (Phase 6)
    "SubjectiveSocialPressureCalculator",
    "ObservableSignal",
    "ObservationContext",
    "RelationshipType",
    
    # ✨ v8 Nonlinear Transfer (Phase 7)
    "NonlinearInterlayerTransfer",
    "TransferType",
    
    # Shared Components
    "RelationshipMatrix",
    "RelationType",
    
    # Pressure System
    "MultiDimensionalPressure",
    "PressureDimension",
    "rank_pressure_calculator",
    "score_pressure_calculator",
    "time_pressure_calculator",
    "survival_pressure_calculator",
    "resource_pressure_calculator",
    "social_pressure_calculator",
    "physical_fatigue_calculator",
    "ideological_pressure_calculator",
]

# Deprecation warnings
import warnings

def _deprecated_society_warning():
    warnings.warn(
        "ssd_social_dynamics.Society は v8 で廃止されました。"
        "SubjectiveSociety を使用してください。"
        "理由: 「神の視点」からの直接的な状態操作が理論的に不整合です。",
        DeprecationWarning,
        stacklevel=2
    )

# Backward compatibility (deprecated)
class Society(_DeprecatedSociety):
    def __init__(self, *args, **kwargs):
        _deprecated_society_warning()
        super().__init__(*args, **kwargs)

SocialCouplingParams = _DeprecatedSocialCouplingParams
create_fear_contagion_scenario = _deprecated_fear_contagion
create_ideology_conflict_scenario = _deprecated_ideology_conflict
create_norm_propagation_scenario = _deprecated_norm_propagation

