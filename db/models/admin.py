from typing import List
from sqlmodel import Field, Relationship, SQLModel
from .link import ChatAdminLink


class Admin(SQLModel, table=True):  # type: ignore
    id: int = Field(primary_key=True)
    name: str = Field(nullable=True)
    chats: List["Chat"] = Relationship(  # type: ignore  # noqa: F821
        back_populates="admins",
        link_model=ChatAdminLink,
        sa_relationship_kwargs={"secondary": "chat_admin_link"},
    )
