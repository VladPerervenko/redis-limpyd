# -*- coding:utf-8 -*-

import unittest

from limpyd import model
from limpyd.exceptions import *
from base import LimpydBaseTest

class Bike(model.RedisModel):
    name = model.StringField(indexable=True)
    wheels = model.StringField(default=2)

class InitTest(LimpydBaseTest):

    def test_instanciation_should_no_connect(self):
        bike = Bike()
        self.assertEqual(bike._pk, None)

    def test_setting_a_field_should_connect(self):
        bike = Bike()
        bike.name.set('rosalie')
        self.assertEqual(bike._pk, 1)

    def test_instances_must_not_share_fields(self):
        bike1 = Bike(name="rosalie")
        self.assertEqual(bike1._pk, 1)
        self.assertEqual(bike1.name.get(), "rosalie")
        bike2 = Bike(name="velocipede")
        self.assertEqual(bike2._pk, 2)
        self.assertEqual(bike2.name.get(), "velocipede")

    def test_field_instance_must_be_consistent(self):
        bike1 = Bike(name="rosalie")
        self.assertEqual(id(bike1), id(bike1.name._instance))
        bike2 = Bike(name="velocipede")
        self.assertEqual(id(bike2), id(bike2.name._instance))
        self.assertNotEqual(id(bike1.name._instance), id(bike2.name._instance))

    def test_one_arg_should_retrieve_from_db(self):
        bike = Bike()
        bike.name.set('rosalie')
        self.assertEqual(bike._pk, 1)
        bike_again = Bike(1)
        self.assertEqual(bike_again._pk, 1)

    def test_kwargs_should_be_setted_as_fields(self):
        bike = Bike(name="rosalie")
        self.assertEqual(bike.name.get(), "rosalie")

    def test_should_have_default_value_if_not_setted(self):
        bike = Bike(name="recumbent")
        self.assertEqual(bike.wheels.get(), '2')

    def test_default_value_should_not_override_setted_one(self):
        bike = Bike(name="rosalie", wheels=4)
        self.assertEqual(bike.wheels.get(), '4')


class IndexationTest(LimpydBaseTest):

    def test_stringfield_indexable(self):
        bike = Bike()
        bike.name.set("monocycle")
        self.assertFalse(Bike.exists(name="tricycle"))
        self.assertTrue(Bike.exists(name="monocycle"))
        bike.name.set("tricycle")
        self.assertFalse(Bike.exists(name="monocycle"))
        self.assertTrue(Bike.exists(name="tricycle"))


class CollectionTest(LimpydBaseTest):

    def test_new_instance_should_be_added_in_collection(self):
        self.assertEqual(Bike.collection(), set())
        bike = Bike()
        self.assertEqual(Bike.collection(), set())
        bike1 = Bike(name="trotinette")
        self.assertEqual(Bike.collection(), set(['1']))
        bike2 = Bike(name="tommasini")
        self.assertEqual(Bike.collection(), set(['1', '2']))


class UniquenessTest(LimpydBaseTest):

    class SailBoat(model.RedisModel):
        name = model.StringField(unique=True)
        length = model.StringField()

    def test_cannot_set_unique_already_indexed_at_init(self):
        boat1 = self.SailBoat(name="Pen Duick I", length=15.1)
        # First check data
        self.assertEqual(boat1.name.get(), "Pen Duick I")
        self.assertEqual(boat1.length.get(), "15.1")
        # Try to create a boat with the same name
        with self.assertRaises(UniquenessError):
            boat2 = self.SailBoat(name="Pen Duick I", length=15.1)
        # Check data after
        self.assertEqual(boat1.name.get(), "Pen Duick I")
        self.assertEqual(boat1.length.get(), "15.1")

    def test_cannot_set_unique_already_indexed_with_setter(self):
        boat1 = self.SailBoat(name="Pen Duick I", length=15.1)
        # First check data
        self.assertEqual(boat1.name.get(), "Pen Duick I")
        self.assertEqual(boat1.length.get(), "15.1")
        boat2 = self.SailBoat(name="Pen Duick II", length=13.6)
        with self.assertRaises(UniquenessError):
            boat2.name.set("Pen Duick I")
        # Check data after
        self.assertEqual(boat1.name.get(), "Pen Duick I")
        self.assertEqual(boat1.length.get(), "15.1")


class CommandCacheTest(LimpydBaseTest):

    def test_should_not_hit_redis_when_cached(self):
        # Not sure the connection.info() is thread safe...
        bike = Bike(name="randonneuse")
        # First get
        name = bike.name.get()
        hits_before = self.connection.info()['keyspace_hits']
        # Get again
        name = bike.name.get()
        hits_after = self.connection.info()['keyspace_hits']
        self.assertEqual(name, "randonneuse")
        self.assertEqual(hits_before, hits_after)

    def test_should_flush_if_modifiers_command_is_called(self):
        bike = Bike(name="draisienne")
        name = bike.name.get()
        self.assertEqual(name, "draisienne")
        bike.name.set('tandem')
        name = bike.name.get()
        self.assertEqual(name, "tandem")


class MetaRedisProxyTest(LimpydBaseTest):

    def test_available_commands(self):
        """
        available_commands must exists on Fields and it must contain getters and modifiers.
        """
        def check_available_commands(cls):
            for command in cls.available_getters:
                self.assertTrue(command in cls.available_commands)
        check_available_commands(model.StringField)
        check_available_commands(model.HashableField)
        check_available_commands(model.SortedSetField)


if __name__ == '__main__':
    unittest.main()
