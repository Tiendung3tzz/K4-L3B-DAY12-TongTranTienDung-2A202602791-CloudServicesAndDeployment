# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị API key vào đây.**
> Repo này công khai — dán khóa vào là mất khóa.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Tống Trần Tiến Dũng |
| Mã học viên | 2A202602791 |
| Repo | https://github.com/Tiendung3tzz/K4-L3B-DAY12-TongTranTienDung-2A202602791-CloudServicesAndDeployment |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://agent-production-78bc.up.railway.app |
| Platform | Railway|
| Ngày deploy | 29/09/2026 |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | platform tự gán |
| `AGENT_API_KEY` | ✅ | đặt trong dashboard, không nằm trong repo |
| `REDIS_URL` | ✅ | Railway Redis add-on / Variable Reference |
| `RATE_LIMIT_PER_MINUTE` | ✅ | 4 |
| `MONTHLY_BUDGET_USD` | ✅ | 10.0 |
| `LOG_LEVEL` | ✅ | INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i <URL>/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Dán output của các lệnh trên vào đây:

```
1.
HTTP/1.1 200 OK
Content-Type: application/json
Date: Tue, 29 Sep 2026 15:03:05 GMT
Server: railway-hikari               
x-railway-request-id: zOK9MwTdRDycvEgL0_TJvA
Content-Length: 57                
x-hikari-trace: sin1.d1nj
x-railway-edge: sin1
Connection: keep-alive

{"status":"ok","service":"day12-agent","version":"1.0.0"}

2.
HTTP/1.1 200 OK
Content-Type: application/json
Date: Tue, 29 Sep 2026 15:04:00 GMT
Server: railway-hikari
x-railway-request-id: ghfgjbuyRIOtikfJY53eZw
Content-Length: 31
x-hikari-trace: sin1.nzn2
x-railway-edge: sin1
Connection: keep-alive

{"status":"ready","redis":true}

3.
HTTP/2 401 
content-type: application/json
date: Tue, 29 Sep 2026 15:07:01 GMT
server: railway-hikari
x-railway-request-id: kgBB6hKeRWCDrusF2h0iww
content-length: 39
x-hikari-trace: sin1.98a6
x-railway-edge: sin1

{"detail":"invalid or missing API key"}

4.
HTTP/2 200 
content-type: application/json
date: Tue, 29 Sep 2026 15:08:21 GMT
server: railway-hikari
x-railway-request-id: lMNGwiUCSPeT-fDEYqVb7A
content-length: 337
x-hikari-trace: sin1.d1nj
x-railway-edge: sin1
vary: accept-encoding

{"answer":"Câu hỏi hay. Deploy là gì thường được giải quyết bằng cách chuẩn hóa môi trường chạy: cùng một image chạy giống nhau ở laptop và trên cloud. (Mình đang nhớ 2 lượt trao đổi trước đó.)","user_id":"sv-test","history_length":2,"cost_usd":3.285e-05,"tokens":{"in":39,"out":45}}

5.
200 200 200 200 429 429 429 429 429 429 429 429 429 429 429 
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên platform
- `screenshots/health.png` — kết quả gọi `/health` từ trình duyệt hoặc curl

---

## Nếu Dùng Phương Án Dự Phòng

Không đăng ký được tài khoản cloud? Vẫn nộp được bài, nhưng CP5 tối đa 60% điểm:

1. Đặt `LOCAL_FALLBACK=true` trong `.env`
2. Chạy `docker compose up -d` rồi kiểm tra `docker compose ps`
3. Chụp màn hình vào `screenshots/`
4. Chạy `pytest tests/test_cp5.py -v` — bộ test sẽ tự chuyển sang kiểm tra
   `http://localhost:8000`
5. Ghi rõ lý do không deploy được vào phần dưới đây:

