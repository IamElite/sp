from typing import Optional

from plugins.fileshare.encoder import PayloadCodec


class LinkBuilder:
    @staticmethod
    def build_share_link(
        bot_username: str,
        message_id: int,
        channel_id: int,
    ) -> str:
        encoded = PayloadCodec.encode(message_id, channel_id)
        return f"https://t.me/{bot_username}?start={encoded}"

    @staticmethod
    def build_batch_link(
        bot_username: str,
        message_ids: list[int],
        channel_id: int,
    ) -> str:
        encoded = PayloadCodec.encode_batch(message_ids, channel_id)
        return f"https://t.me/{bot_username}?start={encoded}"

    @staticmethod
    def parse_start_param(text: str) -> Optional[str]:
        parts = text.split()
        if len(parts) > 1:
            return parts[1]
        return None
