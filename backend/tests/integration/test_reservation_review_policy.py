"""预约、评论评分与规则维护接口集成测试（TC-043 ~ TC-068）。"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.db.base import get_db
from app.infrastructure.models.orm import AccountORM, ReservationORM, SystemAdminORM
from app.infrastructure.security.password_hasher import hash_with_new_salt
from main import app


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client, db):
    password_hash, salt = hash_with_new_salt("admin123")
    account = AccountORM(username="admin", password_hash=password_hash, salt=salt,
                         role="admin")
    db.add(account)
    db.flush()
    db.add(SystemAdminORM(account_id=account.id, name="系统管理员"))
    db.commit()
    return client.post("/api/auth/login",
                       json={"username": "admin", "password": "admin123"}
                       ).json()["data"]["token"]


@pytest.fixture()
def reader_token(client, seeded):
    return client.post("/api/auth/login",
                       json={"username": "zhangsan", "password": "123456"}
                       ).json()["data"]["token"]


class TestReservation:
    def test_create_reservation(self, client, reader_token, seeded):
        resp = client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                           headers={"Authorization": f"Bearer {reader_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["queue_position"] == 1
        assert body["data"]["expires_at"] == (date.today() + timedelta(days=7)).isoformat()

    def test_duplicate_reservation(self, client, reader_token, seeded):
        client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                    headers={"Authorization": f"Bearer {reader_token}"})
        resp = client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 400
        assert "已预约" in resp.json()["message"]

    def test_reserve_title_not_found(self, client, reader_token, seeded):
        resp = client.post("/api/reservations", json={"title_id": 999},
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 404

    def test_cancel_reservation(self, client, reader_token, seeded):
        create = client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                             headers={"Authorization": f"Bearer {reader_token}"})
        resv_id = create.json()["data"]["reservation_id"]

        resp = client.post(f"/api/reservations/{resv_id}/cancel",
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["status"] == "CANCELLED"

    def test_cancel_twice_rejected(self, client, reader_token, seeded):
        create = client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                             headers={"Authorization": f"Bearer {reader_token}"})
        resv_id = create.json()["data"]["reservation_id"]
        client.post(f"/api/reservations/{resv_id}/cancel",
                    headers={"Authorization": f"Bearer {reader_token}"})
        resp = client.post(f"/api/reservations/{resv_id}/cancel",
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 400

    def test_expired_reservation_not_blocking(self, client, reader_token, seeded, db):
        create = client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                             headers={"Authorization": f"Bearer {reader_token}"})
        resv_id = create.json()["data"]["reservation_id"]

        orm = db.query(ReservationORM).filter(ReservationORM.id == resv_id).first()
        orm.expires_at = date.today() - timedelta(days=1)
        db.commit()

        # 过期后可再次预约（惰性失效）
        resp = client.post("/api/reservations", json={"title_id": seeded["title_id"]},
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["queue_position"] == 1


class TestReview:
    def test_submit_review(self, client, reader_token, seeded):
        resp = client.post("/api/reviews",
                           json={"title_id": seeded["title_id"], "rating": 5,
                                 "comment": "太好看了"},
                           headers={"Authorization": f"Bearer {reader_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["status"] == "PENDING"

    def test_rating_out_of_range(self, client, reader_token, seeded):
        resp = client.post("/api/reviews",
                           json={"title_id": seeded["title_id"], "rating": 6},
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 400
        assert "1-5" in resp.json()["message"]

    def test_pending_review_not_visible(self, client, reader_token, seeded):
        client.post("/api/reviews",
                    json={"title_id": seeded["title_id"], "rating": 5},
                    headers={"Authorization": f"Bearer {reader_token}"})
        resp = client.get(f"/api/reviews?title_id={seeded['title_id']}",
                          headers={"Authorization": f"Bearer {reader_token}"})
        body = resp.json()
        assert body["data"]["total"] == 0
        assert body["data"]["average_rating"] == 0.0

    def test_approve_then_visible(self, client, reader_token, admin_token, seeded, db):
        submit = client.post("/api/reviews",
                             json={"title_id": seeded["title_id"], "rating": 5,
                                   "comment": "太好看了"},
                             headers={"Authorization": f"Bearer {reader_token}"})
        review_id = submit.json()["data"]["review_id"]

        resp = client.post(f"/api/reviews/{review_id}/moderate",
                           json={"decision": "APPROVED"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 200

        listed = client.get(f"/api/reviews?title_id={seeded['title_id']}",
                            headers={"Authorization": f"Bearer {reader_token}"})
        body = listed.json()
        assert body["data"]["total"] == 1
        assert body["data"]["average_rating"] == 5.0

    def test_non_admin_cannot_moderate(self, client, reader_token, seeded):
        submit = client.post("/api/reviews",
                             json={"title_id": seeded["title_id"], "rating": 4},
                             headers={"Authorization": f"Bearer {reader_token}"})
        review_id = submit.json()["data"]["review_id"]

        resp = client.post(f"/api/reviews/{review_id}/moderate",
                           json={"decision": "APPROVED"},
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 403

    def test_double_moderate_rejected(self, client, reader_token, admin_token, seeded):
        submit = client.post("/api/reviews",
                             json={"title_id": seeded["title_id"], "rating": 4},
                             headers={"Authorization": f"Bearer {reader_token}"})
        review_id = submit.json()["data"]["review_id"]
        client.post(f"/api/reviews/{review_id}/moderate", json={"decision": "APPROVED"},
                    headers={"Authorization": f"Bearer {admin_token}"})
        resp = client.post(f"/api/reviews/{review_id}/moderate",
                           json={"decision": "REJECTED"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400

    def test_update_resets_to_pending(self, client, reader_token, admin_token, seeded):
        submit = client.post("/api/reviews",
                             json={"title_id": seeded["title_id"], "rating": 5},
                             headers={"Authorization": f"Bearer {reader_token}"})
        review_id = submit.json()["data"]["review_id"]
        client.post(f"/api/reviews/{review_id}/moderate", json={"decision": "APPROVED"},
                    headers={"Authorization": f"Bearer {admin_token}"})

        upd = client.post("/api/reviews",
                          json={"title_id": seeded["title_id"], "rating": 3,
                                "comment": "改评"},
                          headers={"Authorization": f"Bearer {reader_token}"})
        assert upd.json()["data"]["status"] == "PENDING"

        listed = client.get(f"/api/reviews?title_id={seeded['title_id']}",
                            headers={"Authorization": f"Bearer {reader_token}"})
        assert listed.json()["data"]["total"] == 0


class TestPolicyMaintenance:
    def test_update_borrow_policy(self, client, admin_token, seeded):
        resp = client.put("/api/admin/policies/borrow",
                          json={"reader_type": "UNDERGRADUATE", "item_type": "ALL",
                                "max_borrow_count": 8, "borrow_days": 45},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["max_borrow_count"] == 8

    def test_invalid_borrow_policy(self, client, admin_token, seeded):
        resp = client.put("/api/admin/policies/borrow",
                          json={"reader_type": "UNDERGRADUATE", "item_type": "ALL",
                                "max_borrow_count": 0, "borrow_days": 30},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400

    def test_update_fine_rule(self, client, admin_token, seeded):
        resp = client.put("/api/admin/policies/fine",
                          json={"item_category": "THESIS", "grace_days": 1,
                                "amount_per_day": 3.0},
                          headers={"Authorization": f"Bearer {admin_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["grace_days"] == 1

    def test_negative_fine_rule_rejected(self, client, admin_token, seeded):
        resp = client.put("/api/admin/policies/fine",
                          json={"item_category": "THESIS", "grace_days": -1,
                                "amount_per_day": 1.0},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.json()["code"] == 400

    def test_non_admin_cannot_update_policy(self, client, reader_token, seeded):
        resp = client.put("/api/admin/policies/borrow",
                          json={"reader_type": "UNDERGRADUATE", "item_type": "ALL",
                                "max_borrow_count": 9, "borrow_days": 30},
                          headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 403
