from __future__ import annotations

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def create_postgres_search_indexes(apps: object, schema_editor: BaseDatabaseSchemaEditor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    schema_editor.execute(
        """
        CREATE INDEX IF NOT EXISTS call_title_trgm_idx
        ON calls_grantcall
        USING gin (title gin_trgm_ops)
        """
    )
    schema_editor.execute(
        """
        CREATE INDEX IF NOT EXISTS institution_name_trgm_idx
        ON institutions_institution
        USING gin (name gin_trgm_ops)
        """
    )
    schema_editor.execute(
        """
        CREATE INDEX IF NOT EXISTS call_search_fts_idx
        ON calls_grantcall
        USING gin (
            to_tsvector(
                'simple',
                coalesce(title, '') || ' ' ||
                coalesce(summary, '') || ' ' ||
                coalesce(purpose, '') || ' ' ||
                coalesce(eligibility_text, '') || ' ' ||
                coalesce(funding_text, '')
            )
        )
        """
    )


def drop_postgres_search_indexes(apps: object, schema_editor: BaseDatabaseSchemaEditor) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("DROP INDEX IF EXISTS call_search_fts_idx")
    schema_editor.execute("DROP INDEX IF EXISTS institution_name_trgm_idx")
    schema_editor.execute("DROP INDEX IF EXISTS call_title_trgm_idx")


class Migration(migrations.Migration):
    dependencies = [
        ("calls", "0002_grantcall_call_funding_min_lte_max_and_more"),
        ("institutions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_postgres_search_indexes, drop_postgres_search_indexes),
    ]
