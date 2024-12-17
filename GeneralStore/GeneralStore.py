from Database import getObject, updateObject, deleteObject, createNewObject

def _pds__getattr__(self, name):
    self._pds_load() # lazy load
    return getattr(self, name)

def _pds__getitem__(self, key):
    self._pds_load() # lazy load
    return self[key]

def _pds_load(self):
    if self._pds_id is None:
        return
    if not self._pds_loaded:
        data = getObject(self._pds_id)
        self.__dict__ = data["dict"] + {"_pds_id": self._pds_id}
        self.items().update(data["items"])
        self._pds_loaded = True

def _pds_unload(self):
    """Unloads by deleting object data (doesn't save)"""
    if self._pds_loaded:
        self.__dict__ = {"_pds_id": self._pds_id} if hasattr(self, "_pds_id") else {} # keep id for loading
        self.items().clear()
        self._pds_loaded = False

def _pds_save(self, customId: str = None):
    if not self._pds_loaded: # no need to save if not loaded (also avoids recursion)
        return

    if isinstance(self, (int, str, float, complex, bool, bytes, bytearray, type(None))):  # do not track primitive types
        return

    items = self.items() # extract data from object
    dict = {key: value if key not in ["_pds_id", "_pds_loaded"] else None for key, value in self.__dict__.items()}
    values = items.values() + dict.values()

    self._pds_unload() #unload before saving sub-objects to not save on recursion

    if self._pds_id is None: # determines if first save
        if customId is not None:
            #TODO check if id already exists
            self._pds_id = customId
        else:
            self._pds_id = createNewObject({"temp": True}) # create placeholder object to get id for sub-objects to have id on recursion

    for value in values: #save sub-objects first to not save values in parent as well
        value._pds_save()

    updateObject(self._pds_id, {"items": items, "dict": dict}) # save self to DB

def _pds_untrack(self):
    if self._pds_id is None:
        return
    self._pds_load()
    deleteObject(self._pds_id)
    del self._pds_id
    del self._pds_loaded


def extendGlobalObjectPDS():
    # per default not tracked (class level)
    object._pds_loaded = True # when first saved counts as loaded
    object._pds_id = None # also determines if object is tracked

    object.__getattr__ = _pds__getattr__
    object.__getitem__ = _pds__getitem__

    object._pds_load = _pds_load
    object._pds_unload = _pds_unload
    object._pds_save = _pds_save
    object._pds_untrack = _pds_untrack

def loadObjectPDS(id: str, type: type) -> object:
    object = type()
    object._pds_id = id
    object._pds_loaded = False
    return object
