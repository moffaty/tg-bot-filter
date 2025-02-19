from typing import List
from sqlmodel import Field, Relationship, SQLModel
from .link import ChatAdminLink


class Chat(SQLModel, table=True):  # type: ignore
    id: int = Field(primary_key=True)
    title: str
    admins: List["Admin"] = Relationship(  # type: ignore  # noqa: F821
        back_populates="chats",
        link_model=ChatAdminLink,
        sa_relationship_kwargs={"secondary": "chat_admin_link"},
    )
