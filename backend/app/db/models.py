from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.session import Base

# Join table: many-to-many between providers and capabilities
provider_capabilities = Table(
    "provider_capabilities",
    Base.metadata,
    Column("provider_id", Integer, ForeignKey("providers.id"), primary_key=True),
    Column("capability_id", Integer, ForeignKey("capabilities.id"), primary_key=True),
)


class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # e.g. "towing"

    providers = relationship(
        "Provider", secondary=provider_capabilities, back_populates="capabilities" #secondary in simple words is the join table that connects the two tables, and back_populates is used to establish a bidirectional relationship between the two models.
    )


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    vehicle_types = Column(String, nullable=False)  # comma-separated, e.g. "car,suv"
    is_available = Column(Boolean, default=True, nullable=False)
    rating = Column(Float, default=0.0, nullable=False)

    capabilities = relationship(
        "Capability", secondary=provider_capabilities, back_populates="providers" #provider_capabilties is the middle table that connects the two tables, and back_populates is used to establish a bidirectional relationship between the two models.
    )

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    required_capability = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    status = Column(String, nullable=False, default="assigned")  # assigned | failed | reassigned

    provider = relationship("Provider")