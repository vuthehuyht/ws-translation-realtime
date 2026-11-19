"""Unit tests for CustomVocabulary ORM model (app.models.vocabulary)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vocabulary import CustomVocabulary


async def test_create_custom_vocabulary(db_session: AsyncSession) -> None:
    user_id = "vocab-host-sub"
    user = User(id=user_id, email="vocab_host@example.com")
    vocab = CustomVocabulary(
        host_id=user_id,
        name="Medical Terms",
        language_code="vi-VN",
        terms=["Huyết áp", "Kháng sinh"],
    )

    db_session.add_all([user, vocab])
    await db_session.flush()

    stmt = select(CustomVocabulary).where(CustomVocabulary.host_id == user_id)
    fetched = (await db_session.execute(stmt)).scalar_one()
    assert fetched.name == "Medical Terms"
    assert fetched.language_code == "vi-VN"
    assert fetched.terms == ["Huyết áp", "Kháng sinh"]
