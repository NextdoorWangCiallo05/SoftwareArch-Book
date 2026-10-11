<#
  图书管理系统 · 一键运行脚本
  ------------------------------------------------------------------
  一条命令启动后端（:8001）与前端（:5173）：自动检查环境、安装依赖、
  等待健康检查通过；退出时一并停止由本脚本启动的进程。

  用法（在仓库根目录执行）：
    powershell -ExecutionPolicy Bypass -File run.ps1                  # 启动前后端
    powershell -ExecutionPolicy Bypass -File run.ps1 -Reset           # 先重置演示数据再启动
    powershell -ExecutionPolicy Bypass -File run.ps1 -BackendOnly     # 只启动后端（跑 pytest / 验收脚本）
    powershell -ExecutionPolicy Bypass -File run.ps1 -SkipInstall     # 跳过依赖安装（依赖已装好时更快）
    powershell -ExecutionPolicy Bypass -File run.ps1 -Open            # 启动后自动打开浏览器
    powershell -ExecutionPolicy Bypass -File run.ps1 -Detach          # 启动后脚本立即退出，服务留在后台
    powershell -ExecutionPolicy Bypass -File run.ps1 -Stop            # 停止后台残留的进程

  说明：
  - 后端默认幂等初始化（重复启动不清库）；-Reset 等价于 RESET_DB_ON_START=1。
  - 日志写入 logs/backend.log、logs/backend.err.log、logs/frontend.log、logs/frontend.err.log。
  - 前台运行时按 Ctrl+C 退出，脚本会停止本次启动的后端与前端进程。
#>
[CmdletBinding()]
param(
    [switch]$Reset,
    [switch]$BackendOnly,
    [switch]$SkipInstall,
    [switch]$Open,
    [switch]$Detach,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

$root        = $PSScriptRoot
$backendDir  = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$logDir      = Join-Path $root "logs"

$backendLog      = Join-Path $logDir "backend.log"
$backendErr      = Join-Path $logDir "backend.err.log"
$frontendLog     = Join-Path $logDir "frontend.log"
$frontendErr     = Join-Path $logDir "frontend.err.log"
$backendPidFile  = Join-Path $logDir "backend.pid"
$frontendPidFile = Join-Path $logDir "frontend.pid"

$apiBase = "http://127.0.0.1:8001"
$webBase = "http://127.0.0.1:5173"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

# ---------- 工具函数 ----------

function Get-UrlCode($url) {
    # 用 curl.exe 探测：避免 PS 5.1 的 Invoke-WebRequest 在 localhost/代理下的误判
    $code = & curl.exe -s -m 2 -o NUL -w "%{http_code}" $url 2>$null
    if ($LASTEXITCODE -ne 0) { return "000" }
    return ("$code").Trim()
}

function Wait-Url($url, $seconds) {
    for ($i = 0; $i -lt $seconds; $i++) {
        if ((Get-UrlCode $url) -eq "200") { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Stop-Tree($procId, $pidFile, $name) {
    if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
        & taskkill /PID $procId /T /F | Out-Null
        Write-Host "  $name 已停止（PID $procId）"
    } else {
        Write-Host "  $name 未在运行"
    }
    if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
}

function Stop-FromPidFile($pidFile, $name) {
    if (-not (Test-Path $pidFile)) { Write-Host "  $name ：没有由 run.ps1 启动的记录"; return }
    $saved = ("$(Get-Content $pidFile -First 1)").Trim()
    if ($saved -match '^\d+$') {
        Stop-Tree ([int]$saved) $pidFile $name
    } else {
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

function Assert-Command($name, $hint) {
    if (Get-Command $name -ErrorAction SilentlyContinue) { return }
    Write-Host "[x] 未找到命令 $name —— $hint" -ForegroundColor Red
    exit 1
}

# ---------- 0. -Stop：停止后台残留进程 ----------

if ($Stop) {
    Write-Host "=== 停止由 run.ps1 启动的服务 ==="
    Stop-FromPidFile $backendPidFile  "后端 (:8001)"
    Stop-FromPidFile $frontendPidFile "前端 (:5173)"
    Write-Host "完成。"
    exit 0
}

# ---------- 1. 运行环境 ----------

Write-Host "=== 图书管理系统 · 一键运行 ==="
Write-Host "[1/5] 检查运行环境"
Assert-Command "python" "请安装 Python 3.11+ 并加入 PATH（https://www.python.org/downloads/）"
Write-Host "      $(& python --version)"
if (-not $BackendOnly) {
    Assert-Command "npm" "请安装 Node.js 18+（自带 npm）并加入 PATH（https://nodejs.org/）"
    Write-Host "      node $(& node --version)"
}

# ---------- 2. 依赖 ----------

Write-Host "[2/5] 检查依赖"
if ($SkipInstall) {
    Write-Host "      已指定 -SkipInstall，跳过依赖安装"
} else {
    Write-Host "      后端：python -m pip install -r requirements.txt"
    & python -m pip install -q -r (Join-Path $backendDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[x] 后端依赖安装失败，请检查网络或手动执行 pip install -r backend/requirements.txt" -ForegroundColor Red
        exit 1
    }
    if (-not $BackendOnly) {
        if (Test-Path (Join-Path $frontendDir "node_modules")) {
            Write-Host "      前端：node_modules 已存在，跳过 npm install"
        } else {
            Write-Host "      前端：npm install（首次运行约 1 分钟）"
            Push-Location $frontendDir
            & npm install --no-audit --no-fund
            $frontendInstallOk = ($LASTEXITCODE -eq 0)
            Pop-Location
            if (-not $frontendInstallOk) {
                Write-Host "[x] 前端依赖安装失败，请手动执行 cd frontend; npm install" -ForegroundColor Red
                exit 1
            }
        }
    }
}

# ---------- 3. 后端 ----------

Write-Host "[3/5] 启动后端（端口 8001）"
$backendProc = $null
if ((Get-UrlCode "${apiBase}/api/health") -eq "200") {
    Write-Host "      检测到后端已在运行，复用现有服务（不重复启动）"
    if ($Reset) { Write-Host "      提示：-Reset 只对本次由脚本启动的后端生效，现有服务不会被重建" }
} else {
    $occupied = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
    if ($occupied) {
        $owners = ($occupied | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
        Write-Host "[x] 端口 8001 已被其他进程占用（PID：$owners）。" -ForegroundColor Red
        Write-Host "    可先执行：Stop-Process -Id $owners -Force；或设置环境变量 API_PORT 换端口启动。" -ForegroundColor Red
        exit 1
    }
    if ($Reset) {
        Write-Host "      -Reset：将删除并重建数据库，重新灌入种子数据"
        $env:RESET_DB_ON_START = "1"
    } else {
        Write-Host "      幂等初始化：保留现有数据（需要重置时加 -Reset）"
        $env:RESET_DB_ON_START = "0"
    }
    $backendProc = Start-Process -FilePath "python" -ArgumentList "main.py" `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput $backendLog -RedirectStandardError $backendErr `
        -PassThru -WindowStyle Hidden
    Set-Content -Path $backendPidFile -Value $backendProc.Id -Encoding ASCII

    if (-not (Wait-Url "${apiBase}/api/health" 40)) {
        Write-Host "[x] 后端启动失败，日志最后 20 行：" -ForegroundColor Red
        Get-Content $backendLog -Tail 20 -ErrorAction SilentlyContinue | Write-Host
        Get-Content $backendErr -Tail 20 -ErrorAction SilentlyContinue | Write-Host
        Stop-Tree $backendProc.Id $backendPidFile "后端"
        exit 1
    }
    Write-Host "      后端已就绪：$apiBase"
}

# ---------- 4. 前端 ----------

Write-Host "[4/5] 启动前端（端口 5173）"
$frontendProc = $null
if ($BackendOnly) {
    Write-Host "      已指定 -BackendOnly，跳过前端"
} elseif ((Get-UrlCode $webBase) -eq "200") {
    Write-Host "      检测到前端已在运行，复用现有服务（不重复启动）"
} else {
    # --host 127.0.0.1：显式绑定 IPv4，避免 Vite 默认只监听 ::1 导致健康检查与浏览器访问不一致
    $frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" `
        -WorkingDirectory $frontendDir `
        -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendErr `
        -PassThru -WindowStyle Hidden
    Set-Content -Path $frontendPidFile -Value $frontendProc.Id -Encoding ASCII

    if (-not (Wait-Url $webBase 30)) {
        Write-Host "[x] 前端启动失败，日志最后 20 行：" -ForegroundColor Red
        Get-Content $frontendLog -Tail 20 -ErrorAction SilentlyContinue | Write-Host
        Get-Content $frontendErr -Tail 20 -ErrorAction SilentlyContinue | Write-Host
        Stop-Tree $frontendProc.Id $frontendPidFile "前端"
        if ($backendProc) { Stop-Tree $backendProc.Id $backendPidFile "后端" }
        exit 1
    }
    Write-Host "      前端已就绪：$webBase"
}

# ---------- 5. 汇总 ----------

Write-Host ""
Write-Host "[5/5] 启动完成"
Write-Host "      前端界面   http://localhost:5173"
Write-Host "      后端 API   http://localhost:8001        接口文档 http://localhost:8001/docs"
Write-Host "      运行日志   logs\backend.log / logs\frontend.log（失败排查用）"
Write-Host "      演示账号   admin / admin123（系统管理员）"
Write-Host "                 lib01 / 123456（图书管理员）"
Write-Host "                 zhangsan / 123456（读者）"

if ($Open) { Start-Process $webBase }

if ($Detach -or (-not ($backendProc -or $frontendProc))) {
    Write-Host ""
    if ($Detach) {
        Write-Host "服务已在后台运行（-Detach），停止请执行：powershell -ExecutionPolicy Bypass -File run.ps1 -Stop"
    } else {
        Write-Host "前后端均复用既有进程，本脚本不再托管；停止请执行：run.ps1 -Stop"
    }
    exit 0
}

Write-Host ""
Write-Host "服务运行中，按 Ctrl+C 停止 ..." -ForegroundColor Cyan
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host ""
    Write-Host "正在停止服务 ..."
    if ($frontendProc) { Stop-Tree $frontendProc.Id $frontendPidFile "前端" }
    if ($backendProc) { Stop-Tree $backendProc.Id $backendPidFile "后端" }
}
