"""流通接口集成测试：借书、还书、罚款、赔偿（TC-017 ~ TC-042、TC-069 ~ TC-076）。"""

from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.db.base import get_db
from app.infrastructure.models.orm import (
    AccountORM,
    BorrowCardORM,
    FineRuleORM,
    LibrarianORM,
    LoanORM,
)
from app.infrastructure.security.password_hasher import hash_with_new_salt
from main import app


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def lib_token(client, db):
    password_hash, salt = hash_with_new_salt("123456")
    account = AccountORM(username="lib01", password_hash=password_hash, salt=salt,
                         role="librarian")
    db.add(account)
    db.flush()
    db.add(LibrarianORM(account_id=account.id, name="管理员甲", employee_no="EMP0001"))
    db.commit()
    resp = client.post("/api/auth/login", json={"username": "lib01",
                                                "password": "123456"})
    return resp.json()["data"]["token"]


@pytest.fixture()
def reader_token(client, seeded):
    resp = client.post("/api/auth/login", json={"username": "zhangsan",
                                                "password": "123456"})
    return resp.json()["data"]["token"]


def _borrow(client, token, card_no="CARD2026000001", barcode="ITEM2026000001"):
    return client.post("/api/circulation/borrow",
                       json={"card_no": card_no, "barcode": barcode},
                       headers={"Authorization": f"Bearer {token}"})


class TestBorrow:
    def test_non_librarian_rejected(self, client, reader_token, seeded):
        resp = _borrow(client, reader_token)
        assert resp.json()["code"] == 403

    def test_borrow_success(self, client, lib_token, seeded):
        resp = _borrow(client, lib_token)
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["due_date"] == (date.today() + timedelta(days=30)).isoformat()
        assert body["data"]["title"] == "三体"

    def test_card_not_found(self, client, lib_token, seeded):
        resp = _borrow(client, lib_token, card_no="CARD-NOPE")
        assert resp.json()["code"] == 404

    def test_item_not_found(self, client, lib_token, seeded):
        resp = _borrow(client, lib_token, barcode="ITEM-NOPE")
        assert resp.json()["code"] == 404

    def test_invalid_card(self, client, lib_token, seeded, db):
        card = db.query(BorrowCardORM).first()
        card.status = "REVOKED"
        db.commit()
        resp = _borrow(client, lib_token)
        assert resp.json()["code"] == 400
        assert "借阅证无效" in resp.json()["message"]

    def test_quota_exceeded(self, client, lib_token, seeded, db):
        # 本科生上限 5：先补足 5 个副本，再预置 5 条在借记录
        from app.infrastructure.models.orm import LibraryItemORM

        today = date.today()
        item_ids = []
        for i in range(11, 16):
            item = LibraryItemORM(barcode=f"ITEM20260000{i}", title_id=seeded["title_id"],
                                  item_type="BOOK", status="BORROWED",
                                  fine_category="CHINESE_BOOK")
            db.add(item)
            db.flush()
            item_ids.append(item.id)
        for item_id in item_ids:
            db.add(LoanORM(reader_id=seeded["reader_id"], item_id=item_id,
                           borrow_date=today, due_date=today + timedelta(days=30),
                           status="BORROWED"))
        db.commit()
        resp = _borrow(client, lib_token)
        assert resp.json()["code"] == 400
        assert "借阅已满" in resp.json()["message"]

    def test_has_overdue(self, client, lib_token, seeded, db):
        today = date.today()
        db.add(LoanORM(reader_id=seeded["reader_id"], item_id=1,
                       borrow_date=today - timedelta(days=40),
                       due_date=today - timedelta(days=10), status="BORROWED"))
        db.commit()
        resp = _borrow(client, lib_token)
        assert resp.json()["code"] == 400
        assert "超期" in resp.json()["message"]

    def test_item_not_available(self, client, lib_token, seeded, db):
        from app.infrastructure.models.orm import LibraryItemORM

        item = db.query(LibraryItemORM).filter_by(barcode="ITEM2026000001").first()
        item.status = "BORROWED"
        db.commit()
        resp = _borrow(client, lib_token)
        assert resp.json()["code"] == 400
        assert "不可借" in resp.json()["message"]

    def test_magazine_due_date_override(self, client, lib_token, seeded, db):
        """二维策略：杂志期限 7 天。"""
        from app.infrastructure.models.orm import BookTitleORM, LibraryItemORM

        title = BookTitleORM(title="计算机学报", author="学会", isbn="ISSN-1",
                             item_type="MAGAZINE", price="60.00")
        db.add(title)
        db.flush()
        db.add(LibraryItemORM(barcode="ITEM2026000100", title_id=title.id,
                              item_type="MAGAZINE", status="AVAILABLE",
                              fine_category="CHINESE_MAGAZINE"))
        db.commit()

        resp = _borrow(client, lib_token, barcode="ITEM2026000100")
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["due_date"] == (date.today() + timedelta(days=7)).isoformat()


class TestReturn:
    def _borrow_first(self, client, lib_token, seeded):
        resp = _borrow(client, lib_token)
        return resp.json()["data"]["loan_id"]

    def test_return_success(self, client, lib_token, seeded):
        self._borrow_first(client, lib_token, seeded)
        resp = client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["overdue_days"] == 0
        assert float(body["data"]["fine"]) == 0.0

    def test_return_not_library_item(self, client, lib_token, seeded):
        resp = client.post("/api/circulation/return", json={"barcode": "ITEM-NOPE"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400
        assert "非本馆藏书" in resp.json()["message"]

    def test_return_without_loan(self, client, lib_token, seeded):
        resp = client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400
        assert "未找到" in resp.json()["message"]

    def test_overdue_generates_fine(self, client, lib_token, seeded, db):
        self._borrow_first(client, lib_token, seeded)
        # 将应还日期改为 4 天前（中文图书 0.5 元/天，无宽限期）
        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=4)
        db.commit()

        resp = client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["overdue_days"] == 4
        assert float(body["data"]["fine"]) == 2.0

    def test_grace_period_no_fine(self, client, lib_token, seeded, db):
        """外文图书宽限期 3 天：逾期 3 天不计费、不生成记录。"""
        self._borrow_first(client, lib_token, seeded)
        from app.infrastructure.models.orm import LibraryItemORM

        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=3)
        item = db.query(LibraryItemORM).filter_by(barcode="ITEM2026000001").first()
        item.fine_category = "FOREIGN_BOOK"
        db.commit()

        resp = client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["overdue_days"] == 3
        assert float(body["data"]["fine"]) == 0.0

    def test_beyond_grace_period_charges(self, client, lib_token, seeded, db):
        """外文图书逾期 5 天，扣 3 天宽限 → 2 天 × 1.0 = 2.0"""
        self._borrow_first(client, lib_token, seeded)
        from app.infrastructure.models.orm import LibraryItemORM

        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=5)
        item = db.query(LibraryItemORM).filter_by(barcode="ITEM2026000001").first()
        item.fine_category = "FOREIGN_BOOK"
        db.commit()

        resp = client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert float(resp.json()["data"]["fine"]) == 2.0

    def test_unpaid_fine_blocks_borrow(self, client, lib_token, seeded, db):
        from app.infrastructure.models.orm import FineRecordORM

        self._borrow_first(client, lib_token, seeded)
        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=4)
        db.commit()
        client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                    headers={"Authorization": f"Bearer {lib_token}"})

        # 借第二本应被未缴罚款拦截
        resp = _borrow(client, lib_token, barcode="ITEM2026000002")
        assert resp.json()["code"] == 400
        assert "未缴" in resp.json()["message"]

        # 缴清后可借
        fine = db.query(FineRecordORM).first()
        pay = client.post(f"/api/circulation/fines/{fine.id}/pay",
                          headers={"Authorization": f"Bearer {lib_token}"})
        assert pay.json()["code"] == 200

        resp2 = _borrow(client, lib_token, barcode="ITEM2026000002")
        assert resp2.json()["code"] == 200

    def test_pay_fine_twice_rejected(self, client, lib_token, seeded, db):
        from app.infrastructure.models.orm import FineRecordORM

        self._borrow_first(client, lib_token, seeded)
        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=4)
        db.commit()
        client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                    headers={"Authorization": f"Bearer {lib_token}"})

        fine = db.query(FineRecordORM).first()
        client.post(f"/api/circulation/fines/{fine.id}/pay",
                    headers={"Authorization": f"Bearer {lib_token}"})
        resp = client.post(f"/api/circulation/fines/{fine.id}/pay",
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400


class TestLostAndCompensation:
    def test_report_lost(self, client, lib_token, seeded):
        _borrow(client, lib_token)
        resp = client.post("/api/circulation/lost", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        body = resp.json()
        assert body["code"] == 200
        # 三体定价 39.80 × 2.0 = 79.60
        assert float(body["data"]["amount"]) == 79.6

    def test_report_lost_without_loan(self, client, lib_token, seeded):
        resp = client.post("/api/circulation/lost", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400

    def test_unpaid_compensation_blocks_borrow(self, client, lib_token, seeded, db):
        from app.infrastructure.models.orm import LostItemORM

        _borrow(client, lib_token)
        client.post("/api/circulation/lost", json={"barcode": "ITEM2026000001"},
                    headers={"Authorization": f"Bearer {lib_token}"})

        resp = _borrow(client, lib_token, barcode="ITEM2026000002")
        assert resp.json()["code"] == 400

        lost = db.query(LostItemORM).first()
        pay = client.post(f"/api/circulation/lost/{lost.id}/pay",
                          headers={"Authorization": f"Bearer {lib_token}"})
        assert pay.json()["code"] == 200

    def test_lost_item_removed(self, client, lib_token, seeded, db):
        from app.infrastructure.models.orm import LibraryItemORM

        _borrow(client, lib_token)
        client.post("/api/circulation/lost", json={"barcode": "ITEM2026000001"},
                    headers={"Authorization": f"Bearer {lib_token}"})
        item = db.query(LibraryItemORM).filter_by(barcode="ITEM2026000001").first()
        assert item.status == "REMOVED"


class TestRenew:
    def test_renew_success(self, client, lib_token, seeded):
        _borrow(client, lib_token)
        loan_id = 1
        resp = client.post("/api/circulation/renew", json={"loan_id": loan_id},
                           headers={"Authorization": f"Bearer {lib_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["renew_count"] == 1

    def test_renew_twice_rejected(self, client, lib_token, seeded):
        _borrow(client, lib_token)
        client.post("/api/circulation/renew", json={"loan_id": 1},
                    headers={"Authorization": f"Bearer {lib_token}"})
        resp = client.post("/api/circulation/renew", json={"loan_id": 1},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400
        assert "续借上限" in resp.json()["message"]

    def test_renew_overdue_rejected(self, client, lib_token, seeded, db):
        _borrow(client, lib_token)
        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=1)
        db.commit()
        resp = client.post("/api/circulation/renew", json={"loan_id": 1},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400


class TestLoanRecords:
    def test_reader_can_query_self(self, client, reader_token, seeded, db):
        from app.infrastructure.models.orm import ReaderORM

        reader = db.query(ReaderORM).first()
        resp = client.get(f"/api/circulation/records/{reader.id}",
                          headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 200

    def test_reader_cannot_query_others(self, client, reader_token, seeded):
        resp = client.get("/api/circulation/records/999",
                          headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 403

    def test_librarian_can_query_any(self, client, lib_token, seeded):
        resp = client.get(f"/api/circulation/records/{seeded['reader_id']}",
                          headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 200
        assert "records" in resp.json()["data"]


class TestReturnRequestAudit:
    """BR-020：读者发起归还申请、图书管理员审核（TC-083 ~ TC-094）。"""

    def _borrow(self, client, lib_token) -> int:
        return _borrow(client, lib_token).json()["data"]["loan_id"]

    def _apply(self, client, token, loan_id):
        return client.post("/api/circulation/return-request", json={"loan_id": loan_id},
                           headers={"Authorization": f"Bearer {token}"})

    def _pending(self, client, lib_token):
        return client.get("/api/circulation/return-requests",
                          headers={"Authorization": f"Bearer {lib_token}"})

    def test_reader_apply_then_librarian_approve(self, client, reader_token, lib_token,
                                                 seeded):
        loan_id = self._borrow(client, lib_token)

        apply_resp = self._apply(client, reader_token, loan_id)
        assert apply_resp.json()["code"] == 200
        assert apply_resp.json()["data"]["status"] == "RETURN_REQUESTED"
        assert self._pending(client, lib_token).json()["data"]["total"] == 1

        approve = client.post(f"/api/circulation/return-requests/{loan_id}/approve",
                              headers={"Authorization": f"Bearer {lib_token}"})
        body = approve.json()
        assert body["code"] == 200
        assert body["data"]["overdue_days"] == 0
        assert float(body["data"]["fine"]) == 0.0

        assert self._pending(client, lib_token).json()["data"]["total"] == 0
        records = client.get(f"/api/circulation/records/{seeded['reader_id']}",
                             headers={"Authorization": f"Bearer {lib_token}"})
        assert records.json()["data"]["records"][0]["status"] == "RETURNED"

    def test_apply_requires_ownership(self, client, lib_token, seeded, db):
        from app.infrastructure.models.orm import ReaderORM

        loan_id = self._borrow(client, lib_token)

        password_hash, salt = hash_with_new_salt("123456")
        other_account = AccountORM(username="lisi", password_hash=password_hash,
                                   salt=salt, role="reader")
        db.add(other_account)
        db.flush()
        db.add(ReaderORM(account_id=other_account.id, name="李四",
                         reader_type="UNDERGRADUATE"))
        db.commit()
        token = client.post("/api/auth/login",
                            json={"username": "lisi", "password": "123456"}).json()["data"]["token"]

        resp = self._apply(client, token, loan_id)
        assert resp.json()["code"] == 403

    def test_non_librarian_cannot_approve(self, client, reader_token, lib_token, seeded):
        loan_id = self._borrow(client, lib_token)
        self._apply(client, reader_token, loan_id)
        resp = client.post(f"/api/circulation/return-requests/{loan_id}/approve",
                           headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.json()["code"] == 403

    def test_reject_restores_borrowed(self, client, reader_token, lib_token, seeded):
        loan_id = self._borrow(client, lib_token)
        self._apply(client, reader_token, loan_id)

        resp = client.post(f"/api/circulation/return-requests/{loan_id}/reject",
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["status"] == "BORROWED"
        assert self._pending(client, lib_token).json()["data"]["total"] == 0

        # 驳回后可再次续借（状态已回到 BORROWED）
        renew = client.post("/api/circulation/renew", json={"loan_id": loan_id},
                            headers={"Authorization": f"Bearer {reader_token}"})
        assert renew.json()["code"] == 200

    def test_approve_without_request_rejected(self, client, lib_token, seeded):
        loan_id = self._borrow(client, lib_token)
        resp = client.post(f"/api/circulation/return-requests/{loan_id}/approve",
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 400
        assert "归还申请" in resp.json()["message"]

    def test_pending_request_keeps_quota_and_blocks_renew(self, client, reader_token,
                                                          lib_token, seeded):
        loan_id = self._borrow(client, lib_token)
        self._apply(client, reader_token, loan_id)

        # 申请中仍占用借阅配额（书未回馆）
        records = client.get(
            f"/api/circulation/records/{seeded['reader_id']}?status=RETURN_REQUESTED",
            headers={"Authorization": f"Bearer {lib_token}"},
        )
        assert records.json()["data"]["total"] == 1

        renew = client.post("/api/circulation/renew", json={"loan_id": loan_id},
                            headers={"Authorization": f"Bearer {reader_token}"})
        assert renew.json()["code"] == 400
        assert "归还申请" in renew.json()["message"]

    def test_approve_overdue_still_charges_fine(self, client, reader_token, lib_token,
                                                seeded, db):
        loan_id = self._borrow(client, lib_token)
        loan = db.query(LoanORM).first()
        loan.due_date = date.today() - timedelta(days=4)
        db.commit()

        self._apply(client, reader_token, loan_id)
        resp = client.post(f"/api/circulation/return-requests/{loan_id}/approve",
                           headers={"Authorization": f"Bearer {lib_token}"})
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["overdue_days"] == 4
        assert float(body["data"]["fine"]) == 2.0

    def test_librarian_can_return_on_the_spot(self, client, lib_token, seeded):
        """现场办理：读者未先申请，馆员凭条码直接归还（保留通道）。"""
        self._borrow(client, lib_token)
        resp = client.post("/api/circulation/return", json={"barcode": "ITEM2026000001"},
                           headers={"Authorization": f"Bearer {lib_token}"})
        assert resp.json()["code"] == 200
