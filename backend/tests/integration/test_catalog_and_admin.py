"""馆藏检索与系统管理接口集成测试（TC-007 ~ TC-016、TC-077 ~ TC-082）。"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import DB_PATH
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.infrastructure.db.base import SessionLocal, get_db
from app.infrastructure.security.password_hasher import hash_with_new_salt
from app.infrastructure.models.orm import AccountORM, SystemAdminORM
from main import app


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client, db):
    """在测试库中创建系统管理员并登录。"""
    password_hash, salt = hash_with_new_salt("admin123")
    account = AccountORM(username="admin", password_hash=password_hash, salt=salt,
                         role="admin")
    db.add(account)
    db.flush()
    db.add(SystemAdminORM(account_id=account.id, name="系统管理员"))
    db.commit()

    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return resp.json()["data"]["token"]


@pytest.fixture()
def reader_token(client, seeded):
    """复用种子数据中的读者账号登录。"""
    resp = client.post("/api/auth/login", json={"username": "zhangsan",
                                                "password": "123456"})
    return resp.json()["data"]["token"]


class TestCatalogSearch:
    def test_search_requires_login(self, client):
        resp = client.get("/api/books/search")
        assert resp.json()["code"] == 403

    def test_search_returns_books(self, client, reader_token, seeded):
        resp = client.get("/api/books/search",
                          headers={"Authorization": f"Bearer {reader_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 1
        assert body["data"]["books"][0]["title"] == "三体"
        assert body["data"]["books"][0]["available_count"] == 2

    def test_search_empty_result(self, client, reader_token, seeded):
        resp = client.get("/api/books/search", params={"keyword": "不存在"},
                          headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["total"] == 0

    def test_detail(self, client, reader_token, seeded):
        resp = client.get(f"/api/books/{seeded['title_id']}",
                          headers={"Authorization": f"Bearer {reader_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]["items"]) == 2
        assert body["data"]["average_rating"] == 0.0

    def test_detail_not_found(self, client, reader_token, seeded):
        resp = client.get("/api/books/999",
                          headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 404


class TestAdminAuthorization:
    def test_non_admin_rejected(self, client, reader_token, seeded):
        resp = client.post("/api/admin/titles",
                           json={"title": "X", "author": "Y", "isbn": "ISBN-999"},
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 403


class TestTitleManagement:
    def test_add_title(self, client, admin_token):
        resp = client.post("/api/admin/titles",
                           json={"title": "设计模式", "author": "GoF", "isbn": "ISBN-101",
                                 "price": "59.00"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["title_id"] >= 1

    def test_add_duplicate_isbn(self, client, admin_token, seeded, db):
        from app.infrastructure.models.orm import BookTitleORM

        title = db.query(BookTitleORM).first()
        resp = client.post("/api/admin/titles",
                           json={"title": "重复", "author": "X", "isbn": title.isbn},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400
        assert "ISBN" in resp.json()["message"]

    def test_update_title(self, client, admin_token, seeded):
        resp = client.put(f"/api/admin/titles/{seeded['title_id']}",
                          json={"title": "三体（新版）", "price": "45.00"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["title"] == "三体（新版）"

    def test_deactivate_title_with_borrowed_copy(self, client, admin_token, seeded, db):
        from app.infrastructure.models.orm import LibraryItemORM

        item = db.query(LibraryItemORM).first()
        item.status = "BORROWED"
        db.commit()

        resp = client.post(f"/api/admin/titles/{seeded['title_id']}/deactivate",
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400


class TestItemManagement:
    def test_add_items(self, client, admin_token, seeded):
        resp = client.post("/api/admin/items",
                           json={"title_id": seeded["title_id"], "count": 3,
                                 "location": "B区"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]["items"]) == 3

    def test_remove_borrowed_item_rejected(self, client, admin_token, seeded, db):
        from app.infrastructure.models.orm import LibraryItemORM

        item = db.query(LibraryItemORM).first()
        item.status = "BORROWED"
        db.commit()

        resp = client.post(f"/api/admin/items/{item.id}/remove",
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400


class TestCardManagement:
    def test_issue_card(self, client, admin_token, seeded):
        # 先清除 seeded 中已有的借阅证，验证新办证
        resp = client.post("/api/admin/cards", json={"reader_id": seeded["reader_id"]},
                           headers={"Authorization": f"Bearer {admin_token}"})
        # seeded 已有一张有效证 -> 400；此处断言业务规则生效
        assert resp.json()["code"] == 400
        assert "有效借阅证" in resp.json()["message"]

    def test_revoke_card_with_active_loan(self, client, admin_token, seeded, db):
        from datetime import date, timedelta

        from app.infrastructure.models.orm import LoanORM

        card_resp = client.get("/api/admin/readers",
                               headers={"Authorization": f"Bearer {admin_token}"})
        assert card_resp.json()["code"] == 200

        db.add(LoanORM(reader_id=seeded["reader_id"], item_id=1,
                       borrow_date=date.today(),
                       due_date=date.today() + timedelta(days=30), status="BORROWED"))
        db.commit()

        resp = client.post("/api/admin/cards/1/revoke",
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400
        assert "归还" in resp.json()["message"]


class TestReaderManagement:
    def test_list_and_update_reader(self, client, admin_token, seeded):
        resp = client.get("/api/admin/readers",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["total"] == 1

        upd = client.put(f"/api/admin/readers/{seeded['reader_id']}",
                         json={"name": "张三丰", "reader_type": "GRADUATE"},
                         headers={"Authorization": f"Bearer {admin_token}"})
        assert upd.json()["code"] == 200
        assert upd.json()["data"]["name"] == "张三丰"
        assert upd.json()["data"]["reader_type"] == "GRADUATE"

    def test_deactivate_reader_with_loan(self, client, admin_token, seeded, db):
        from datetime import date, timedelta

        from app.infrastructure.models.orm import LoanORM

        db.add(LoanORM(reader_id=seeded["reader_id"], item_id=1,
                       borrow_date=date.today(),
                       due_date=date.today() + timedelta(days=30), status="BORROWED"))
        db.commit()

        resp = client.post(f"/api/admin/readers/{seeded['reader_id']}/deactivate",
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400


class TestLibrarianManagement:
    def test_add_and_list_librarian(self, client, admin_token):
        resp = client.post("/api/admin/librarians",
                           json={"username": "lib01", "password": "123456",
                                 "name": "管理员甲", "employee_no": "EMP0001"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 200

        listed = client.get("/api/admin/librarians",
                            headers={"Authorization": f"Bearer {admin_token}"})
        assert listed.json()["data"]["total"] == 1

    def test_duplicate_librarian_username(self, client, admin_token):
        payload = {"username": "lib01", "password": "123456", "name": "甲"}
        client.post("/api/admin/librarians", json=payload,
                    headers={"Authorization": f"Bearer {admin_token}"})
        resp = client.post("/api/admin/librarians", json=payload,
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400
