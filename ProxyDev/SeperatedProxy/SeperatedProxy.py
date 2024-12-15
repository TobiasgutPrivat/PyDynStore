from Database import createNewObject, getObject, updateObject, deleteObject
from typing import Iterable
# !!! Debugging can cause unintended loading !!!

#TODO think about how to handle referenced objects in memory
#should work when already proxied, only issue when multiple references in memory and then both get proxied
#maybe solvable by using objectid assuming it's same when referenece is the same

class ObjectProxy:
    _id: int  # take from qdrant
    # _packages: list[str] # TODO track packages needed to import when loading object
    # also think about form of import, because dill references it in according scope
    _obj: object
    _loaded: bool

    def __init__(self, obj=None):
        """
        :param obj: If an existing object is passed, it will be wrapped by the proxy.
        """
        self._id = id(obj)
        createNewObject(self._id, obj)
        self._loaded = True
        self._obj = obj
        self._WrapSubObjects()

    def _WrapSubObjects(self):
        for k, v in self._obj.__dict__.items():
            self._obj.__dict__[k] = wrapProxy(v)

    def _load(self):
        """Loads the object from disk."""
        if not self._loaded:
            self._obj = getObject(self._id)
            self._loaded = True

    def _save(self):
        """Saves the object to disk."""
        updateObject(self._id, self._obj)
        self._unload() #(optional)

    def _unload(self):
        """Unloads the object without saving."""
        if not self._loaded:
            return
        
        # Recursively unload sub-objects
        # if isinstance(self._obj, dict):
        #     for value in self._obj.values():
        #         unloadProxy(value)
        # elif isinstance(self._obj, (list, set, tuple)):
        #     for item in self._obj:
        #         unloadProxy(item)
        # elif hasattr(self._obj, '__slots__'):
        #     for slot in self._obj.__slots__:
        #         value = getattr(self._obj, slot)
        #         unloadProxy(value)
        self._unloadSubObjects()
        
        self._obj = None
        self._loaded = False

    def _unloadSubObjects(self):
        for attr_value in self._obj.__dict__.values():
            if isinstance(attr_value, ObjectProxy):
                attr_value._unload()

    def __getstate__(self): #always store subobjects unloaded
        self._unload()
        return self.__dict__.copy() #(uses __dict__ of DynamicProxy)

    def __setstate__(self, state): #load into __dict__
        self.__dict__.update(state)

    def __getattr__(self, name): #only called if attribute not found in Dynamicproxy
        self._load()
        return getattr(self._obj, name)

    def __setattr__(self, name, value):
        if name in ['_id', '_packages', '_obj', '_loaded']:
            super().__setattr__(name, value)
        else:
            self._load()
            setattr(self._obj, name, wrapProxy(value))
            self._save()  # Automatically save after modifying

    def __delattr__(self, name):
        if name in ['_id', '_packages', '_obj', '_loaded']:
            super().__delattr__(name)
        else:
            self._load()  # Load the object before deleting any attributes
            delattr(self._obj, name)
            self._save()

    def __getitem__(self, key):#TODO potentialy unnecessary
        self._load()  # Load the object when an item is accessed
        return self._obj[key]

    def __setitem__(self, key, value):
        self._load()  # Load the object before setting any item
        self._obj[key] = wrapProxy(value)
        self._save()  # Automatically save after modifying

    def __delitem__(self, key):
        self._load()  # Load the object before deleting an item
        del self._obj[key]
        self._save()

    def __call__(self, *args, **kwargs):#TODO potentialy unnecessary
        self._load()  # If the object is callable (has a __call__ method), call it
        return self._obj(*args, **kwargs)

    def __str__(self):#TODO potentialy unnecessary
        self._load()
        return self._obj.__str__()

    def __repr__(self):
        attrs = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
    
    def _delete(self): #TODO think about when to delete
        # if isinstance(self._obj, dict):
        #     for value in self._obj.values():
        #         deleteProxy(value)
        # elif isinstance(self._obj, (list, set, tuple)):
        #     for item in self._obj:
        #         deleteProxy(item)
        # elif hasattr(self._obj, '__slots__'):
        #     for slot in self._obj.__slots__:
        #         value = getattr(self._obj, slot)
        #         deleteProxy(value)
        # elif hasattr(self._obj, '__dict__'):
        self._deleteSubObjects()
        deleteObject(self._id) 

    def _deleteSubObjects(self):
        for attr_value in self._obj.__dict__.values():
            if isinstance(attr_value, ObjectProxy):
                attr_value._delete()

    def _untrack(self) -> object:
        obj = self._obj
        del self
        return obj
    
    #TODO handle more dunders
    # dunders which only would require loading can be ignored because, get handled by getattr if not found

# def deleteProxy(value):
#     if isinstance(value, ObjectProxy):
#         value._delete()
#     elif isinstance(value, (frozenset, tuple)):
#         for x in value:
#             deleteProxy(x)

# def unloadProxy(item):
#     if isinstance(item, ObjectProxy):
#         item._unload()

def wrapProxy(value):
    """Wrap sub-objects for proxy handling."""
    if isinstance(value, (ObjectProxy,type,int,str,float,complex,bool,bytes,bytearray,type(None))):
        return value
    elif (isinstance(value, Iterable) + isinstance(value, dict) + hasattr(value, '__dict__')) > 1:
        raise TypeError(f"Object has multiple types like dict, iterable, __dict__")
    elif isinstance(value, Iterable):
        return IterableProxy(value)
    elif isinstance(value, dict):
        return DictProxy(value)
    elif hasattr(value, '__dict__'):
        return ObjectProxy(value)
    else: # callables?
        raise TypeError(f"Cannot proxy object of type {type(value)}")

#TODO delete unused proxies

class IterableProxy(ObjectProxy):
    def _WrapSubObjects(self):
        for k, v in iter(self._obj):
            if not isinstance(v, ObjectProxy):
                self._obj[k] = wrapProxy(v)

    def _unloadSubObjects(self):
        for item in self._obj:
            if isinstance(item, ObjectProxy):
                item._unload()

    def _deleteSubObjects(self):
        for item in self._obj:
            if isinstance(item, ObjectProxy):
                item._delete()

class DictProxy(ObjectProxy):
    def _WrapSubObjects(self):
        for k, v in self._obj.items():
            if not isinstance(v, ObjectProxy):
                self._obj[k] = wrapProxy(v)

    def _unloadSubObjects(self):
        for value in self._obj.values():
            if isinstance(value, ObjectProxy):
                value._unload()

    def _deleteSubObjects(self):
        for value in self._obj.values():
            if isinstance(value, ObjectProxy):
                value._delete()
