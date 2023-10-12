import inspect
import os
from importlib.machinery import SourceFileLoader
from tala.utils.unicodify import unicodify
from tala.ddd.loading.ddd_loader import DddLoaderException


class MissingModuleException(Exception):
    pass


class PythonModuleLoader(object):
    def __init__(self, name):
        self._name = name

    def load_py_module_class(self, module_path, ParentClass):
        if os.path.exists(module_path):
            module = self._load_py_module(module_path)
            class_name = self._find_subclass_in_module(ParentClass, module)
            return getattr(module, class_name)
        else:
            raise MissingModuleException("%s missing in DDD %r at %r" % (module_path, self._name, os.getcwd()))

    def _load_py_module(self, module_filename):
        module_name = os.path.splitext(module_filename)[0]
        ddd_module_name = "%s_%s" % (self._name, module_name)
        try:
            return SourceFileLoader(ddd_module_name, module_filename).load_module()
        except IOError:
            raise DddLoaderException("failed to load module %r from %s" % (module_filename, os.getcwd()))

    def _find_subclass_in_module(self, BaseClass, module):
        all_module_classes = inspect.getmembers(module, inspect.isclass)
        classes = self._find_classes_defined_in_module(all_module_classes, module)
        subclasses = self._classes_of_base_class(classes, BaseClass)
        if not subclasses:
            raise DddLoaderException(
                "Could not find class %s in file %r" % (BaseClass.__name__, os.path.abspath(module.__file__))
            )
        if len(subclasses) > 1:
            raise DddLoaderException(
                "Expected one class with base class %r but found %s" % (BaseClass.__name__, unicodify(subclasses))
            )
        subclass = subclasses[0]
        return subclass.__name__

    def _find_classes_defined_in_module(self, classes, module):
        def is_class_defined_in_module(class_, module):
            return inspect.getmodule(class_).__name__ == module.__name__

        return [class_ for name, class_ in classes if is_class_defined_in_module(class_, module)]

    def _classes_of_base_class(self, classes, BaseClass):
        def base_classes_of(class_):
            return inspect.getmro(class_)

        return [class_ for class_ in classes if BaseClass in base_classes_of(class_)]
