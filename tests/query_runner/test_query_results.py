import sqlite3
from unittest import TestCase

from redash.query_runner.query_results import (PermissionError, _load_query, create_table,
                                               extract_query_ids)
from tests import BaseTestCase


class TestExtractQueryIds(TestCase):
    def test_works_with_simple_query(self):
        query = "SELECT 1"
        self.assertEquals([], extract_query_ids(query))

    def test_finds_queries_to_load(self):
        query = "SELECT * FROM query_123"
        self.assertEquals([123], extract_query_ids(query))

    def test_finds_queries_in_joins(self):
        query = "SELECT * FROM query_123 JOIN query_4566"
        self.assertEquals([123, 4566], extract_query_ids(query))


class TestCreateTable(TestCase):
    def test_creates_table_with_colons_in_column_name(self):
        connection = sqlite3.connect(':memory:')
        results = {'columns': [{'name': 'ga:newUsers'}, {
            'name': 'test2'}], 'rows': [{'ga:newUsers': 123, 'test2': 2}]}
        table_name = 'query_123'
        create_table(connection, table_name, results)
        connection.execute('SELECT 1 FROM query_123')

    def test_creates_table(self):
        connection = sqlite3.connect(':memory:')
        results = {'columns': [{'name': 'test1'},
                               {'name': 'test2'}], 'rows': []}
        table_name = 'query_123'
        create_table(connection, table_name, results)
        connection.execute('SELECT 1 FROM query_123')

    def test_creates_table_with_missing_columns(self):
        connection = sqlite3.connect(':memory:')
        results = {'columns': [{'name': 'test1'}, {'name': 'test2'}], 'rows': [
            {'test1': 1, 'test2': 2}, {'test1': 3}]}
        table_name = 'query_123'
        create_table(connection, table_name, results)
        connection.execute('SELECT 1 FROM query_123')

    def test_creates_table_with_spaces_in_column_name(self):
        connection = sqlite3.connect(':memory:')
        results = {'columns': [{'name': 'two words'}, {'name': 'test2'}], 'rows': [
            {'two words': 1, 'test2': 2}, {'test1': 3}]}
        table_name = 'query_123'
        create_table(connection, table_name, results)
        connection.execute('SELECT 1 FROM query_123')

    def test_loads_results(self):
        connection = sqlite3.connect(':memory:')
        rows = [{'test1': 1, 'test2': 'test'}, {'test1': 2, 'test2': 'test2'}]
        results = {'columns': [{'name': 'test1'},
                               {'name': 'test2'}], 'rows': rows}
        table_name = 'query_123'
        create_table(connection, table_name, results)
        self.assertEquals(
            len(list(connection.execute('SELECT * FROM query_123'))), 2)


class TestGetQuery(BaseTestCase):
    # test query from different account
    def test_raises_exception_for_query_from_different_account(self):
        query = self.factory.create_query()
        user = self.factory.create_user(org=self.factory.create_org())

        self.assertRaises(PermissionError, lambda: _load_query(user, query.id))

    def test_raises_exception_for_query_with_different_groups(self):
        ds = self.factory.create_data_source(group=self.factory.create_group())
        query = self.factory.create_query(data_source=ds)
        user = self.factory.create_user()

        self.assertRaises(PermissionError, lambda: _load_query(user, query.id))

    def test_returns_query(self):
        query = self.factory.create_query()
        user = self.factory.create_user()

        loaded = _load_query(user, query.id)
        self.assertEquals(query, loaded)