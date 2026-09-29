# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Tống Trần Tiến Dũng  Mã học viên: 2A202602791

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Ví dụ deploy lên Railway nhưng quên cấu hình AGENT_API_KEY. Nếu agent_api_key không có giá trị mặc định, ứng dụng sẽ fail ngay khi khởi động. Railway phát hiện container không healthy và báo deploy lỗi, giúp tôi biết phải bổ sung secret trước khi đưa service lên public.
Nếu dùng mặc định "changeme", app vẫn khởi động bình thường. Khi đó attacker có thể đoán được key mặc định và gọi /ask miễn phí, làm phát sinh chi phí OpenAI hoặc khai thác dữ liệu hội thoại.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

`{"message":"","severity":"info","attributes":{"level":"info","event":"ask_completed","timestamp":"2026-09-29T15:19:51.764477+00:00","user_id":"sv-test","tokens_in":445,"tokens_out":45,"cost_usd":0.00009375}}`

Lọc và thống kê request bằng máy: tìm tất cả event ask_completed, lọc theo user_id, thời gian hoặc phát hiện request lỗi. Theo dõi token và chi phí: cộng tổng tokens_in, tokens_out, cost_usd để lập thống kê, cảnh báo khi user vượt ngân sách hoặc chi phí tăng bất thường.
---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 453MB |
| Multi-stage | 67.6 MB |

Dockerfile-1-stage: một stage, dùng python:3.11 đầy đủ, copy toàn bộ project.
Dockerfile: multi-stage builder/runtime, dùng python:3.11-slim, tận dụng cache dependency, image nhẹ hơn, chỉ copy phần cần thiết.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Được dùng lại từ cache:
- FROM python:3.11-slim
- WORKDIR, ENV
- COPY requirements.txt
- RUN pip install
- Runtime copy phần dependency /install

Phải build lại:
- COPY app ./app vì source đã thay đổi.
- Các layer đứng sau nó như COPY utils, tạo user và các layer runtime tiếp theo.
Lý do là Docker cache theo thứ tự layer. requirements.txt không đổi nên Docker không cài lại dependency.
Nếu đặt:
COPY . .
RUN pip install -r requirements.txt
thì chỉ cần sửa app/main.py, layer COPY . . bị thay đổi và RUN pip install cũng phải chạy lại. Build sẽ chậm hơn dù dependency không thay đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Lỗ hổng trong Python
→ attacker thực thi được code/command trong app
→ command chạy với quyền root trong container
→ đọc/sửa file hệ thống, cài công cụ, khai thác capability hoặc Docker socket
→ thoát container qua lỗi runtime/kernel hoặc cấu hình sai
→ có thể đạt quyền root trên máy host

Nếu Dockerfile có USER app thì process Uvicorn và code Python chạy bằng user thường app. Khi bị khai thác, attacker chỉ có quyền của app, không có quyền root trong container. Vì vậy chuỗi bị cắt ở bước 

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Có thể gửi tối đa 20 request trong khoảng 2 giây.

Cách thực hiện:
00:00:59 — gửi 10 request
00:01:00 — cửa sổ phút reset
00:01:01 — gửi tiếp 10 request

Hệ thống đếm theo phút đồng hồ coi chúng thuộc hai phút khác nhau, nên cả 20 request đều được chấp nhận dù thực tế xảy ra gần như liên tiếp.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Hai cơ chế giới hạn khác nhau:
- Rate limit: giới hạn số lần gọi trong một khoảng thời gian.
- Cost guard: giới hạn tổng chi phí đã sử dụng.

Tình huống rate limit cho qua nhưng cost guard chặn:
- User mới chỉ gửi 1 request trong phút này → chưa vượt 10 request/phút.
- Nhưng user đã tiêu 9.99 USD trong tháng,
- request mới dự kiến tốn 0.05 USD → vượt ngân sách.
Kết quả: rate limit cho qua, cost guard trả 402.

Tình huống rate limit chặn nhưng cost guard cho qua:
- User gửi 11 request trong cùng một phút → vượt 10 request/phút.
- Nhưng tổng chi phí tháng mới chỉ 0.01 USD → vẫn còn ngân sách.
Kết quả: rate limit trả 429, cost guard chưa cần chặn.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Thứ tự sự kiện:
1. Redis mất kết nối.
2. Cả 3 container gọi endpoint health chung, endpoint này cố kiểm tra Redis nên đều trả lỗi hoặc 503.
3. Orchestrator đánh dấu cả 3 container là unhealthy.
4. Orchestrator loại cả 3 khỏi traffic và restart chúng gần như cùng lúc.
5. Trong 30 giây Redis vẫn chưa sẵn sàng, các container mới tiếp tục healthcheck thất bại và có thể bị restart lặp lại.
6. Khi Redis hoạt động lại, cả 3 container cùng kết nối lại một lúc, tạo “thundering herd” và có thể tiếp tục gây quá tải.
Kết quả là một sự cố Redis ngắn biến thành sự cố toàn bộ cụm. Vì vậy /health chỉ kiểm tra process còn sống, còn /ready mới được phép kiểm tra Redis.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Nếu lưu history trong Redis, các container dùng chung dữ liệu nên response sẽ tăng đều, Nếu lưu trong một dict Python, mỗi container có một dict riêng. Khi request được phân phối sang container khác, container đó không biết history trước đó.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

- lỗi đầu tiên tôi gặp phải là: sai URL agent.
- thông báo lỗi: /bin/sh: 1: exec: docker-entrypoint.sh: not found
- kiểm tra bằng: `railway logs`, `railway domain` và nhận ra domain đang được tạo cho service redis, không phải service agent. Service Redis đang cố chạy sai lệnh khởi động docker-entrypoint.sh.
- sửa bằng cách:
+ giữ Redis là service database riêng của Railway;
+ bỏ cấu hình start command sai trên Redis;
+ tạo service agent riêng và build từ Dockerfile;
+ cấu hình REDIS_URL trên agent bằng biến reference:
- Sau đó deploy lại agent và kiểm tra:
health → 200
ready  → 200
---