#!/usr/bin/env bash
# 图书管理系统 · 一键运行（Linux / macOS，与 run.ps1 行为等价）
# 用法：./run.sh [-r|--reset] [--backend-only] [--skip-install] [--open] [--detach] [--stop]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BD="$ROOT/backend"
FD="$ROOT/frontend"
LD="$ROOT/logs"
BL="$LD/backend.log";  BE="$LD/backend.err.log"
FL="$LD/frontend.log"; FE="$LD/frontend.err.log"
BP="$LD/backend.pid";  FP="$LD/frontend.pid"
API="http://127.0.0.1:8001"
WEB="http://127.0.0.1:5173"

RESET=0; BONLY=0; SKIP=0; OPEN=0; DETACH=0; STOP=0

while [ $# -gt 0 ]; do
    case "$1" in
        -r|--reset|-Reset)            RESET=1 ;;
        --backend-only|-BackendOnly)  BONLY=1 ;;
        --skip-install|-SkipInstall)  SKIP=1 ;;
        --open|-Open)                 OPEN=1 ;;
        --detach|-Detach)             DETACH=1 ;;
        --stop|-Stop)                 STOP=1 ;;
        -h|--help|-Help)              sed -n '2,3p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) printf '[x] 未知参数：%s（用 --help 查看用法）\n' "$1" >&2; exit 2 ;;
    esac
    shift
done

http_code() {
    local c
    c="$(curl -s -m 2 -o /dev/null -w '%{http_code}' "$1" 2>/dev/null)"
    printf '%s' "${c:-000}"
}

wait_url() {
    local i=0
    while [ "$i" -lt "$2" ]; do
        [ "$(http_code "$1")" = "200" ] && return 0
        sleep 1; i=$((i + 1))
    done
    return 1
}

port_busy() {
    if command -v ss >/dev/null 2>&1; then
        ss -ltnH "sport = :$1" 2>/dev/null | grep -q .
    else
        (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
    fi
}

kill_tree() {
    local c
    for c in $(pgrep -P "$1" 2>/dev/null); do kill_tree "$c"; done
    kill -TERM "$1" 2>/dev/null || true
}

stop_tree() {
    local pid="$1" name="$2" file="$3" i=0
    if ! kill -0 "$pid" 2>/dev/null; then
        printf '  %s 未在运行（清理记录）\n' "$name"; rm -f "$file"; return 0
    fi
    kill_tree "$pid"
    while [ "$i" -lt 15 ] && kill -0 "$pid" 2>/dev/null; do sleep 0.2; i=$((i + 1)); done
    kill -KILL "$pid" 2>/dev/null || true
    printf '  %s 已停止（PID %s）\n' "$name" "$pid"; rm -f "$file"
}

stop_from_file() {
    local pid=""
    if [ ! -f "$1" ]; then printf '  %s ：没有由 run.sh 启动的记录\n' "$2"; return 0; fi
    pid="$(head -n 1 "$1" | tr -dc '0-9')"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        stop_tree "$pid" "$2" "$1"
    else
        printf '  %s 未在运行（清理记录）\n' "$2"; rm -f "$1"
    fi
}

mkdir -p "$LD"

if [ "$STOP" -eq 1 ]; then
    printf '=== 停止由 run.sh 启动的服务 ===\n'
    stop_from_file "$BP" "后端 (:8001)"
    stop_from_file "$FP" "前端 (:5173)"
    printf '完成。\n'; exit 0
fi

printf '=== 图书管理系统 · 一键运行 ===\n'
printf '[1/5] 检查运行环境\n'

command -v curl >/dev/null 2>&1 || { printf '[x] 未找到 curl，请先安装：sudo apt install curl\n' >&2; exit 1; }

if [ -x "$BD/.venv/bin/python" ]; then
    PY="$BD/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PY="$(command -v python)"
else
    printf '[x] 未找到 python3，请先安装：sudo apt install python3 python3-venv python3-pip\n' >&2
    exit 1
fi
printf '      %s\n' "$("$PY" --version 2>&1)"

if [ "$BONLY" -eq 0 ]; then
    command -v npm >/dev/null 2>&1 || { printf '[x] 未找到 npm，请安装 Node.js 18+：sudo apt install nodejs npm\n' >&2; exit 1; }
    printf '      node %s\n' "$(node --version 2>&1)"
fi

printf '[2/5] 检查依赖\n'
if [ "$SKIP" -eq 1 ]; then
    printf '      已指定 --skip-install，跳过依赖安装\n'
else
    printf '      后端：%s -m pip install -r requirements.txt\n' "$PY"
    if ! "$PY" -m pip install -q -r "$BD/requirements.txt"; then
        if [ "$PY" = "$BD/.venv/bin/python" ]; then
            printf '[x] 后端依赖安装失败，请检查网络后手动执行：%s -m pip install -r backend/requirements.txt\n' "$PY" >&2
            exit 1
        fi
        printf '      系统 Python 拒绝直接安装（PEP 668），改用虚拟环境 backend/.venv\n'
        "$PY" -m venv "$BD/.venv" || { printf '[x] 创建虚拟环境失败，请先执行：sudo apt install python3-venv\n' >&2; exit 1; }
        PY="$BD/.venv/bin/python"
        "$PY" -m pip install -q -r "$BD/requirements.txt" || {
            printf '[x] 后端依赖安装失败，请检查网络后手动执行：%s -m pip install -r backend/requirements.txt\n' "$PY" >&2
            exit 1
        }
    fi
    if [ "$BONLY" -eq 0 ]; then
        if [ -d "$FD/node_modules" ]; then
            printf '      前端：node_modules 已存在，跳过 npm install\n'
        else
            printf '      前端：npm install（首次运行约 1 分钟）\n'
            (cd "$FD" && npm install --no-audit --no-fund) || {
                printf '[x] 前端依赖安装失败，请手动执行：cd frontend && npm install\n' >&2
                exit 1
            }
        fi
    fi
fi

printf '[3/5] 启动后端（端口 8001）\n'
B_STARTED=0
if [ "$(http_code "$API/api/health")" = "200" ]; then
    printf '      检测到后端已在运行，复用现有服务（不重复启动）\n'
    [ "$RESET" -eq 1 ] && printf '      提示：--reset 只对本次由脚本启动的后端生效，现有服务不会被重建\n'
else
    if port_busy 8001; then
        printf '[x] 端口 8001 已被其他进程占用。可先执行：ss -ltnp | grep 8001，或用 API_PORT 换端口启动。\n' >&2
        exit 1
    fi
    if [ "$RESET" -eq 1 ]; then
        printf '      --reset：将删除并重建数据库，重新灌入种子数据\n'
        export RESET_DB_ON_START=1
    else
        printf '      幂等初始化：保留现有数据（需要重置时加 --reset）\n'
        export RESET_DB_ON_START=0
    fi
    ( cd "$BD"; nohup "$PY" main.py >>"$BL" 2>>"$BE" </dev/null & echo $! > "$BP" )
    B_PID="$(head -n 1 "$BP")"
    B_STARTED=1
    if ! wait_url "$API/api/health" 40; then
        printf '[x] 后端启动失败，日志最后 20 行：\n'
        tail -n 20 "$BL" 2>/dev/null
        tail -n 20 "$BE" 2>/dev/null
        stop_tree "$B_PID" "后端" "$BP"
        exit 1
    fi
    printf '      后端已就绪：%s\n' "$API"
fi

printf '[4/5] 启动前端（端口 5173）\n'
F_STARTED=0
if [ "$BONLY" -eq 1 ]; then
    printf '      已指定 --backend-only，跳过前端\n'
elif [ "$(http_code "$WEB")" = "200" ]; then
    printf '      检测到前端已在运行，复用现有服务（不重复启动）\n'
else
    ( cd "$FD"; nohup npm run dev -- --host 127.0.0.1 >>"$FL" 2>>"$FE" </dev/null & echo $! > "$FP" )
    F_PID="$(head -n 1 "$FP")"
    F_STARTED=1
    if ! wait_url "$WEB" 30; then
        printf '[x] 前端启动失败，日志最后 20 行：\n'
        tail -n 20 "$FL" 2>/dev/null
        tail -n 20 "$FE" 2>/dev/null
        stop_tree "$F_PID" "前端" "$FP"
        [ "$B_STARTED" -eq 1 ] && stop_tree "$B_PID" "后端" "$BP"
        exit 1
    fi
    printf '      前端已就绪：%s\n' "$WEB"
fi

printf '\n[5/5] 启动完成\n'
printf '      前端界面   %s\n' "$WEB"
printf '      后端 API   %s        接口文档 %s/docs\n' "$API" "$API"
printf '      运行日志   logs/backend.log / logs/frontend.log（失败排查用）\n'
printf '      演示账号   admin / admin123（系统管理员）\n'
printf '                 lib01 / 123456（图书管理员）\n'
printf '                 zhangsan / 123456（读者）\n'

if [ "$OPEN" -eq 1 ]; then
    (xdg-open "$WEB" >/dev/null 2>&1 || open "$WEB" >/dev/null 2>&1) || true
fi

if [ "$DETACH" -eq 1 ] || { [ "$B_STARTED" -eq 0 ] && [ "$F_STARTED" -eq 0 ]; }; then
    printf '\n'
    if [ "$DETACH" -eq 1 ]; then
        printf '服务已在后台运行（--detach），停止请执行：./run.sh --stop\n'
    else
        printf '前后端均复用既有进程，本脚本不再托管；停止请执行：./run.sh --stop\n'
    fi
    exit 0
fi

cleanup() {
    printf '\n正在停止服务 ...\n'
    [ "$F_STARTED" -eq 1 ] && stop_tree "$F_PID" "前端" "$FP"
    [ "$B_STARTED" -eq 1 ] && stop_tree "$B_PID" "后端" "$BP"
    exit 0
}
trap cleanup INT TERM

printf '\n服务运行中，按 Ctrl+C 停止 ...\n'
while :; do sleep 1; done
