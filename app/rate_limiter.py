"""CP3 — Rate limiting bằng thuật toán sliding window.

Đếm số request trong 60 giây **gần nhất** (cửa sổ trượt), thay vì đếm theo
phút đồng hồ. Đếm theo phút đồng hồ có lỗ hổng: 10 request lúc 10:00:59 và
10 request lúc 10:01:01 = 20 request trong 2 giây mà vẫn "đúng luật".

Cấu trúc dữ liệu: Redis Sorted Set (ZSET), score = timestamp của request.
"""

from __future__ import annotations

import time
import uuid

from fastapi import HTTPException, status

WINDOW_SECONDS = 60


class RateLimiter:
    def __init__(self, client, limit_per_minute: int) -> None:
        self.client = client
        self.limit = limit_per_minute

    @staticmethod
    def _key(user_id: str) -> str:
        """CHO SẴN — mỗi user một key riêng."""
        return f"ratelimit:{user_id}"

    def hit_count(self, user_id: str, now: float | None = None) -> int:
        """Số request của user trong ``WINDOW_SECONDS`` giây gần nhất.

        TODO (CP3):
          1. ``now = now if now is not None else time.time()``
          2. Xóa các entry cũ hơn cửa sổ:
             ``self.client.zremrangebyscore(key, 0, now - WINDOW_SECONDS)``
          3. Trả về ``self.client.zcard(key)``
        """
        now = now if now is not None else time.time()
        key = self._key(user_id)
        self.client.zremrangebyscore(key, 0, now - WINDOW_SECONDS)
        return int(self.client.zcard(key))

    def check(self, user_id: str, now: float | None = None) -> None:
        """Cho qua nếu còn quota, ngược lại raise 429.

        TODO (CP3):
          1. ``now = now if now is not None else time.time()``
          2. Gọi ``self.hit_count(user_id, now)``.
          3. Nếu số đó ``>= self.limit`` → raise
             ``HTTPException(status_code=429, detail="rate limit exceeded",
                             headers={"Retry-After": str(WINDOW_SECONDS)})``
          4. Chưa vượt → ghi nhận request này:
             ``self.client.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})``
             (member phải là chuỗi DUY NHẤT, nếu không hai request cùng
             timestamp sẽ ghi đè nhau và bạn đếm thiếu)
             rồi ``self.client.expire(key, WINDOW_SECONDS)`` để key tự dọn.

        Lưu ý thứ tự: **kiểm tra trước, ghi nhận sau**. Ghi trước rồi mới đếm
        sẽ chặn nhầm ngay ở request thứ ``limit``.
        """
        now = now if now is not None else time.time()
        if self.hit_count(user_id, now) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

        key = self._key(user_id)
        member = f"{now}:{uuid.uuid4().hex}"
        self.client.zadd(key, {member: now})
        self.client.expire(key, WINDOW_SECONDS)


class TokenRateLimiter:
    """Giới hạn số token sử dụng trong 60 giây gần nhất của mỗi user.

    Mỗi lượt gọi được lưu trong Redis Sorted Set dưới dạng member có chứa số
    token. Nhờ vậy bộ đếm được dùng chung giữa nhiều container, thay vì mỗi
    process giữ một quota riêng trong RAM.
    """

    def __init__(self, client, limit_per_minute: int) -> None:
        self.client = client
        self.limit = limit_per_minute

    @staticmethod
    def _key(user_id: str) -> str:
        return f"tokenratelimit:{user_id}"

    def _prune(self, user_id: str, now: float) -> str:
        key = self._key(user_id)
        self.client.zremrangebyscore(key, 0, now - WINDOW_SECONDS)
        return key

    def used(self, user_id: str, now: float | None = None) -> int:
        """Tổng token đã ghi nhận trong cửa sổ trượt hiện tại."""
        now = now if now is not None else time.time()
        key = self._prune(user_id, now)
        total = 0
        for member in self.client.zrange(key, 0, -1):
            try:
                # Member có dạng: timestamp:token_count:uuid
                total += int(str(member).split(":", 2)[1])
            except (IndexError, TypeError, ValueError):
                # Bỏ qua dữ liệu hỏng thay vì làm endpoint /ask lỗi.
                continue
        return total

    def check(
        self,
        user_id: str,
        estimated_tokens: int,
        now: float | None = None,
    ) -> None:
        """Chặn request nếu ngân sách token trong phút sẽ bị vượt."""
        now = now if now is not None else time.time()
        if self.used(user_id, now) + max(0, estimated_tokens) > self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="token rate limit exceeded",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

    def record(
        self,
        user_id: str,
        tokens: int,
        now: float | None = None,
    ) -> int:
        """Ghi token thực tế của request và trả về tổng trong cửa sổ."""
        now = now if now is not None else time.time()
        tokens = max(0, int(tokens))
        if tokens:
            key = self._prune(user_id, now)
            member = f"{now}:{tokens}:{uuid.uuid4().hex}"
            self.client.zadd(key, {member: now})
            self.client.expire(key, WINDOW_SECONDS)
        return self.used(user_id, now)
