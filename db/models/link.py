from sqlmodel import Field, SQLModel


class ChatAdminLink(SQLModel, table=True):  # type: ignore
    __tablename__ = "chat_admin_link"

    chat_id: int = Field(foreign_key="chat.id", primary_key=True)
    admin_id: int = Field(foreign_key="admin.id", primary_key=True)
