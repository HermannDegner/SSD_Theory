"""
SSD Theory Experimental Features

実験的機能 - Nano Coreエンジン

このパッケージには、SSD理論の実験的な実装が含まれています。
これらは研究・検証段階であり、APIが変更される可能性があります。
"""

from .nano_core_engine import NanoCoreEngine

__all__ = [
    'NanoCoreEngine',
]

__version__ = '0.9.0'  # Experimental

# Note: nano_core_engine_v9.py は旧バージョンのため、
# import非推奨。アーカイブ目的で保管。
