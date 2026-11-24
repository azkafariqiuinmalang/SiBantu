import unittest
from pathlib import Path
from unittest.mock import Mock

from database import PostgresConnection, SCHEMA_VERSION, migrate


class PostgresMigrationTest(unittest.TestCase):
    def connection(self, schema_exists):
        db = object.__new__(PostgresConnection)

        def execute(query, args=()):
            if "information_schema.schemata" in query:
                return Mock(fetchone=lambda: {"present": schema_exists})
            if "MAX(version)" in query:
                return Mock(fetchone=lambda: {"version": SCHEMA_VERSION})
            return Mock()

        db.execute = Mock(side_effect=execute)
        return db

    def test_existing_private_schema_does_not_need_database_create_permission(self):
        db = self.connection(True)
        migrate(db, Path.cwd(), "")
        queries = [call.args[0] for call in db.execute.call_args_list]
        self.assertFalse(any(query.startswith("CREATE SCHEMA") for query in queries))
        self.assertTrue(any("MAX(version)" in query for query in queries))

    def test_new_database_still_creates_private_schema(self):
        db = self.connection(False)
        migrate(db, Path.cwd(), "")
        self.assertEqual(sum(call.args[0] == "CREATE SCHEMA sibantu"
                             for call in db.execute.call_args_list), 1)
