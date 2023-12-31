import os
import unittest

from mmlib.equal import model_equal
from mmlib.util.dummy_data import imagenet_input
from mmlib.util.init_from_file import create_object, create_object_with_parameters
from tests.example_files.mynets.resnet18 import resnet18
from tests.init_from_file.dummy_classes import DummyA

CODE = os.path.join(os.path.dirname(os.path.realpath(__file__)), './dummy_classes.py')


class TestInitFromFIle(unittest.TestCase):

    def test_init_no_args(self):
        obj = create_object(CODE, 'DummyC')

        self.assertEqual(42, obj.state)
        self.assertEqual(DummyA(42).state, obj.state2.state)

    def test_init_no_ref_args(self):
        init_args = {'state': 42}
        obj = create_object_with_parameters('DummyA', init_args=init_args, code_file=CODE)

        self.assertEqual(42, obj.state)

    def test_init_ref_args_code(self):
        init_args = {'arg1': 42, 'arg2': 43}
        ref_args = {'arg3': DummyA(42)}
        obj = create_object_with_parameters('DummyB', init_args=init_args, init_ref_type_args=ref_args, code_file=CODE)

        self.assertEqual(42, obj.state1)
        self.assertEqual(43, obj.state2)
        self.assertEqual(42, obj.state3.state)

    def test_init_code_string(self):
        init_args = {'int_arg': 42, 'str_arg': '43'}
        obj = create_object_with_parameters('DummyD', init_args=init_args, code_file=CODE)

        self.assertEqual(42, obj.int_state)
        self.assertEqual('43', obj.str_state)

    def test_init_import_cmd(self):
        expected = resnet18(pretrained=True)
        init_args = {'pretrained': True}
        obj = create_object_with_parameters('resnet18', init_args=init_args, init_ref_type_args={},
                                            import_cmd='from torchvision.models import resnet18')

        self.assertTrue(model_equal(expected, obj, imagenet_input))

    def test_init_ref_args_import_cmd(self):
        init_args = {'arg1': 42, 'arg2': 43}
        ref_args = {'arg3': DummyA(42)}
        obj = create_object_with_parameters('DummyB', init_args=init_args, init_ref_type_args=ref_args,
                                            import_cmd='from tests.init_from_file.dummy_classes import DummyB')

        self.assertEqual(42, obj.state1)
        self.assertEqual(43, obj.state2)
        self.assertEqual(42, obj.state3.state)
