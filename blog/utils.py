import uuid

from .models import Post


def create_post_slug(title):
    slug = title.lower().replace(' ', '-')
    if Post.objects.filter(slug=slug).exists():
        unique_text = uuid.uuid4()
        slug += f'-{unique_text}'
    return slug
