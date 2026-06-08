import sys
from pathlib import Path

root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import pytest
from jose import jwt
from uuid import uuid4

@pytest.fixture
def valid_jwt():
    payload = {"sub": str(uuid4())}
    return jwt.encode(payload, "your-secret-key-change-in-production", algorithm="HS256")

@pytest.fixture
def valid_jwt_with_fixed_id():
    expected_seller_id = "123e4567-e89b-12d3-a456-426614174000"
    payload = {"sub": expected_seller_id}
    token = jwt.encode(payload, "your-secret-key-change-in-production", algorithm="HS256")
    return token, expected_seller_id