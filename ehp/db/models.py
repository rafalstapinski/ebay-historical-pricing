from __future__ import annotations

from datetime import date, datetime

from p3orm import Column, ForeignKeyRelationship, ReverseRelationship, Table
from p3orm.fields import _PormField


def _id() -> _PormField:
    return Column(int, pk=True, autogen=True)


def _at() -> _PormField:
    return Column(datetime, autogen=True)


class Item(Table):
    __tablename__ = "item"

    id = _id()
    name = Column(str)

    created_at = _at()
    deleted_at = Column(datetime | None)

    sales: list[Sale] = ReverseRelationship(self_column="id", foreign_column="item_id")


class Sale(Table):
    __tablename__ = "sale"

    id = _id()
    item_id = Column(int)
    listing_price = Column(int)
    listing_name = Column(str)
    listing_url = Column(str)
    listing_image = Column(str)
    sold_at = Column(date)

    created_at = _at()

    item: Item = ForeignKeyRelationship(self_column="item_id", foreign_column="id")
