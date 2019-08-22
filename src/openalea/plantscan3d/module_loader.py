import importlib.util
import sys

class ModuleLoader:

    def __init__(self, configFile: str):
        """
        :param configFile: Modules configuration file.
        """
        self.configFile = configFile
        self.modules = []

    def load(self):
        """
        Load all modules.
        :return: None
        """
        self.modules = []

        for name, path in self.__getLoadOrder():
            try:
                module = self.__loadModule(name, path)
            except:
                print('Could not load module:', name)
            else:
                self.modules.append((name, module))
                print('Loaded module:', name)

    def __getLoadOrder(self) -> list:
        """
        Get the module load order, by reading the configuration file.
        :return: list
        """
        loadOrder = []
        file = open(self.configFile, 'r')

        for config in file:
            try:
                name, path = config.rstrip('\n').split(':', 1)
            except:
                pass
            else:
                loadOrder.append((name, path))

        return loadOrder

    def __loadModule(self, name: str, path: str):
        """
        Load a module.
        :param name: Name of the module.
        :param path: Path to the module file.
        :return: object
        """
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
