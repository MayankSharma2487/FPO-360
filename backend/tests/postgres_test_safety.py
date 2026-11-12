"""Fail-closed URL checks for PostgreSQL integration-test fixtures."""
import os
import re

from sqlalchemy.engine import URL, make_url


TEST_DATABASE_OPT_IN = "FPO360_ALLOW_DISPOSABLE_POSTGRES_TESTS"
APPLICATION_DATABASE_NAME = "FPO360_APPLICATION_DATABASE_NAME"
# All PostgreSQL integration fixtures use a dedicated fpo360_test_<purpose> database.
_TEST_NAME = re.compile(r"^fpo360_test_[a-z0-9]+(?:[_-][a-z0-9]+)*$", re.IGNORECASE)
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9a-fA-F]{2})")
_TARGET_OVERRIDE_OPTIONS = {"database", "dbname", "host", "hostaddr", "port", "service", "servicefile"}


def _parse_url(value, error_message):
    if isinstance(value, str) and _INVALID_PERCENT_ESCAPE.search(value):
        raise ValueError(error_message)
    try:
        return make_url(value)
    except Exception:
        raise ValueError(error_message) from None


def validate_test_database_url(url, *, environ=None):
    """Return a parsed URL only when explicitly authorized as a disposable PG test DB.

    This function performs no I/O. Error messages intentionally omit URL values.
    """
    env = os.environ if environ is None else environ
    if env.get(TEST_DATABASE_OPT_IN) != "1":
        raise ValueError(f"Set {TEST_DATABASE_OPT_IN}=1 to enable disposable PostgreSQL tests")
    if not url:
        raise ValueError("A PostgreSQL test database URL is required")

    target = _parse_url(url, "The PostgreSQL test database URL is invalid")

    if target.get_backend_name() != "postgresql":
        raise ValueError("PostgreSQL integration tests require a PostgreSQL URL")
    if _has_target_override(target):
        raise ValueError("PostgreSQL test URLs cannot use service or connection-target overrides")
    if not target.database or not _TEST_NAME.fullmatch(target.database):
        raise ValueError("The PostgreSQL test database name must use fpo360_test_<purpose>")

    application_url = env.get("DATABASE_URL")
    application_name = env.get(APPLICATION_DATABASE_NAME)
    if application_url:
        application = _parse_url(
            application_url, "DATABASE_URL is invalid; refusing PostgreSQL test setup"
        )
        if application.get_backend_name() == "postgresql":
            if _has_target_override(application):
                raise ValueError("DATABASE_URL uses connection-target overrides; refusing PostgreSQL test setup")
            configured_name = application.database or application.username or ""
            if application_name and application_name.casefold() != configured_name.casefold():
                raise ValueError(
                    f"{APPLICATION_DATABASE_NAME} does not match DATABASE_URL's database identifier"
                )
            application_name = configured_name
        elif not application_name:
            raise ValueError(
                f"Set {APPLICATION_DATABASE_NAME} when DATABASE_URL is a non-PostgreSQL shim"
            )
    elif not application_name:
        raise ValueError(
            f"Set {APPLICATION_DATABASE_NAME} when DATABASE_URL is unset or hidden by a shim"
        )

    if application_name and _same_database_name(target, application_name):
        raise ValueError("The PostgreSQL test database must not match the application database name")

    return target


def _has_target_override(url: URL) -> bool:
    return any(key.casefold() in _TARGET_OVERRIDE_OPTIONS for key in url.query)


def _same_database_name(target: URL, application: URL | str) -> bool:
    # Host aliases, driver names, credentials, and query/service options must not
    # make the same database name look like a separate test target.
    target_name = target.database or ""
    # libpq defaults the database name to the user name when no database is given.
    if isinstance(application, URL):
        application_name = application.database or application.username or ""
    else:
        application_name = application
    return bool(target_name and application_name) and target_name.casefold() == application_name.casefold()
