# -*- coding: utf-8 -*-

import importlib
import sys
from time import sleep
from utils.Logger import STREAM


class PluginController:
    
    def __init__(self, gen_config):
        self.general_config = gen_config

    def load_plugins(self):
        lst_of_plugins = [plug.strip() for plug in self.general_config["enabled_plugins"].split(",")]
        STREAM.info("==> Checking plugins...")
        for plugin in lst_of_plugins:
            self.check_plugin(plugin)
        loaded_plugins = {}
        STREAM.info("==> Loading plugins...")
        for plugin in lst_of_plugins:
            loaded_plugins[plugin] = self.load_plugin(plugin)
        return loaded_plugins

    def load_plugin(self, plugin_name):        
        plugin = importlib.import_module("plugins.%s" % plugin_name)
        cls = getattr(plugin, "Keyword")
        STREAM.success(" -> Loading plugin <%s>..........OK" % plugin_name)
        sleep(0.3)
        return cls        

    def check_plugin(self, plugin_name):        
        try:
            plugin = importlib.import_module("plugins.%s" % plugin_name)
            cls = getattr(plugin, "Keyword")
            getattr(cls, "main")
            STREAM.success(" -> Checking plugin <%s>.........OK" % plugin_name)
        except ImportError as err:
            STREAM.warning(" -> Checking plugin <%s>.........FAILED" % plugin_name)
            STREAM.critical("  -> %s" % err)
            sys.exit()
        except AttributeError as err:
            STREAM.warning(" -> Checking plugin <%s>.........FAILED" % plugin_name)
            STREAM.critical("  -> %s" % err)
            sys.exit()
        finally:
            sleep(0.3)


if __name__ == "__main__":
    pass
