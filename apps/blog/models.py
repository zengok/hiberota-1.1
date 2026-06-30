from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.core.models import TimeStampedModel

ALLOWED_RICH_TEXT_TAGS = {
    "a",
    "blockquote",
    "br",
    "em",
    "h2",
    "h3",
    "img",
    "li",
    "ol",
    "p",
    "strong",
    "ul",
}
ALLOWED_RICH_TEXT_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
}
ALLOWED_RICH_TEXT_SCHEMES = {"http", "https", "mailto"}


class RichTextAllowlistParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._validate_tag(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._validate_tag(tag, attrs)

    def _validate_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in ALLOWED_RICH_TEXT_TAGS:
            self.errors.append(f"'{tag}' etiketi desteklenmiyor.")
            return

        allowed_attrs = ALLOWED_RICH_TEXT_ATTRIBUTES.get(tag, set())
        for key, value in attrs:
            if key not in allowed_attrs:
                self.errors.append(f"'{tag}' etiketi için '{key}' niteliği desteklenmiyor.")
                continue
            if key in {"href", "src"} and value and not self._is_safe_url(value):
                self.errors.append(f"'{tag}' etiketi güvenli olmayan URL içeriyor.")

    def _is_safe_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return not parsed.scheme or parsed.scheme in ALLOWED_RICH_TEXT_SCHEMES


def validate_rich_text_allowlist(value: str) -> None:
    parser = RichTextAllowlistParser()
    parser.feed(value)
    parser.close()
    if parser.errors:
        raise ValidationError(parser.errors)


class BlogAuthor(TimeStampedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    title = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    photo = models.FileField(upload_to="blog/authors/", blank=True)
    photo_alt_text = models.CharField(max_length=180, blank=True)
    website_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="blog_author_slug_idx"),
            models.Index(fields=["is_active"], name="blog_author_active_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class BlogPost(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"

    class Category(models.TextChoices):
        GUIDE = "guide", "Proje rehberi"
        FUNDING = "funding", "Hibe ve fon"
        NEWS = "news", "Duyuru"

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    excerpt = models.TextField(max_length=500)
    category = models.CharField(max_length=40, choices=Category.choices, default=Category.GUIDE)
    cover_image = models.FileField(upload_to="blog/covers/", blank=True)
    cover_alt_text = models.CharField(max_length=180, blank=True)
    cover_caption = models.CharField(max_length=220, blank=True)
    cover_source_url = models.URLField(max_length=500, blank=True)
    author = models.ForeignKey(BlogAuthor, on_delete=models.PROTECT, related_name="posts")
    body_html = models.TextField(validators=[validate_rich_text_allowlist])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    publish_at = models.DateTimeField(blank=True, null=True)
    reading_time_minutes = models.PositiveSmallIntegerField(default=1)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(max_length=500, blank=True)
    related_calls = models.ManyToManyField(GrantCall, blank=True, related_name="blog_posts")

    class Meta:
        ordering = ["-publish_at", "-created_at"]
        indexes = [
            models.Index(fields=["slug"], name="blog_post_slug_idx"),
            models.Index(fields=["status", "publish_at"], name="blog_post_status_publish_idx"),
            models.Index(fields=["category"], name="blog_post_category_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        validate_rich_text_allowlist(self.body_html)
        if self.status in {self.Status.SCHEDULED, self.Status.PUBLISHED} and self.publish_at is None:
            raise ValidationError({"publish_at": "Yayınlanacak veya planlanmış içerikler için tarih zorunludur."})
        if self.status == self.Status.SCHEDULED and self.publish_at is not None and self.publish_at <= timezone.now():
            raise ValidationError({"publish_at": "Planlanmış içerik tarihi gelecekte olmalıdır."})
        if self.reading_time_minutes < 1:
            raise ValidationError({"reading_time_minutes": "Okuma süresi en az 1 dakika olmalıdır."})

    def __str__(self) -> str:
        return self.title
