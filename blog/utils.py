import uuid

from django.db.models import F, Value
from django.db.models.expressions import RawSQL

from .models import Post, Comment


def create_post_slug(title):
    slug = title.lower().replace(' ', '-')
    if Post.objects.filter(slug=slug).exists():
        unique_text = uuid.uuid4()
        slug += f'-{unique_text}'
    return slug
