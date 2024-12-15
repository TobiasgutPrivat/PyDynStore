from Database import createNewObject, getObject, updateObject, clearOrphans, ObjectId
import importlib
from typing import Iterable
# obj.__class__ = type("DynamicClass", (OriginalClass,), {"__str__": custom_str})
# allows to not wrap it and have better intelisense 
# requires loading/unloading attributes
# not sure how to handle dict's, iterables, sets
# allows dunder method access by inheritence
# maybe also no issue with isinstance

# i don't think that i can handle data apart from __dict__
# actually possible (example list: list(self), self.clear(), self.extend(dbdata) )

def load_class(qualified_name: str) -> type:
    module_name, class_name = qualified_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

ExtendedClasses: dict[type,type] = {}

def make_dynamic_class(orgType: type) -> type:
    """Dynamically create a class with the required methods and ensure __class__ cell is available."""
    
    class ExtendDynamic(orgType):
        def _load(self):
            if not self._loaded:
                self._loaded = True
                self.__dict__.update(getObject(self._id))

        def _save(self):
            updateObject(self._id, self._getData())
            self._unload()

        def _getData(self):
            return {
                "__class__": f"{self.__class__.__bases__[0].__module__}.{self.__class__.__bases__[0].__name__}",
                **{key: value for key, value in self.__dict__.items() if key not in ["_id", "_loaded"]},
                "__listitems__": list(self.items() if isinstance(self, Iterable) else None),
                "__dictvalues__": list(self.values()) if isinstance(self, dict) else None
            }

        def _unload(self):
            if self._loaded:
                self.__dict__ = {"_id": self._id} if hasattr(self, "_id") else {}
                self._loaded = False

        def __getattr__(self, name):
            self._load()
            return super().__getattribute__(name)

        def __setattr__(self, name, value):
            if name not in ["_id", "_loaded"]:
                self._load()
            super().__setattr__(name, value)

        def __getstate__(self):
            self._unload()
            state = self.__dict__.copy()
            state["__class__"] = f"{self.__class__.__bases__[0].__module__}.{self.__class__.__bases__[0].__name__}"
            return state

        def __setstate__(self, state: dict):
            class_name = state.pop("__class__")
            loadClassExtension(load_class(class_name))
            self.__dict__.update(state)
    
    # Return the dynamically created class
    return ExtendDynamic

def loadClassExtension(base_class: type) -> type:
    if base_class not in ExtendedClasses:
        wrapped_class = make_dynamic_class(base_class)
        ExtendedClasses[base_class] = wrapped_class
    else:
        wrapped_class = ExtendedClasses[base_class]

    return wrapped_class

def loadId(id: ObjectId) -> object:
    data = getObject(id)
    class_name = data.pop("__class__")
    base_class = load_class(class_name)
    extended_Class = loadClassExtension(base_class)
    obj = object.__new__(extended_Class)
    obj.__dict__.update(data)
    obj._loaded = True
    obj._id = id
    return obj

def wrapProxy(obj: object, recursive: bool = True) -> object:
    if recursive:
        wrapSubObjects(obj) 

    #TODO probably need to exit for objects without __dict__
    #TODO maybe change proxy to only use loaded if __dict__ is allowed, but still extend it
    # if not hasattr(obj, '__dict__'):
    #     return obj

    if obj.__class__ in ExtendedClasses.values():
        return obj
    if obj.__class__ in ExtendedClasses:
        obj.__class__ = ExtendedClasses[obj.__class__]
        return obj
    extended_class = make_dynamic_class(obj.__class__)
    
    ExtendedClasses[obj.__class__] = extended_class
    obj.__class__ = extended_class
    obj._loaded = True
    obj._id = createNewObject(obj._getData())

    return obj

def wrapSubObjects(obj: object) -> object:
    if isinstance(obj, (type, int, str, float, complex, bool, bytes, bytearray, type(None))):
        return
    if hasattr(obj, '__dict__'):
        for k, v in obj.__dict__.items():
            obj.__dict__[k] = wrapProxy(v)
    elif isinstance(obj, dict):
        for val in obj.values():
            wrapProxy(val)
    elif isinstance(obj, (set,tuple,list)):
        for item in obj:
            wrapProxy(item)