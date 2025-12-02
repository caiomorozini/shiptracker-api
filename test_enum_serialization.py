import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    SELLER = "SELLER"
    VIEWER = "VIEWER"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

from pydantic import BaseModel

class TestModel(BaseModel):
    role: UserRole
    status: UserStatus

# Test enum serialization
print("Testing enum values:")
print(f"UserRole.ADMIN = {UserRole.ADMIN}")
print(f"UserRole.ADMIN.value = {UserRole.ADMIN.value}")
print(f"str(UserRole.ADMIN) = {str(UserRole.ADMIN)}")

# Test Pydantic serialization
test = TestModel(role=UserRole.ADMIN, status=UserStatus.ACTIVE)
print("\nPydantic model_dump():")
print(test.model_dump())
print("\nPydantic model_dump_json():")
print(test.model_dump_json())
