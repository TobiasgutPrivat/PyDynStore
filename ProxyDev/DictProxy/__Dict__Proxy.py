from Database import createNewObject, getObject, updateObject, deleteObject
from pymongo.collection import ObjectId

new_objects: dict[int,ObjectId] = {}
class DictProxy(dict):
    def __init__(self, dict: dict|ObjectId):
        """:param obj: If an existing object is passed, it will be wrapped by the proxy."""
        if isinstance(dict, ObjectId):
            self._id = dict
        else:
            if id(dict) in new_objects:
                self._id = new_objects[id(dict)]
                return
            wrapSubObjects(dict)
            self._id = createNewObject(dict)
            new_objects[id(dict)] = self._id #issue with recursion in subobjects

    def __getitem__(self, key):
        return getObject(self._id)[key]

    def __setitem__(self, key, value):
        object = getObject(self._id)
        object[key] = wrapProxy(value)
        updateObject(self._id, object)

    def __delitem__(self, key):
        object = getObject(self._id)
        object.pop(key)
        updateObject(self._id, object)

    def __getattr__(self, name):
        if name in ['_id', '_obj']: # needed because of serialization
            return super().__getattribute__(name)
        obj = getObject(self._id)
        return getattr(obj, name)

    def __setattr__(self, name: str, value) -> None:
        if name in ['_id', '_obj']:
            return super().__setattr__(name, value)
        obj = getObject(self._id)
        setattr(obj, name, wrapProxy(value))
        updateObject(self._id, obj)

    def __delattr__(self, name):
        obj = getObject(self._id)
        delattr(obj, name)
        updateObject(self._id, obj)

    def __str__(self):
        return str(getObject(self._id))
    def __repr__(self):
        return repr(getObject(self._id))

def wrapSubObjects(dict: dict):
    for k, v in dict.items():
        dict[k] = wrapProxy(v)

def wrapProxy(value):
    """Wrap sub-objects for proxy handling."""
    if isinstance(value, (DictProxy,type,int,str,float,complex,bool,bytes,bytearray,type(None))):
        return value
    elif hasattr(value, '__dict__'):
        value.__dict__ = DictProxy(value.__dict__)
        return value
    else: #TODO handle other types
        return value