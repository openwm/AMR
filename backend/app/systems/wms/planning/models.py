from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PlanningConfig(Base):
    __tablename__ = "planning_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    max_active_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_picking_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
