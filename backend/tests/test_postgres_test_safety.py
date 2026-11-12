import unittest

from postgres_test_safety import (
    APPLICATION_DATABASE_NAME,
    TEST_DATABASE_OPT_IN,
    validate_test_database_url,
)


class PostgreSQLTestDatabaseSafetyTests(unittest.TestCase):
    def _environment(self, **overrides):
        return {
            TEST_DATABASE_OPT_IN: "1",
            APPLICATION_DATABASE_NAME: "fpo360_application",
            **overrides,
        }

    def test_missing_test_url_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "test database URL is required"):
            validate_test_database_url(None, environ=self._environment())

    def test_missing_and_invalid_opt_in_values_are_rejected(self):
        url = "postgresql://user:secret@localhost/fpo360_test_inventory"
        values = (None, "", "true", "yes", " ", "1 ")
        for value in values:
            with self.subTest(value=value):
                environment = {"DATABASE_URL": "sqlite:///application.db"}
                if value is not None:
                    environment[TEST_DATABASE_OPT_IN] = value
                with self.assertRaisesRegex(ValueError, TEST_DATABASE_OPT_IN):
                    validate_test_database_url(url, environ=environment)

    def test_malformed_test_url_is_rejected_without_echoing_it(self):
        malformed = "postgresql://user:secret@%zz/"
        with self.assertRaisesRegex(ValueError, "URL is invalid") as context:
            validate_test_database_url(malformed, environ=self._environment())
        self.assertNotIn("secret", str(context.exception))
        self.assertNotIn(malformed, str(context.exception))

    def test_malformed_application_url_fails_closed(self):
        environment = self._environment(DATABASE_URL="postgresql://user:secret@%zz/")
        with self.assertRaisesRegex(ValueError, "DATABASE_URL is invalid") as context:
            validate_test_database_url(
                "postgresql://test:secret@localhost/fpo360_test_inventory",
                environ=environment,
            )
        self.assertNotIn("secret", str(context.exception))

    def test_sqlite_runtime_shim_requires_non_secret_application_database_name(self):
        environment = {TEST_DATABASE_OPT_IN: "1", "DATABASE_URL": "sqlite://"}
        with self.assertRaisesRegex(ValueError, APPLICATION_DATABASE_NAME):
            validate_test_database_url(
                "postgresql://test:secret@localhost/fpo360_test_inventory",
                environ=environment,
            )

    def test_sqlite_runtime_shim_still_rejects_application_database_name_match(self):
        environment = self._environment(
            DATABASE_URL="sqlite://",
            **{APPLICATION_DATABASE_NAME: "fpo360_test_inventory"},
        )
        with self.assertRaisesRegex(ValueError, "application database name"):
            validate_test_database_url(
                "postgresql://test:secret@localhost/fpo360_test_inventory",
                environ=environment,
            )

    def test_service_and_target_override_options_are_rejected(self):
        for query in ("service=production", "dbname=application", "host=db.internal"):
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "connection-target overrides"):
                    validate_test_database_url(
                        f"postgresql://test:secret@localhost/fpo360_test_inventory?{query}",
                        environ=self._environment(),
                    )

    def test_application_service_override_fails_closed(self):
        environment = self._environment(
            DATABASE_URL="postgresql://app:secret@localhost/application?service=production"
        )
        with self.assertRaisesRegex(ValueError, "DATABASE_URL uses connection-target overrides"):
            validate_test_database_url(
                "postgresql://test:secret@localhost/fpo360_test_inventory",
                environ=environment,
            )

    def test_non_postgresql_url_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "PostgreSQL"):
            validate_test_database_url(
                "sqlite:///fpo360_test_inventory.db", environ=self._environment()
            )

    def test_unsafe_database_names_are_rejected(self):
        names = (
            "fpo_test_inventory",
            "test_fpo360_inventory",
            "fpo360_test_",
        )
        for name in names:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "fpo360_test_<purpose>"):
                    validate_test_database_url(
                        f"postgresql://user:secret@localhost/{name}",
                        environ=self._environment(),
                    )

    def test_matching_application_database_name_is_rejected_across_hosts_and_options(self):
        environment = {
            TEST_DATABASE_OPT_IN: "1",
            "DATABASE_URL": (
                "postgresql+psycopg2://application:secret@db.internal/"
                "fpo360_test_inventory?sslmode=require&application_name=application"
            )
        }
        with self.assertRaisesRegex(ValueError, "must not match"):
            validate_test_database_url(
                "postgresql+psycopg://test:other@localhost:55432/"
                "fpo360_test_inventory?sslmode=disable&application_name=tests",
                environ=environment,
            )

    def test_application_database_name_defaulting_to_username_is_rejected(self):
        environment = {
            TEST_DATABASE_OPT_IN: "1",
            "DATABASE_URL": "postgresql://fpo360_test_inventory@db.internal",
        }
        with self.assertRaisesRegex(ValueError, "must not match"):
            validate_test_database_url(
                "postgresql://test:secret@localhost/fpo360_test_inventory",
                environ=environment,
            )

    def test_postgresql_driver_variants_and_query_options_are_accepted(self):
        parsed = validate_test_database_url(
            "postgresql+psycopg://test_user:secret@localhost:55432/"
            "fpo360_test_inventory?sslmode=verify-full&application_name=guard-test",
            environ=self._environment(DATABASE_URL="sqlite:///application.db"),
        )
        self.assertEqual("postgresql", parsed.get_backend_name())
        self.assertEqual("psycopg", parsed.get_driver_name())
        self.assertEqual("fpo360_test_inventory", parsed.database)
        self.assertEqual("verify-full", parsed.query["sslmode"])

    def test_explicit_application_name_must_match_configured_postgresql_url(self):
        environment = self._environment(
            DATABASE_URL="postgresql://application:secret@db.internal/fpo360_app"
        )
        with self.assertRaisesRegex(ValueError, "does not match DATABASE_URL"):
            validate_test_database_url(
                "postgresql://test:secret@localhost/fpo360_test_inventory",
                environ=environment,
            )

    def test_valid_explicitly_opted_in_test_url_is_returned(self):
        parsed = validate_test_database_url(
            "postgresql://test_user:secret@localhost/fpo360_test_inventory",
            environ=self._environment(DATABASE_URL="sqlite:///application.db"),
        )
        self.assertEqual("postgresql", parsed.get_backend_name())
        self.assertEqual("fpo360_test_inventory", parsed.database)

    def test_errors_never_expose_credentials(self):
        secret = "never-log-this"
        with self.assertRaises(ValueError) as context:
            validate_test_database_url(
                f"postgresql://user:{secret}@localhost/unsafe_name",
                environ=self._environment(),
            )
        self.assertNotIn(secret, str(context.exception))


if __name__ == "__main__":
    unittest.main()
