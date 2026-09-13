"""认证接口集成测试（TC-001 ~ TC-006）。"""

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.db.base import get_db
from main import app


@pytest.fixture()
def client(db):
    """覆盖数据库依赖，使用临时库。"""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register(client, username="zhangsan", password="123456", name="张三",
              reader_type="UNDERGRADUATE"):
    return client.post("/api/auth/register", json={
        "username": username,
        "password": password,
        "name": name,
        "reader_type": reader_type,
    })


def _login(client, username="zhangsan", password="123456"):
    return client.post("/api/auth/login", json={
        "username": username,
        "password": password,
    })


class TestRegister:
    def test_register_success(self, client):
        resp = _register(client)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["username"] == "zhangsan"
        assert body["data"]["reader_type"] == "UNDERGRADUATE"

    def test_register_duplicate_username(self, client):
        _register(client)
        resp = _register(client)
        assert resp.json()["code"] == 400
        assert "用户名已存在" in resp.json()["message"]

    def test_register_missing_fields(self, client):
        resp = client.post("/api/auth/register", json={"username": "x"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        _register(client)
        resp = _login(client)
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["token"]
        assert body["data"]["role"] == "reader"
        assert body["data"]["user_id"] >= 1

    def test_login_wrong_password(self, client):
        _register(client)
        resp = _login(client, password="wrong")
        assert resp.status_code == 403
        assert resp.json()["code"] == 403
        assert resp.json()["message"] == "用户名或密码错误"

    def test_login_nonexistent_user(self, client):
        resp = _login(client)
        assert resp.json()["code"] == 403

    def test_password_not_stored_in_plain_text(self, client, db):
        from app.infrastructure.models.orm import AccountORM

        _register(client, password="secret123")
        orm = db.query(AccountORM).filter(AccountORM.username == "zhangsan").first()
        assert orm.password_hash != "secret123"
        assert len(orm.salt) == 32
        assert len(orm.password_hash) == 64


class TestToken:
    def test_logout_requires_token(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.json()["code"] == 403

    def test_logout_invalidates_token(self, client):
        _register(client)
        token = _login(client).json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/api/auth/logout", headers=headers)
        assert resp.json()["code"] == 200

        # 令牌失效后再次使用
        resp2 = client.post("/api/auth/logout", headers=headers)
        assert resp2.json()["code"] == 403

    def test_invalid_token_rejected(self, client):
        resp = client.post("/api/auth/logout",
                           headers={"Authorization": "Bearer invalid-token"})
        assert resp.json()["code"] == 403
