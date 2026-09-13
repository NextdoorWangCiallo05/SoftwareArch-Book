"""pytest 全局配置：确保可从 backend 目录导入 app 包。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
