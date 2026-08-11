import asyncio
from types import SimpleNamespace

from app.services.news import NewsService


def _article(*, news_id: int = 1, views: int = 4) -> SimpleNamespace:
    return SimpleNamespace(
        id=news_id,
        publish_time=None,
        created_at=None,
        updated_at=None,
        title="test news",
        description=None,
        content="content",
        image=None,
        author=None,
        category_id=1,
        views=views,
    )


class _FakeNewsRepository:
    def __init__(self) -> None:
        self.article = _article()

    async def list_news(self, **_kwargs: object) -> tuple[list[SimpleNamespace], int]:
        return [self.article], 1

    async def get_news_by_id(self, news_id: int) -> SimpleNamespace | None:
        return self.article if news_id == self.article.id else None

    async def increment_views(self, article: SimpleNamespace) -> SimpleNamespace:
        article.views += 1
        return article

    async def list_related_news(self, **_kwargs: object) -> list[SimpleNamespace]:
        return [_article(news_id=2, views=8)]

    async def list_categories(self) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                id=1,
                created_at=None,
                updated_at=None,
                name="Technology",
                sort_order=0,
            )
        ]


def test_news_service_keeps_business_orchestration_out_of_routes() -> None:
    async def verify() -> None:
        service = NewsService(_FakeNewsRepository())

        list_payload = await service.list_news(category_id=None, page=1, page_size=10)
        detail_payload = await service.get_news_detail(1)
        missing_payload = await service.get_news_detail(999)
        categories = await service.list_categories()

        assert list_payload["total"] == 1
        assert list_payload["hasMore"] is False
        assert detail_payload is not None
        assert detail_payload["views"] == 5
        assert detail_payload["relatedNews"][0]["id"] == 2
        assert missing_payload is None
        assert categories == [
            {
                "id": 1,
                "created_at": None,
                "updated_at": None,
                "name": "Technology",
                "sort_order": 0,
            }
        ]

    asyncio.run(verify())
