import os
import shutil
import unittest

from mmlib.equal import model_equal
from mmlib.persistence import FileSystemPersistenceService, MongoDictPersistenceService
from mmlib.save import BaselineSaveService
from mmlib.schema.save_info_builder import ModelSaveInfoBuilder
from mmlib.track_env import track_current_environment
from mmlib.util.dummy_data import imagenet_input
from mmlib.util.mongo import MongoService
from tests.example_files.mynets.googlenet import googlenet
from tests.example_files.mynets.mobilenet import mobilenet_v2
from tests.example_files.mynets.resnet18 import resnet18

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
NETWORK_CODE_TEMPLATE = os.path.join(FILE_PATH, '../example_files/mynets/{}.py')
MONGO_CONTAINER_NAME = 'mongo-test'

GOOGLENET = 'googlenet'
MOBILENET = 'mobilenet'
RESNET_18 = 'resnet18'


class TestBaselineSaveService(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp_path = './filesystem-tmp'
        self.abs_tmp_path = os.path.abspath(self.tmp_path)

        self.__clean_up()

        # run mongo DB locally in docker container
        os.system('docker run --rm --name %s -it -p 27017:27017 -d  mongo:4.4.3 ' % MONGO_CONTAINER_NAME)

        self.mongo_service = MongoService('127.0.0.1', 'mmlib')

        os.mkdir(self.abs_tmp_path)
        self.file_pers_service = FileSystemPersistenceService(self.tmp_path)
        self.dict_pers_service = MongoDictPersistenceService()
        self.init_save_service(self.dict_pers_service, self.file_pers_service)

    def init_save_service(self, dict_pers_service, file_pers_service):
        self.save_service = BaselineSaveService(file_pers_service, dict_pers_service, logging=True)

    def tearDown(self) -> None:
        self.__clean_up()

    def __clean_up(self):
        os.system('docker kill %s' % MONGO_CONTAINER_NAME)
        if os.path.exists(self.abs_tmp_path):
            shutil.rmtree(self.abs_tmp_path)

    def test_save_restore_mobilenet(self):
        model = mobilenet_v2(pretrained=True)
        self._test_save_restore_model(model)

    def test_save_restore_resnet18(self):
        model = resnet18(pretrained=True)
        self._test_save_restore_model(model)

    def test_save_restore_model_googlenet(self):
        model = googlenet()
        self._test_save_restore_model(model)

    def _test_save_restore_model(self, model):
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=model, env=env)
        save_info = save_info_builder.build()

        model_id = self.save_service.save_model(save_info)
        restored_model_info = self.save_service.recover_model(model_id)
        self.assertTrue(model_equal(model, restored_model_info.model, imagenet_input))

    def test_save_restore_mobilenet_val_info(self):
        model = mobilenet_v2(pretrained=True)
        self._test_save_restore_model_and_validation_info(model)

    def test_save_restore_resnet18_val_info(self):
        model = resnet18(pretrained=True)
        self._test_save_restore_model_and_validation_info(model)

    def test_save_restore_model_googlenet_val_info(self):
        model = googlenet()
        self._test_save_restore_model_and_validation_info(model)

    def _test_save_restore_model_and_validation_info(self, model):
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=model, env=env)
        save_info = save_info_builder.build()

        model_id = self.save_service.save_model(save_info)

        # save additionally validation info
        restored_model_info = self.save_service.recover_model(model_id, execute_checks=True)
        self.assertTrue(model_equal(model, restored_model_info.model, imagenet_input))

    def test_save_restore_derived_models(self):
        initial_model = resnet18()

        # save initial model
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=initial_model, env=env)
        save_info = save_info_builder.build()
        initial_model_id = self.save_service.save_model(save_info)

        # save derived model
        derived_model = resnet18(pretrained=True)
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=derived_model, base_model_id=initial_model_id, env=env)
        save_info = save_info_builder.build()
        derived_model_id = self.save_service.save_model(save_info)

        restored_model_info = self.save_service.recover_model(derived_model_id)

        self.assertTrue(model_equal(derived_model, restored_model_info.model, imagenet_input))

    def test_save_restore_multiple_derived_models(self):
        initial_model = resnet18()

        # save initial model
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=initial_model, env=env)
        save_info = save_info_builder.build()
        initial_model_id = self.save_service.save_model(save_info)

        # save derived model
        derived_model = resnet18(pretrained=True)
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=derived_model, base_model_id=initial_model_id, env=env)
        save_info = save_info_builder.build()
        derived_model_id = self.save_service.save_model(save_info)

        restored_model_info = self.save_service.recover_model(derived_model_id)

        self.assertTrue(model_equal(derived_model, restored_model_info.model, imagenet_input))

        # save derived model
        derived_model_2 = restored_model_info.model
        save_info_builder = ModelSaveInfoBuilder()
        env = track_current_environment()
        save_info_builder.add_model_info(model=derived_model_2, base_model_id=derived_model_id, env=env)
        save_info = save_info_builder.build()
        derived_model_id_2 = self.save_service.save_model(save_info)

        restored_model_info_2 = self.save_service.recover_model(derived_model_id_2)

        self.assertTrue(model_equal(derived_model_2, restored_model_info_2.model, imagenet_input))
