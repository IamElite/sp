import base64
from typing import Optional


class PayloadCodec:
    PREFIX = "get-"

    @staticmethod
    def encode(message_id: int, channel_id: int) -> str:
        raw = f"{PayloadCodec.PREFIX}{message_id * abs(channel_id)}"
        b64 = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        return b64

    @staticmethod
    def decode(encoded: str, channel_id: int) -> Optional[dict]:
        try:
            padded = encoded + "=" * (-len(encoded) % 4)
            raw = base64.urlsafe_b64decode(padded.encode()).decode()
            if not raw.startswith(PayloadCodec.PREFIX):
                return None
            parts = raw[len(PayloadCodec.PREFIX):].split("-")
            abs_ch = abs(channel_id)
            msg_ids = [int(p) // abs_ch for p in parts]
            return {"message_ids": msg_ids, "channel_id": channel_id}
        except Exception:
            return None

    @staticmethod
    def encode_batch(message_ids: list[int], channel_id: int) -> str:
        ids = "-".join(str(mid * abs(channel_id)) for mid in message_ids)
        raw = f"{PayloadCodec.PREFIX}{ids}"
        b64 = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        return b64
