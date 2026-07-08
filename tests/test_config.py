"""测试 config — 验证配置模块结构（mock maibot_sdk）。"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# 必须在导入 config 之前 mock maibot_sdk
_mock_sdk = MagicMock()
_mock_sdk.PluginConfigBase = type("PluginConfigBase", (), {})
_mock_sdk.Field = lambda *a, **kw: None
sys.modules["maibot_sdk"] = _mock_sdk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import importlib
import core.config as config_module


class TestConfigModule(unittest.TestCase):
    def setUp(self):
        importlib.reload(config_module)

    def test_module_imports(self):
        self.assertTrue(hasattr(config_module, "PluginSection"))
        self.assertTrue(hasattr(config_module, "SttConfig"))
        self.assertTrue(hasattr(config_module, "SenseVoiceSttPluginConfig"))

    def test_classes_exist(self):
        self.assertIsNotNone(config_module.PluginSection)
        self.assertIsNotNone(config_module.SttConfig)
        self.assertIsNotNone(config_module.SenseVoiceSttPluginConfig)


if __name__ == "__main__":
    unittest.main()
