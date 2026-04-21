"""
Django ORM helpers. Requires django.setup() to be called before import.
"""

def get_categories():
    from homepage.models import BlogCategory
    return [
        {"id": c.id, "name": c.name, "name_de": c.name_de or "", "slug": c.slug}
        for c in BlogCategory.objects.all().order_by("name")
    ]


def get_recent_posts(limit=30):
    from homepage.models import BlogPost
    posts = BlogPost.objects.select_related("category").order_by("-created_at")[:limit]
    return [
        {
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "category": p.category.name if p.category else "",
            "post_type": p.post_type,
            "is_published": p.is_published,
            "created_at": p.created_at.strftime("%Y-%m-%d") if p.created_at else "",
        }
        for p in posts
    ]


def slug_exists(slug: str) -> bool:
    from homepage.models import BlogPost
    return BlogPost.objects.filter(slug=slug).exists()


def create_draft_post(data: dict) -> dict:
    """
    Creates a BlogPost with is_published=False.
    data keys: title, title_de, slug, category_id, post_type,
               excerpt, excerpt_de, body, body_de,
               meta_title, meta_description, cover_public_id (Cloudinary public_id)
    Returns: {id, slug, admin_url}
    """
    from homepage.models import BlogPost, BlogCategory

    category = None
    if data.get("category_id"):
        try:
            category = BlogCategory.objects.get(id=data["category_id"])
        except BlogCategory.DoesNotExist:
            pass

    post = BlogPost(
        title=data.get("title", ""),
        title_de=data.get("title_de", ""),
        slug=data.get("slug", ""),
        post_type=data.get("post_type", "article"),
        category=category,
        excerpt=data.get("excerpt", ""),
        excerpt_de=data.get("excerpt_de", ""),
        body=data.get("body", ""),
        body_de=data.get("body_de", ""),
        meta_title=data.get("meta_title", "")[:60] if data.get("meta_title") else "",
        meta_description=data.get("meta_description", "")[:160] if data.get("meta_description") else "",
        is_published=False,
    )

    # Assign Cloudinary cover image by public_id
    if data.get("cover_public_id"):
        post.cover_image.name = data["cover_public_id"]

    post.save()

    return {
        "id": post.id,
        "slug": post.slug,
        "admin_url": f"/en/admin/homepage/blogpost/{post.id}/change/",
    }
