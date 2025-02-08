from django.test import TestCase
from posts.Singleton.config_manager import ConfigManager
# Create your tests here.

class ConfigManagerTest(TestCase):
    def test_singleton_instance(self):
        config1 = ConfigManager()
        config2 = ConfigManager()

        assert config1 is config2  # Both instances should be the same
        config1.set_setting("DEFAULT_PAGE_SIZE", 50)
        assert config2.get_setting("DEFAULT_PAGE_SIZE") == 50
