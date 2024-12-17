import unittest
from dataclasses import dataclass
from ExtensionProxy import wrapProxy, loadId

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
        wrapProxy(parent)
        #init
        assert parent.value == 10
        assert parent.sub_obj.value == 20
        assert isinstance(parent, ParentObject)# solved issue with type checks
        assert isinstance(parent.sub_obj, SubObject)

        #references
        # parent_proxy.parent = parent

        #edit
        parent.sub_obj.value = 30
        assert parent.sub_obj.value == 30

        #reload
        id = parent._id
        del parent
        parent = loadId(id)
        assert parent.value == 10
        assert parent.sub_obj.value == 30

        #delete
        assert hasattr(parent, 'value') == True
        delattr(parent, 'value')
        assert hasattr(parent, 'value') == False

        #new object
        newObj = SubObject(40)
        parent.newObj = newObj
        assert parent.newObj.value == 40
        assert isinstance(parent.newObj, SubObject)

        # print(str(parent_proxy)) #TODO some Error due to attribute access of dataclass
        #list
        parent.somelist = [1,2,3]
        assert parent.somelist[0] == 1
        parent.somelist.pop(0)#TODO issue: doesn't save again after executing pop
        # assert parent_proxy.somelist[0] == 2
        # parent_proxy.somelist.append(4)
        # assert parent_proxy.somelist[2] == 4

        #dict
        parent.somedict = {'a':1, 'b':2}
        assert parent.somedict['a'] == 1
        # parent_proxy.pop('a')
        # parent_proxy['c'] = 3
        # assert parent_proxy['c'] == 3

        #set
        parent.someset = {1,2,3}
        assert 1 in parent.someset
        # parent_proxy.someset.add(4)
        # assert 4 in parent_proxy.someset
        # parent_proxy.someset.discard(1)
        # assert 1 not in parent_proxy.someset
        # other_set = {2,3,4}
        # parent_proxy.someset.update(other_set.union(parent_proxy.someset))

        #tuple

unittest.main()