from unittest.case import TestCase
from uuid import uuid4

from eventsourcing.domain.model.entity import EntityIsDiscarded, WithReflexiveMutator
from eventsourcing.example.domainmodel import Example


class ExampleWithReflexiveMutator(WithReflexiveMutator, Example):
    class Created(Example.Created):
        def apply(self, cls):
            return cls(**self.__dict__)

    class AttributeChanged(Example.AttributeChanged):
        def apply(self, entity):
            entity._validate_originator(self)
            setattr(entity, self.name, self.value)
            entity._last_modified_on = self.timestamp
            entity._increment_version()
            return entity

    class Discarded(Example.Discarded):
        def apply(self, entity):
            entity._validate_originator(self)
            entity._is_discarded = True
            entity._increment_version()
            return None


class TestReflexiveMutator(TestCase):
    def test(self):
        # Create an entity.
        entity_id = uuid4()
        created = ExampleWithReflexiveMutator.Created(entity_id=entity_id, a=1, b=2)
        entity = ExampleWithReflexiveMutator.mutate(event=created)
        self.assertIsInstance(entity, ExampleWithReflexiveMutator)
        self.assertEqual(entity.id, entity_id)
        self.assertEqual(entity.a, 1)
        self.assertEqual(entity.b, 2)

        # Check the attribute changed event can be applied.
        entity.a = 3
        self.assertEqual(entity.a, 3)

        # Check the discarded event can be applied.
        entity.discard()
        with self.assertRaises(EntityIsDiscarded):
            entity.a = 4
