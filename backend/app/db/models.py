from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.db.session import Base

# Provider <-> Capability many-to-many relationshi

provider_capabilities = Table(
    "provider_capabilities",
    Base.metadata,
    Column(
        "provider_id",
        Integer,
        ForeignKey("providers.id"),
        primary_key=True,
    ),
    Column(
        "capability_id",
        Integer,
        ForeignKey("capabilities.id"),
        primary_key=True,
    ),
)

# Provider <-> VehicleType many-to-many relationshi

provider_vehicle_types = Table(
    "provider_vehicle_types",
    Base.metadata,
    Column(
        "provider_id",
        Integer,
        ForeignKey("providers.id"),
        primary_key=True,
    ),
    Column(
        "vehicle_type_id",
        Integer,
        ForeignKey("vehicle_types.id"),
        primary_key=True,
    ),
)


class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    providers = relationship(
        "Provider",
        secondary=provider_capabilities,
        back_populates="capabilities",
    )


class VehicleType(Base):
    __tablename__ = "vehicle_types"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    providers = relationship(
        "Provider",
        secondary=provider_vehicle_types,
        back_populates="vehicle_types",
    )


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    is_available = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    rating = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    capabilities = relationship(
        "Capability",
        secondary=provider_capabilities,
        back_populates="providers",
    )

    vehicle_types = relationship(
        "VehicleType",
        secondary=provider_vehicle_types,
        back_populates="providers",
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)

    required_capability = Column(
        String,
        nullable=False,
    )

    vehicle_type = Column(
        String,
        nullable=False,
    )

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    provider_id = Column(
        Integer,
        ForeignKey("providers.id"),
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="assigned",
    )
    # assigned | failed | reassigned

    provider = relationship("Provider")