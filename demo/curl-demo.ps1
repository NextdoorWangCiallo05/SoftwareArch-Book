<#
  实验二 · 接口 curl 验证脚本（学生任务卡 第 5 节 第 2 条）
  ------------------------------------------------------------------
  验证两个任务挂接的新接口：
    任务一 续借 -> POST /api/circulation/renew
    任务二 评论 -> POST /api/reviews、GET /api/reviews、POST /api/reviews/{id}/moderate
  另验证 BR-020 两段式还书：读者发起归还申请 -> 馆员审核（通过/驳回）

  前置：先启动后端 python main.py（启动时重建库，保证种子数据干净）
  运行：powershell -ExecutionPolicy Bypass -File demo/curl-demo.ps1

  说明：下面展示的是标准 curl 命令（可直接在 bash / Git Bash / WSL 中执行）。
        在 Windows PowerShell 下，JSON 体里的双引号需写成 \"（脚本内已处理），
        故实际执行的参数与展示文本略有差异。
#>

$base = "http://localhost:8001"

function Step($title, $cmd) {
    Write-Host ""
    Write-Host "------------------------------------------------------------"
    Write-Host "# $title"
    Write-Host $cmd
}

function Body($json) {
    # PowerShell 传参给原生 curl.exe 时，JSON 内层双引号需转义
    return $json -replace '"', '\"'
}

# ---------- 0. 健康检查 ----------
Step "服务健康检查" @'
$ curl.exe -s http://localhost:8001/api/health
'@
curl.exe -s "$base/api/health"
Write-Host ""

# ---------- 1. 登录三名角色 ----------
Step "登录：图书管理员 lib01" @'
$ curl.exe -s -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"lib01","password":"123456"}'
'@
$lib = curl.exe -s -X POST "$base/api/auth/login" -H "Content-Type: application/json" `
    -d (Body '{"username":"lib01","password":"123456"}')
Write-Host $lib
$libToken = ($lib | ConvertFrom-Json).data.token

Step "登录：读者 zhangsan" @'
$ curl.exe -s -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"zhangsan","password":"123456"}'
'@
$zs = curl.exe -s -X POST "$base/api/auth/login" -H "Content-Type: application/json" `
    -d (Body '{"username":"zhangsan","password":"123456"}')
Write-Host $zs
$zsToken = ($zs | ConvertFrom-Json).data.token

Step "登录：系统管理员 admin" @'
$ curl.exe -s -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}'
'@
$ad = curl.exe -s -X POST "$base/api/auth/login" -H "Content-Type: application/json" `
    -d (Body '{"username":"admin","password":"admin123"}')
Write-Host $ad
$adToken = ($ad | ConvertFrom-Json).data.token

# ---------- 2. 解析当前身份（reader_id / card_no） ----------
Step "读者解析当前身份（拿 reader_id / card_no）" @'
$ curl.exe -s http://localhost:8001/api/auth/me \
    -H "Authorization: Bearer <reader-token>"
'@
curl.exe -s "$base/api/auth/me" -H "Authorization: Bearer $zsToken"
Write-Host ""

# ---------- 3. 借书（管理员代理） ----------
Step "管理员办理借书《三体》" @'
$ curl.exe -s -X POST http://localhost:8001/api/circulation/borrow \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <librarian-token>" \
    -d '{"card_no":"CARD2026000001","barcode":"ITEM2026000002"}'
'@
curl.exe -s -X POST "$base/api/circulation/borrow" -H "Content-Type: application/json" `
    -H "Authorization: Bearer $libToken" `
    -d (Body '{"card_no":"CARD2026000001","barcode":"ITEM2026000002"}')
Write-Host ""

# ---------- 4. 任务一：续借 ----------
Step "读者查询在借记录，取 loan_id" @'
$ curl.exe -s "http://localhost:8001/api/circulation/records/1?status=BORROWED" \
    -H "Authorization: Bearer <reader-token>"
'@
curl.exe -s "$base/api/circulation/records/1?status=BORROWED" -H "Authorization: Bearer $zsToken"
Write-Host ""

Step "【任务一】续借" @'
$ curl.exe -s -X POST http://localhost:8001/api/circulation/renew \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <reader-token>" \
    -d '{"loan_id":2}'
'@
curl.exe -s -X POST "$base/api/circulation/renew" -H "Content-Type: application/json" `
    -H "Authorization: Bearer $zsToken" -d (Body '{"loan_id":2}')
Write-Host ""

# ---------- 5. 任务二：评论与评分 ----------
Step "【任务二】提交评分与评论" @'
$ curl.exe -s -X POST http://localhost:8001/api/reviews \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <reader-token>" \
    -d '{"title_id":1,"rating":5,"comment":"太好看了"}'
'@
curl.exe -s -X POST "$base/api/reviews" -H "Content-Type: application/json" `
    -H "Authorization: Bearer $zsToken" -d (Body '{"title_id":1,"rating":5,"comment":"太好看了"}')
Write-Host ""

Step "查看评论（审核前，PENDING 不可见）" @'
$ curl.exe -s "http://localhost:8001/api/reviews?title_id=1" \
    -H "Authorization: Bearer <reader-token>"
'@
curl.exe -s "$base/api/reviews?title_id=1" -H "Authorization: Bearer $zsToken"
Write-Host ""

Step "系统管理员审核通过" @'
$ curl.exe -s -X POST http://localhost:8001/api/reviews/1/moderate \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin-token>" \
    -d '{"decision":"APPROVED"}'
'@
curl.exe -s -X POST "$base/api/reviews/1/moderate" -H "Content-Type: application/json" `
    -H "Authorization: Bearer $adToken" -d (Body '{"decision":"APPROVED"}')
Write-Host ""

Step "查看评论（审核后，进入平均分）" @'
$ curl.exe -s "http://localhost:8001/api/reviews?title_id=1" \
    -H "Authorization: Bearer <reader-token>"
'@
curl.exe -s "$base/api/reviews?title_id=1" -H "Authorization: Bearer $zsToken"
Write-Host ""

# ---------- 6. 归还：读者发起申请 + 馆员审核（BR-020 两段式） ----------
Step "读者查询在借记录，取 loan_id" @'
$ curl.exe -s "http://localhost:8001/api/circulation/records/1?status=BORROWED" \
    -H "Authorization: Bearer <reader-token>"
'@
curl.exe -s "$base/api/circulation/records/1?status=BORROWED" -H "Authorization: Bearer $zsToken"
Write-Host ""

Step "【BR-020】读者发起归还申请（BORROWED -> RETURN_REQUESTED）" @'
$ curl.exe -s -X POST http://localhost:8001/api/circulation/return-request \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <reader-token>" \
    -d '{"loan_id":2}'
'@
curl.exe -s -X POST "$base/api/circulation/return-request" -H "Content-Type: application/json" `
    -H "Authorization: Bearer $zsToken" -d (Body '{"loan_id":2}')
Write-Host ""

Step "馆员查看待审核归还申请清单" @'
$ curl.exe -s http://localhost:8001/api/circulation/return-requests \
    -H "Authorization: Bearer <librarian-token>"
'@
curl.exe -s "$base/api/circulation/return-requests" -H "Authorization: Bearer $libToken"
Write-Host ""

Step "【BR-020】馆员审核通过（确认收书，结算逾期罚款）" @'
$ curl.exe -s -X POST http://localhost:8001/api/circulation/return-requests/2/approve \
    -H "Authorization: Bearer <librarian-token>"
'@
curl.exe -s -X POST "$base/api/circulation/return-requests/2/approve" `
    -H "Authorization: Bearer $libToken"
Write-Host ""

Step "（备选）馆员驳回归还申请：POST /api/circulation/return-requests/{loan_id}/reject" @'
$ curl.exe -s -X POST http://localhost:8001/api/circulation/return-requests/1/reject \
    -H "Authorization: Bearer <librarian-token>"
'@
Write-Host "（读者未交书时使用；驳回后借阅记录退回 BORROWED）"
Write-Host ""

Write-Host "------------------------------------------------------------"
Write-Host "完成。"
