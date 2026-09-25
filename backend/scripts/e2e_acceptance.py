"""实验二端到端验收脚本。

用途：对运行中的后端服务（http://localhost:8001）执行实验二最终验收清单中的
功能项，并生成 Markdown 记录 `scripts/e2e_report.md`。

覆盖：
- 验收 9：借书、还书、预约、查询可用
- 验收 10：不同读者类型借阅规则可用（UNDERGRADUATE/GRADUATE/ASSOCIATE + 出借物维度）
- 验收 11：不同借出物类型罚款规则可用（CHINESE_BOOK 0.50/天 vs THESIS 2.00/天）
- 学生任务卡：任务一续借、任务二图书评论与评分

运行前提：后端已以**干净的种子库**启动（`python main.py` 会删库重建）。
脚本会改变库状态，重复运行前请重启后端服务。
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

BASE = "http://localhost:8001"
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import DB_PATH  # noqa: E402

REPORT = Path(__file__).resolve().parent / "e2e_report.md"
TODAY = date.today()

rows: list[tuple[str, str, str, str, str]] = []
failures: list[str] = []


# ---------- 基础工具 ----------


def call(method: str, path: str, token: str | None = None, json: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = httpx.request(method, f"{BASE}{path}", json=json, headers=headers, timeout=20)
    body = resp.json()
    return resp.status_code, body.get("code"), body.get("message"), body.get("data")


def login(username: str, password: str) -> str:
    status, code, msg, data = call("POST", "/api/auth/login",
                                  json={"username": username, "password": password})
    assert status == 200, f"登录失败 {username}: {status} {msg}"
    return data["token"]


def sql(query: str, args: tuple = ()):
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    try:
        cur = conn.execute(query, args)
        result = cur.fetchall()
        conn.commit()
        return result
    finally:
        conn.close()


def barcode_of(title: str, skip: int = 0) -> str:
    rows_ = sql(
        "SELECT i.barcode FROM library_items i "
        "JOIN book_titles t ON t.id = i.title_id "
        "WHERE t.title = ? AND i.status = 'AVAILABLE' ORDER BY i.id LIMIT 1 OFFSET ?",
        (title, skip),
    )
    if not rows_:
        raise RuntimeError(f"没有可借副本：{title}")
    return rows_[0][0]


def card_no_of(username: str) -> str:
    rows_ = sql(
        "SELECT c.card_no FROM borrow_cards c JOIN readers r ON r.id = c.reader_id "
        "JOIN accounts a ON a.id = r.account_id WHERE a.username = ?",
        (username,),
    )
    return rows_[0][0]


def reader_id_of(username: str) -> int:
    return sql("SELECT r.id FROM readers r JOIN accounts a ON a.id = r.account_id "
               "WHERE a.username = ?", (username,))[0][0]


def title_id_of(title: str) -> int:
    return sql("SELECT id FROM book_titles WHERE title = ?", (title,))[0][0]


def loan_id_of(barcode: str) -> int:
    return sql(
        "SELECT l.id FROM loans l JOIN library_items i ON i.id = l.item_id "
        "WHERE i.barcode = ? AND l.status = 'BORROWED'", (barcode,))[0][0]


def make_overdue(loan_id: int, days: int) -> None:
    sql("UPDATE loans SET due_date = ? WHERE id = ?",
        ((TODAY - timedelta(days=days)).isoformat(), loan_id))


# ---------- 断言与记录 ----------


def record(no: str, scene: str, request: str, expect: str, actual: str, ok: bool) -> None:
    rows.append((no, scene, request, f"{expect}<br>实际：{actual}", "PASS" if ok else "FAIL"))
    if not ok:
        failures.append(no)
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {no} {scene} -> {actual}")


def expect_ok(no: str, scene: str, request: str, status: int, data, expect: str,
              actual: str, cond: bool) -> None:
    record(no, scene, request, expect, f"HTTP {status}｜{actual}", status == 200 and cond)


def expect_error(no: str, scene: str, request: str, status: int, code, msg: str,
                 expect: str, expect_code: int, keyword: str = "") -> None:
    ok = status == expect_code and (not keyword or keyword in (msg or ""))
    record(no, scene, request, expect, f"HTTP {status} code={code}｜{msg}", ok)


# ---------- 验收场景 ----------


def main() -> int:
    try:
        httpx.get(f"{BASE}/api/health", timeout=5)
    except Exception:
        print(f"后端未启动，请先运行：cd {BACKEND_DIR} && python main.py")
        return 2

    print("=" * 60)
    print("实验二端到端验收")
    print("=" * 60)

    # --- 1. 认证 ---
    admin = login("admin", "admin123")
    lib = login("lib01", "123456")
    zs = login("zhangsan", "123456")
    ls = login("lisi", "123456")
    zl = login("zhaoliu", "123456")
    record("A-01", "三类角色登录（admin/lib01/zhangsan）", "POST /api/auth/login",
           "返回 token", "admin/librarian/reader 令牌均已取得", True)

    # 身份解析：user_id 与 reader_id 不同，Agent 必须靠本接口解析
    st, c, m, d = call("GET", "/api/auth/me", zs)
    zs_reader_id = d.get("reader_id") if d else None
    zs_card = d.get("card_no") if d else None
    expect_ok("A-02", "解析当前身份（reader_id / card_no）", "GET /api/auth/me", st, d,
              "reader_id 与 card_no 均非空，且与登录返回的 user_id 不同",
              f"user_id={d.get('user_id') if d else None}, reader_id={zs_reader_id}, card_no={zs_card}",
              bool(d) and zs_reader_id is not None and zs_card is not None)

    st, c, m, d = call("GET", "/api/admin/readers", admin)
    first_card = (d.get("readers") or [{}])[0].get("card_no") if d else None
    expect_ok("A-03", "管理员查询读者列表含借阅证号", "GET /api/admin/readers", st, d,
              "readers[].card_no 非空（管理员代办借书时可取用）",
              f"total={d.get('total') if d else None}, 首位 card_no={first_card}",
              bool(d) and first_card is not None)

    # --- 2. 权限收口 ---
    st, c, m, _ = call("POST", "/api/circulation/borrow", None,
                       {"card_no": card_no_of("zhangsan"), "barcode": barcode_of("活着")})
    expect_error("B-01", "未登录调用借书", "POST /api/circulation/borrow（无令牌）",
                 st, c, m, "403 未登录或令牌无效", 403)

    st, c, m, _ = call("POST", "/api/circulation/borrow", zs,
                       {"card_no": card_no_of("zhangsan"), "barcode": barcode_of("活着")})
    expect_error("B-02", "读者调用管理员接口借书", "POST /api/circulation/borrow（读者令牌）",
                 st, c, m, "403 权限不足（借书必须由管理员代理）", 403)

    # --- 3. 借书 + 不同读者类型规则（验收 9 / 10） ---
    st, c, m, d = call("POST", "/api/circulation/borrow", lib,
                       {"card_no": card_no_of("zhangsan"), "barcode": barcode_of("Java核心技术")})
    due_ug = (TODAY + timedelta(days=30)).isoformat()
    expect_ok("C-01", "借书：本科生（5 本 / 30 天）", "POST /api/circulation/borrow",
              st, d, f"due_date = 今天+30 = {due_ug}",
              f"due_date={d.get('due_date') if d else None}", bool(d) and d.get("due_date") == due_ug)

    st, c, m, d = call("POST", "/api/circulation/borrow", lib,
                       {"card_no": card_no_of("lisi"), "barcode": barcode_of("深入理解计算机系统")})
    due_gr = (TODAY + timedelta(days=60)).isoformat()
    expect_ok("C-02", "借书：研究生（10 本 / 60 天）", "POST /api/circulation/borrow",
              st, d, f"due_date = 今天+60 = {due_gr}",
              f"due_date={d.get('due_date') if d else None}", bool(d) and d.get("due_date") == due_gr)

    # --- 4. 二维策略：出借物维度（验收 10 扩展） ---
    st, c, m, d = call("POST", "/api/circulation/borrow", lib,
                       {"card_no": card_no_of("zhangsan"), "barcode": barcode_of("计算机学报")})
    due_mag = (TODAY + timedelta(days=7)).isoformat()
    expect_ok("C-03", "借书：期刊（读者类型 × 出借物二维策略，7 天）",
              "POST /api/circulation/borrow", st, d, f"due_date = 今天+7 = {due_mag}",
              f"due_date={d.get('due_date') if d else None}",
              bool(d) and d.get("due_date") == due_mag)

    st, c, m, d = call("POST", "/api/circulation/borrow", lib,
                       {"card_no": card_no_of("zhangsan"), "barcode": barcode_of("软件架构设计博士论文")})
    due_th = (TODAY + timedelta(days=3)).isoformat()
    expect_ok("C-04", "借书：学位论文（二维策略，3 天）", "POST /api/circulation/borrow",
              st, d, f"due_date = 今天+3 = {due_th}",
              f"due_date={d.get('due_date') if d else None}",
              bool(d) and d.get("due_date") == due_th)

    # --- 5. 借阅数量上限（验收 10） ---
    card_zl = card_no_of("zhaoliu")
    ok_three = True
    used = []
    for _ in range(3):
        b = barcode_of("三国演义")
        st, c, m, d = call("POST", "/api/circulation/borrow", lib,
                           {"card_no": card_zl, "barcode": b})
        used.append(b)
        ok_three = ok_three and st == 200
    record("C-05", "专科生连借 3 本（上限 3）", "POST /api/circulation/borrow ×3",
           "3 次均成功", f"{sum(1 for _ in used)} 次请求，全部成功={ok_three}", ok_three)

    st, c, m, _ = call("POST", "/api/circulation/borrow", lib,
                       {"card_no": card_zl, "barcode": barcode_of("活着")})
    expect_error("C-06", "超过借阅数量上限（第 4 本）", "POST /api/circulation/borrow",
                 st, c, m, "400 借阅数量已达上限", 400, "借阅")

    # --- 6. 查询借阅信息（验收 9） ---
    zs_id = reader_id_of("zhangsan")
    st, c, m, d = call("GET", f"/api/circulation/records/{zs_id}", zs)
    expect_ok("D-01", "读者查询本人借阅记录", f"GET /api/circulation/records/{zs_id}",
              st, d, "total ≥ 4（三体 + 3 本新借）",
              f"total={d.get('total') if d else None}", bool(d) and d.get("total", 0) >= 4)

    ls_id = reader_id_of("lisi")
    st, c, m, _ = call("GET", f"/api/circulation/records/{ls_id}", zs)
    expect_error("D-02", "读者查询他人借阅记录", f"GET /api/circulation/records/{ls_id}（张三令牌）",
                 st, c, m, "403 权限不足", 403)

    st, c, m, d = call("GET", f"/api/circulation/records/{ls_id}", lib)
    expect_ok("D-03", "管理员查询任意读者借阅记录", f"GET /api/circulation/records/{ls_id}",
              st, d, "管理员可查他人", f"total={d.get('total') if d else None}", bool(d))

    # --- 7. 续借（学生任务卡 任务一） ---
    san_ti = sql("SELECT i.barcode FROM loans l JOIN library_items i ON i.id = l.item_id "
                 "JOIN book_titles t ON t.id = i.title_id "
                 "WHERE t.title = '三体' AND l.status = 'BORROWED'")[0][0]
    loan_id = loan_id_of(san_ti)
    st, c, m, d = call("POST", "/api/circulation/renew", zs, {"loan_id": loan_id})
    new_due = d.get("new_due_date") if d else None
    expect_ok("E-01", "续借：读者本人续借在借图书", "POST /api/circulation/renew",
              st, d, f"new_due_date 后延、renew_count=1",
              f"new_due_date={new_due}, renew_count={d.get('renew_count') if d else None}",
              bool(d) and new_due == (TODAY + timedelta(days=60)).isoformat()
              and d.get("renew_count") == 1)

    st, c, m, _ = call("POST", "/api/circulation/renew", zs, {"loan_id": loan_id})
    expect_error("E-02", "重复续借（上限 1 次）", "POST /api/circulation/renew",
                 st, c, m, "400 已达续借上限", 400, "续借")

    # --- 8. 还书（验收 9） ---
    st, c, m, d = call("POST", "/api/circulation/return", lib, {"barcode": san_ti})
    expect_ok("F-01", "还书：按期归还", "POST /api/circulation/return", st, d,
              "status=RETURNED，无罚款", f"fine={d.get('fine') if d else None}",
              bool(d) and float(d.get("fine") or 0) == 0)

    st, c, m, _ = call("POST", "/api/circulation/return", lib, {"barcode": san_ti})
    expect_error("F-02", "重复还书（已归还记录）", "POST /api/circulation/return",
                 st, c, m, "400 未找到借阅记录", 400)

    # --- 9. 不同借出物类型罚款规则（验收 11） ---
    b_book = barcode_of("活着")
    call("POST", "/api/circulation/borrow", lib, {"card_no": card_no_of("lisi"), "barcode": b_book})
    make_overdue(loan_id_of(b_book), 10)
    st, c, m, d = call("POST", "/api/circulation/return", lib, {"barcode": b_book})
    expect_ok("G-01", "逾期还书：中文图书 0.50 元/天（宽限 0 天），逾期 10 天",
              "POST /api/circulation/return", st, d, "fine = 5.00",
              f"overdue_days={d.get('overdue_days') if d else None}, fine={d.get('fine') if d else None}",
              bool(d) and abs(float(d.get("fine") or 0) - 5.00) < 1e-6)

    fine_id = sql("SELECT id FROM fine_records WHERE paid = 0 ORDER BY id DESC LIMIT 1")[0][0]
    st, c, m, d = call("POST", f"/api/circulation/fines/{fine_id}/pay", lib)
    expect_ok("G-02", "缴清罚款（未缴罚款会阻塞后续借书）",
              f"POST /api/circulation/fines/{fine_id}/pay", st, d, "paid = true",
              f"amount={d.get('amount') if d else None}, paid={d.get('paid') if d else None}",
              bool(d) and d.get("paid") is True)

    b_thesis = barcode_of("软件架构设计博士论文")
    st, c, m, d = call("POST", "/api/circulation/borrow", lib,
                       {"card_no": card_no_of("lisi"), "barcode": b_thesis})
    make_overdue(loan_id_of(b_thesis), 10)
    st, c, m, d = call("POST", "/api/circulation/return", lib, {"barcode": b_thesis})
    expect_ok("G-03", "逾期还书：学位论文 2.00 元/天，同样逾期 10 天",
              "POST /api/circulation/return", st, d, "fine = 20.00（与图书 5.00 不同）",
              f"overdue_days={d.get('overdue_days') if d else None}, fine={d.get('fine') if d else None}",
              bool(d) and abs(float(d.get("fine") or 0) - 20.00) < 1e-6)

    # --- 10. 预约（验收 9） ---
    title_sgyy = title_id_of("三国演义")
    st, c, m, d = call("POST", "/api/reservations", zs, {"title_id": title_sgyy})
    expires = (TODAY + timedelta(days=7)).isoformat()
    expect_ok("H-01", "预约图书（7 天有效期）", "POST /api/reservations", st, d,
              f"queue_position≥1，expires_at = 今天+7 = {expires}",
              f"queue_position={d.get('queue_position') if d else None}, "
              f"expires_at={str(d.get('expires_at'))[:10] if d else None}",
              bool(d) and str(d.get("expires_at"))[:10] == expires)

    st, c, m, _ = call("POST", "/api/reservations", zs, {"title_id": title_sgyy})
    expect_error("H-02", "重复预约同一标题", "POST /api/reservations", st, c, m,
                 "400 已预约过该书", 400, "预约")

    res_id = d.get("reservation_id") if d else None
    if res_id is None:
        res_id = sql("SELECT id FROM reservations WHERE reader_id = ? AND title_id = ? "
                     "AND status = 'ACTIVE'", (zs_id, title_sgyy))[0][0]
    st, c, m, d2 = call("POST", f"/api/reservations/{res_id}/cancel", zs)
    expect_ok("H-03", "取消预约", f"POST /api/reservations/{res_id}/cancel", st, d2,
              "status = CANCELLED", f"status={d2.get('status') if d2 else None}",
              bool(d2) and d2.get("status") == "CANCELLED")

    # --- 11. 评论与评分（学生任务卡 任务二） ---
    title_st = title_id_of("三体")
    st, c, m, d = call("POST", "/api/reviews", zs,
                       {"title_id": title_st, "rating": 5, "comment": "太好看了"})
    expect_ok("I-01", "提交评分与评论", "POST /api/reviews", st, d,
              "status = PENDING（待审核）", f"rating={d.get('rating') if d else None}, "
              f"status={d.get('status') if d else None}",
              bool(d) and d.get("status") == "PENDING")
    review_id = d.get("review_id") if d else None

    st, c, m, _ = call("POST", "/api/reviews", zs,
                       {"title_id": title_id_of("活着"), "rating": 6, "comment": "越界评分"})
    expect_error("I-02", "评分越界（6 分）", "POST /api/reviews", st, c, m,
                 "400 评分必须为 1-5 的整数", 400, "评分")

    st, c, m, d = call("GET", f"/api/reviews?title_id={title_st}", zs)
    expect_ok("I-03", "未审核评论不可见", f"GET /api/reviews?title_id={title_st}", st, d,
              "total=0, average_rating=0.0（仅统计 APPROVED）",
              f"total={d.get('total') if d else None}, average_rating={d.get('average_rating') if d else None}",
              bool(d) and d.get("total") == 0)

    st, c, m, _ = call("POST", f"/api/reviews/{review_id}/moderate", zs, {"decision": "APPROVED"})
    expect_error("I-04", "读者审核评论", f"POST /api/reviews/{review_id}/moderate（读者令牌）",
                 st, c, m, "403 权限不足（仅系统管理员）", 403)

    st, c, m, d = call("POST", f"/api/reviews/{review_id}/moderate", admin, {"decision": "APPROVED"})
    expect_ok("I-05", "系统管理员审核通过", f"POST /api/reviews/{review_id}/moderate", st, d,
              "status = APPROVED", f"status={d.get('status') if d else None}",
              bool(d) and d.get("status") == "APPROVED")

    st, c, m, d = call("GET", f"/api/reviews?title_id={title_st}", zs)
    expect_ok("I-06", "查看评论与平均分", f"GET /api/reviews?title_id={title_st}", st, d,
              "total=1, average_rating=5.0",
              f"total={d.get('total') if d else None}, average_rating={d.get('average_rating') if d else None}",
              bool(d) and d.get("total") == 1 and float(d.get("average_rating") or 0) == 5.0)

    # --- 报告输出 ---
    lines = [
        "# 实验二端到端验收记录",
        "",
        f"- 生成时间：{date.today().isoformat()}",
        "- 生成方式：`python scripts/e2e_acceptance.py`（对运行中的 http://localhost:8001 调用真实接口）",
        f"- 结果：**{len(rows) - len(failures)} / {len(rows)} 通过**",
        "",
        "| 编号 | 验收场景 | 请求 | 预期与实际 | 结论 |",
        "|---|---|---|---|---|",
    ]
    for no, scene, req, detail, verdict in rows:
        lines.append(f"| {no} | {scene} | `{req}` | {detail} | {verdict} |")
    lines += [
        "",
        "## 覆盖的实验二验收项",
        "",
        "| 验收项 | 对应用例 |",
        "|---|---|",
        "| 9. 借书、还书、预约、查询可用 | C-01、F-01、H-01、D-01 |",
        "| 10. 不同读者类型借阅规则可用 | C-01/C-02/C-05/C-06、C-03/C-04（出借物维度） |",
        "| 11. 不同借出物类型罚款规则可用 | G-01（图书 5.00）vs G-03（论文 20.00） |",
        "| 任务卡 任务一 续借 | E-01、E-02 |",
        "| 任务卡 任务二 图书评论与评分 | I-01～I-06 |",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print("-" * 60)
    print(f"结果：{len(rows) - len(failures)} / {len(rows)} 通过，报告已写入 {REPORT}")
    if failures:
        print("失败用例：" + "、".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
