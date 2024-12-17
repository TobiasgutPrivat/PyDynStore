import unittest
from dataclasses import dataclass
from __Dict__Proxy import DictProxy, wrapProxy

@dataclass
class SubObject:
    value: int

@dataclass
class ParentObject:
    value: int
    sub_obj: SubObject

    def __init__(self, value):
        self.value = value
        self.sub_obj = SubObject(value * 2)
    
class SimpleTestCase(unittest.TestCase):
    def testBasicProxy(self):
        parent = ParentObject(10)
        parent_proxy = wrapProxy(parent)
        #init
        assert parent_proxy.value == 10
        assert parent_proxy.sub_obj.value == 20
        assert isinstance(parent_proxy, DictProxy)# issue if there are type checks in general
        assert isinstance(parent_proxy.sub_obj, DictProxy)

        #references
        # parent_proxy.parent = parent

        #edit
        parent_proxy.sub_obj.value = 30
        assert parent_proxy.sub_obj.value == 30

        #reload
        id = parent_proxy._id
        del parent_proxy
        parent_proxy = DictProxy(id)
        assert parent_proxy.value == 10
        assert parent_proxy.sub_obj.value == 30

        #delete
        assert hasattr(parent_proxy, 'value') == True
        delattr(parent_proxy, 'value')
        assert hasattr(parent_proxy, 'value') == False

        #new object
        newObj = SubObject(40)
        parent_proxy.newObj = newObj
        assert parent_proxy.newObj.value == 40
        assert isinstance(parent_proxy.newObj, DictProxy)

        # # print(str(parent_proxy)) #TODO some Error due to attribute access of dataclass
        # #list
        # parent_proxy.somelist = [1,2,3]
        # assert parent_proxy.somelist[0] == 1
        # parent_proxy.somelist.pop(0)#TODO issue: doesn't save again after executing pop
        # # assert parent_proxy.somelist[0] == 2
        # # parent_proxy.somelist.append(4)
        # # assert parent_proxy.somelist[2] == 4

        # #dict
        # parent_proxy.somedict = {'a':1, 'b':2}
        # assert parent_proxy.somedict['a'] == 1
        # # parent_proxy.pop('a')
        # # parent_proxy['c'] = 3
        # # assert parent_proxy['c'] == 3

        # #set
        # parent_proxy.someset = {1,2,3}
        # assert 1 in parent_proxy.someset
        # # parent_proxy.someset.add(4)
        # # assert 4 in parent_proxy.someset
        # # parent_proxy.someset.discard(1)
        # # assert 1 not in parent_proxy.someset
        # # other_set = {2,3,4}
        # # parent_proxy.someset.update(other_set.union(parent_proxy.someset))

        # #tuple

unittest.main()