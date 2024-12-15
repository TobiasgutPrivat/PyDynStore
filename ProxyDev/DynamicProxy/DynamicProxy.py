from Database import createNewObject, getObject, updateObject, deleteObject
# !!! Debugging can cause unintended loading !!!

#TODO think about how to handle referenced objects in memory

class DynamicProxy:
    _id: int  # take from qdrant
    # _packages: list[str] # TODO track packages needed to import when loading object
    # also think about form of import, because dill references it in according scope
    _obj: object
    _loaded: bool #could be removed because equal to _obj != None

    def __init__(self, obj=None): #TODO allow create from ObjectID #TODO new created for references
        """
        :param obj: If an existing object is passed, it will be wrapped by the proxy.
        """
        self._id = createNewObject(obj)
        self._loaded = True
        for k, v in obj.__dict__.items():
            obj.__dict__[k] = wrapProxy(v)
        #TODO also wrap dict/iterable
        self._obj = obj


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
        # elif hasattr(self._obj, '__dict__'):
        #     for attr_value in self._obj.__dict__.values():
        #         unloadProxy(attr_value)
        # not needed because done when serialized
        
        self._obj = None
        self._loaded = False

    def __getstate__(self): #always store subobjects unloaded
        self._unload()
        return self.__dict__.copy()

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __getattr__(self, name):
        """Loads the object when an attribute is accessed"""
        self._load()
        return getattr(self._obj, name)

    def __setattr__(self, name, value):
        if name in ['_id', '_packages', '_obj', '_loaded']:
            super().__setattr__(name, value)
        else:
            self._load()
            # deleteProxy(getattr(self._obj,name))
            setattr(self._obj, name, wrapProxy(value))
            self._save()  # Automatically save after modifying

    def __delattr__(self, name):
        if name in ['_id', '_packages', '_obj', '_loaded']:
            super().__delattr__(name)
        else:
            self._load()  # Load the object before deleting any attributes
            # deleteProxy(getattr(self._obj,name))
            delattr(self._obj, name)
            self._save()

    def __getitem__(self, key):#TODO potentialy unnecessary
        self._load()  # Load the object when an item is accessed
        return self._obj[key]

    def __setitem__(self, key, value):
        self._load()  # Load the object before setting any item
        # deleteProxy(self._obj[key])
        self._obj[key] = wrapProxy(value)
        self._save()  # Automatically save after modifying

    def __delitem__(self, key):
        self._load()  # Load the object before deleting an item
        # deleteProxy(self._obj[key])
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
    
    # def _delete(self):
    #     if isinstance(self._obj, dict):
    #         for value in self._obj.values():
    #             deleteProxy(value)
    #     elif isinstance(self._obj, (list, set, tuple)):
    #         for item in self._obj:
    #             deleteProxy(item)
    #     elif hasattr(self._obj, '__slots__'):
    #         for slot in self._obj.__slots__:
    #             value = getattr(self._obj, slot)
    #             deleteProxy(value)
    #     elif hasattr(self._obj, '__dict__'):
    #         for attr_value in self._obj.__dict__.values():
    #             deleteProxy(attr_value)
    #     deleteObject(self._id) 

    def _untrack(self) -> object:
        obj = self._obj
        del self
        return obj
    
    #TODO handle more dunders
    # dunders which only would require loading can be ignored because, get handled by getattr if not found

# def deleteProxy(value):
#     if isinstance(value, DynamicProxy):
#         value._delete()
#     elif isinstance(value, (frozenset, tuple)):
#         for x in value:
#             deleteProxy(x)

# def unloadProxy(item):
#     if isinstance(item, DynamicProxy):
#         item._unload()

def wrapProxy(value):
    """Wrap sub-objects for proxy handling."""#TODO think about other types (range)
    if isinstance(value, (DynamicProxy,type,int,str,float,complex,bool,bytes,bytearray,type(None))):
        return value
    elif isinstance(value, (frozenset,tuple)): # potentially unnecessary
        for x in value:
            wrapProxy(x)
        return value
    else: # list, dict, set, normal-objects, callables
        return DynamicProxy(value)

#TODO delete unused proxies