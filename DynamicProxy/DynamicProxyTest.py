import unittest
from dataclasses import dataclass
from DynamicProxy import DynamicProxy

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
    parent_proxy: DynamicProxy

    def setUp(self):
        """Call before every test case."""
        parent = ParentObject(10)
        self.parent_proxy = DynamicProxy(parent)

    def tearDown(self):
        """Call after every test case."""
        print("tearing down")

    def testInit(self):
        assert self.parent_proxy.value == 10
        assert self.parent_proxy.sub_obj.value == 20
        assert isinstance(self.parent_proxy, DynamicProxy)
        assert isinstance(self.parent_proxy._obj, ParentObject)
        assert isinstance(self.parent_proxy.sub_obj, DynamicProxy)
        assert isinstance(self.parent_proxy.sub_obj._obj, SubObject)


    def testLoading(self):
        self.parent_proxy._unload()
        assert self.parent_proxy._loaded == False
        self.parent_proxy._load()
        assert self.parent_proxy._loaded == True

    def testGet(self):
        self.parent_proxy._unload()
        assert self.parent_proxy._loaded == False
        assert self.parent_proxy.sub_obj._loaded == False
        assert self.parent_proxy.value == 10
        assert self.parent_proxy._loaded == True
        assert self.parent_proxy.sub_obj._loaded == False
        assert self.parent_proxy.sub_obj.value == 20
        assert self.parent_proxy.sub_obj._loaded == True

    # def testSubobject(self):
    #     self.parent_proxy.new_attr = SubObject(100)

unittest.main()