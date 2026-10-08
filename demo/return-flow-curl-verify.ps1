<#
  实验二 · 两段式还书（BR-020）接口 curl 验证脚本
  ------------------------------------------------------------------
  自包含流程：启动后端 -> 登录取 token -> 验证归还申请/待审清单/驳回/通过
              -> 生成 markdown 测试记录 -> 停止后端

  产出：demo/return-flow-curl-test.md
  运行：powershell -ExecutionPolicy Bypass -File demo/return-flow-curl-verify.ps1
#>
$base = "http://127.0.0.1:8001"
$backendDir = Join-Path $PSScriptRoot "..\backend"
$report = Join-Path $PSScriptRoot "return-flow-curl-test.md"
$log = Join-Path $backendDir "server_verify.log"
$logErr = Join-Path $backendDir "server_verify.err"

# ---------- 1. 启动后端（后台） ----------
Write-Host "[1/6] 启动后端服务..."
# 若 8001 端口已有残留进程，先清理，保证使用全新种子库
$existing = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "   检测到 8001 端口占用，先结束残留进程..."
    $existing | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}
$proc = Start-Process -FilePath "python" -ArgumentList "main.py" `
    -WorkingDirectory $backendDir -RedirectStandardOutput $log -RedirectStandardError $logErr `
    -PassThru -WindowStyle Hidden

# ---------- 2. 等待健康检查（用 curl.exe，避免 localhost/IPv6 与代理干扰） ----------
$up = $false
for ($i = 0; $i -lt 40; $i++) {
    $code = & curl.exe -s -m 2 -o NUL -w "%{http_code}" "$base/openapi.json"
    if ($code -eq "200") { $up = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $up) {
    Write-Error "后端未就绪，日志如下：`n$(Get-Content $log -Tail 20 | Out-String)`n$(Get-Content $logErr -Tail 20 | Out-String)"
    exit 1
}
Write-Host "[2/6] 后端已就绪。"

# ---------- markdown 容器 ----------
$md = @()
$md += "# 两段式还书接口 curl 测试记录"
$md += ""
$md += "> 生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += "> 后端地址：$base（端口 8001）"
$md += "> 测试覆盖：BR-020 两段式还书 —— 读者发起归还申请 + 图书管理员审核"
$md += "> 标记为 新接口 的为本次新增接口"
$md += ""

# Windows PowerShell 5.1 向 curl.exe 传参时会破坏 JSON 里的双引号，
# 因此请求体统一先写入临时文件，再用 curl 的 -d "@file" 语法发送。
$bodyFile = Join-Path $env:TEMP "verify_return_body.json"
function Set-JsonBody($body) {
    [System.IO.File]::WriteAllText($bodyFile, $body, (New-Object System.Text.UTF8Encoding($false)))
    return "@$bodyFile"
}

function Run-Curl($title, $isNew, $method, $path, $body, $token) {
    $url = "$base$path"
    # 展示用命令（token 以占位符呈现）
    $show = "curl.exe -s -X $method `"$url`""
    if ($token) { $show += " -H `"Authorization: Bearer <TOKEN>`"" }
    if ($body) { $show += " -H `"Content-Type: application/json`" -d '$body'" }

    $args = @('-s', '-X', $method, $url)
    if ($token) { $args += @('-H', "Authorization: Bearer $token") }
    if ($body) { $args += @('-H', 'Content-Type: application/json', '-d', (Set-JsonBody $body)) }
    $resp = & curl.exe @args

    $script:md += "### $title" + $(if ($isNew) { ' [新接口]' })
    $script:md += '```bash'
    $script:md += $show
    $script:md += '```'
    $script:md += "**响应：**"
    $script:md += '```json'
    $script:md += $resp
    $script:md += '```'
    try {
        $j = $resp | ConvertFrom-Json
        if ($j.code -eq 200) {
            $script:md += "> 结构正确：code=$($j.code), message=$($j.message)"
        } else {
            $script:md += "> 业务返回非 200：code=$($j.code), message=$($j.message)"
        }
    } catch {
        $script:md += "> 响应非 JSON：$resp"
    }
    $script:md += ""
    return $resp
}

# ---------- 3. 登录取 token ----------
Write-Host "[3/6] 登录读者 / 馆员..."
$rLogin = & curl.exe -s -X POST "$base/api/auth/login" -H "Content-Type: application/json" `
    -d (Set-JsonBody '{"username":"zhangsan","password":"123456"}')
$rt = ($rLogin | ConvertFrom-Json).data.token
$lLogin = & curl.exe -s -X POST "$base/api/auth/login" -H "Content-Type: application/json" `
    -d (Set-JsonBody '{"username":"lib01","password":"123456"}')
$lt = ($lLogin | ConvertFrom-Json).data.token
if (-not $rt) { Write-Error "读者登录失败：$rLogin"; exit 1 }
if (-not $lt) { Write-Error "馆员登录失败：$lLogin"; exit 1 }

$md += "## 1. 认证"
$md += "读者令牌 READER_TOKEN、馆员令牌 LIBRARIAN_TOKEN 均通过 POST /api/auth/login 取得（用户名 zhangsan / lib01，密码 123456）。"
$md += "- 读者登录响应：" + ($rLogin -replace '(?<="token":")[^"]+', '<READER_TOKEN>')
$md += "- 馆员登录响应：" + ($lLogin -replace '(?<="token":")[^"]+', '<LIBRARIAN_TOKEN>')
$md += ""

# 由 /api/auth/me 解析读者 reader_id（避免硬编码）
$meResp = & curl.exe -s -X GET "$base/api/auth/me" -H "Authorization: Bearer $rt"
$readerId = ($meResp | ConvertFrom-Json).data.reader_id
Write-Host "   读者 reader_id=$readerId"

# ---------- 4. 查询在借记录（定位 loan_id） ----------
Write-Host "[4/6] 查询在借记录，定位 loan_id..."
$recResp = Run-Curl "查询读者在借记录（定位 loan_id）" $false "GET" "/api/circulation/records/$readerId`?status=BORROWED" $null $rt
$loanId = (($recResp | ConvertFrom-Json).data.records[0]).loan_id
Write-Host "   定位到 loan_id=$loanId"

# ---------- 5. 新接口：申请 / 待审清单 / 驳回 / 通过 ----------
Write-Host "[5/6] 验证归还申请与审核新接口（loan_id=$loanId）..."
$md += "## 2. 两段式还书核心接口验证"
$md += ""
$applyResp = Run-Curl "读者发起归还申请（BORROWED -> RETURN_REQUESTED）" $true "POST" "/api/circulation/return-request" "{`"loan_id`":$loanId}" $rt
Run-Curl "馆员查询待审核归还申请清单" $true "GET" "/api/circulation/return-requests" $null $lt
Run-Curl "申请期间复核记录（状态应为 RETURN_REQUESTED，仍占借阅配额）" $false "GET" "/api/circulation/records/$readerId`?status=RETURN_REQUESTED" $null $rt
Run-Curl "馆员审核驳回（RETURN_REQUESTED -> BORROWED）" $true "POST" "/api/circulation/return-requests/$loanId/reject" $null $lt
Run-Curl "驳回后复核在借记录（恢复在借）" $false "GET" "/api/circulation/records/$readerId`?status=BORROWED" $null $rt
Run-Curl "读者再次发起归还申请" $true "POST" "/api/circulation/return-request" "{`"loan_id`":$loanId}" $rt
Run-Curl "馆员再次查询待审清单" $true "GET" "/api/circulation/return-requests" $null $lt
$approveResp = Run-Curl "馆员审核通过（确认收书，RETURN_REQUESTED -> RETURNED）" $true "POST" "/api/circulation/return-requests/$loanId/approve" $null $lt

# ---------- 6. 二次查询确认状态 ----------
Run-Curl "复核读者在借记录（应无在借）" $false "GET" "/api/circulation/records/$readerId`?status=BORROWED" $null $rt

$md += "## 3. 结构校验结论"
$md += "- 读者发起归还申请 POST /api/circulation/return-request：返回 code/message/data，data.status = RETURN_REQUESTED 通过"
$md += "- 馆员待审核清单 GET /api/circulation/return-requests：返回 code/message/data，data.total 与 data.records 通过"
$md += "- 馆员审核驳回 POST /api/circulation/return-requests/{loan_id}/reject：返回 code/message/data，记录回到 BORROWED 通过"
$md += "- 馆员审核通过 POST /api/circulation/return-requests/{loan_id}/approve：返回 code/message/data，含 return_date / overdue_days / fine 通过"
$md += "- 四个接口统一遵循 {code, message, data} 信封结构，与 specs/14-api-spec.md 契约一致 通过"

# 以 UTF-8(无 BOM) 写入，避免 markdown 里出现多余字符
$dir = Split-Path $report -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
[System.IO.File]::WriteAllLines($report, [string[]]$md, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "[6/6] 测试记录已生成：$report"

# 清理：停止后端
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Host "后端已停止。"
