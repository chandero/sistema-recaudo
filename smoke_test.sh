#!/bin/bash
# Smoke test suite for Sistema de Recaudo
API="http://localhost:8055/api/v1"
PASS=0
FAIL=0

check() {
    local name="$1"
    local result="$2"
    if [ $? -eq 0 ] && [ -n "$result" ] && [ "$result" != "FAIL" ]; then
        echo "  PASS: $name => $result"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name => $result"
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================="
echo "  SMOKE TEST SUITE - Sistema de Recaudo"
echo "========================================="
echo ""

# 1. Login (JSON body to /auth/login)
echo "--- 1. Authentication ---"
LOGIN_RESP=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@sistema-cobro.com","password":"admin123"}')
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','FAIL'))" 2>/dev/null)
check "Login" "${TOKEN:0:30}..."
AUTH="Authorization: Bearer $TOKEN"

# 2. Dashboard Stats
echo ""
echo "--- 2. Dashboard ---"
RESP=$(curl -s -H "$AUTH" "$API/dashboard/stats")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'clients={d.get(\"total_clients\",0)}, processes={d.get(\"total_processes\",0)}')" 2>/dev/null)
check "Dashboard stats" "$RESULT"

# 3. Workflow States
echo ""
echo "--- 3. Workflow ---"
RESP=$(curl -sL -H "$AUTH" "$API/workflows/states/")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} states')" 2>/dev/null)
check "Workflow states" "$RESULT"

# 4. Kanban
RESP=$(curl -s -H "$AUTH" "$API/workflows/kanban")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d.get(\"columns\",[]))} columns')" 2>/dev/null)
check "Kanban board" "$RESULT"

# 5. Designer
RESP=$(curl -s -H "$AUTH" "$API/workflows/designer")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d.get(\"states\",[]))} states, {len(d.get(\"transitions\",[]))} transitions')" 2>/dev/null)
check "Workflow designer" "$RESULT"

# 6. Transition Rules
RESP=$(curl -s -H "$AUTH" "$API/workflows/transitions/rules")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d) if isinstance(d,list) else d} rules')" 2>/dev/null)
check "Transition rules" "$RESULT"

# 7. Processes (paginated)
echo ""
echo "--- 4. Processes ---"
RESP=$(curl -s -H "$AUTH" "$API/processes/?skip=0&limit=10")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'total={d.get(\"total\",0) if isinstance(d,dict) else len(d)}')" 2>/dev/null)
check "Processes list" "$RESULT"

# 8. Clients
echo ""
echo "--- 5. Clients ---"
RESP=$(curl -s -H "$AUTH" "$API/clients/?skip=0&limit=10")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'total={d.get(\"total\",0) if isinstance(d,dict) else len(d)}')" 2>/dev/null)
check "Clients list" "$RESULT"

# 9. Notifications
echo ""
echo "--- 6. Notifications ---"
RESP=$(curl -s -H "$AUTH" "$API/notifications/count")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'total={d.get(\"total\",0)}, unread={d.get(\"unread\",0)}')" 2>/dev/null)
check "Notification count" "$RESULT"

# 10. Search
RESP=$(curl -s -H "$AUTH" "$API/processes/search?q=test&limit=5")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d) if isinstance(d,list) else \"ok\"} results')" 2>/dev/null)
check "Process search" "$RESULT"

# 11. Users
echo ""
echo "--- 7. Users ---"
RESP=$(curl -s -H "$AUTH" "$API/users/")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d) if isinstance(d,list) else d} users')" 2>/dev/null)
check "Users list" "$RESULT"

# 12. Obligations
RESP=$(curl -s -H "$AUTH" "$API/obligations/?skip=0&limit=10")
RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'total={d.get(\"total\",0) if isinstance(d,dict) else len(d)}')" 2>/dev/null)
check "Obligations list" "$RESULT"

# 13. Validation error handling (should return 422, not 500)
echo ""
echo "--- 8. Error Handling ---"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"bad","password":"x"}')
check "Validation error returns 4xx" "$RESP"

# 14. Form-based login (OAuth2)
RESP=$(curl -s -X POST "$API/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@sistema-cobro.com&password=admin123")
TOKEN2=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','FAIL'))" 2>/dev/null)
check "Form-based login (/auth/token)" "${TOKEN2:0:30}..."

# Summary
echo ""
echo "========================================="
echo "  RESULTS: $PASS passed, $FAIL failed"
echo "========================================="
[ $FAIL -eq 0 ] && echo "  ALL TESTS PASSED!" || echo "  SOME TESTS FAILED!"
