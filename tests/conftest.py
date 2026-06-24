from __future__ import annotations

import os

os.environ["USE_MOCK_DATA"] = "true"
os.environ["DEEPSEEK_API_KEY"] = "test-key"
os.environ["C1_BASE_URL"] = "http://test.local"
os.environ["C1_USERNAME"] = "test"
os.environ["C1_PASSWORD"] = "test"
os.environ["AUTH_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345678901234567890"
