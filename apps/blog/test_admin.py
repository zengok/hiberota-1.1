from __future__ import annotations

from typing import Any, cast

from django.contrib import admin
from django.test import SimpleTestCase

from apps.blog.admin import BlogPostAdmin
from apps.blog.models import BlogAuthor, BlogPost


class BlogAdminTests(SimpleTestCase):
    def test_blog_models_are_registered_in_admin(self) -> None:
        self.assertIn(BlogAuthor, admin.site._registry)
        self.assertIn(BlogPost, admin.site._registry)

    def test_post_admin_exposes_editor_publish_and_seo_sections(self) -> None:
        model_admin = admin.site._registry[BlogPost]

        self.assertIsInstance(model_admin, BlogPostAdmin)
        fieldsets = model_admin.fieldsets
        self.assertIsNotNone(fieldsets)
        fieldsets = cast(list[tuple[Any, Any]], fieldsets)
        fieldset_titles = [fieldset[0] for fieldset in fieldsets]
        self.assertEqual(fieldset_titles, ["İçerik", "Görsel", "Yayın", "SEO"])
        self.assertIn("related_calls", model_admin.autocomplete_fields)
