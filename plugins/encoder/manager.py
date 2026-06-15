import asyncio
import os
import subprocess
from pathlib import Path
from typing import Optional

from config.settings import Config
from plugins.encoder.presets import get_preset
from utils.helpers import get_temp_path, cleanup_file
from utils.logger import setup_logger

logger = setup_logger("encoder_manager")


class EncodeJob:
    def __init__(self, input_path: Path, quality: str = "1080"):
        self.input_path = input_path
        self.quality = quality
        self.output_path: Optional[Path] = None
        self._process: Optional[asyncio.subprocess.Process] = None
        self._cancelled = False

    def _build_x264_params(self, cfg: dict) -> list[str]:
        parts = [
            f"ref={cfg.get('ref', 1)}",
            f"deblock={cfg.get('deblock', '1,0')}",
            f"me={cfg.get('me', 'hex')}",
            f"subme={cfg.get('subme', 2)}",
            f"trellis={cfg.get('trellis', 0)}",
            f"bframes={cfg.get('bframes', 3)}",
            f"b_pyramid={cfg.get('b_pyramid', 2)}",
            f"weightp={cfg.get('weightp', 1)}",
            f"keyint={cfg.get('keyint', 250)}",
            f"keyint_min={cfg.get('keyint_min', 23)}",
            f"scenecut={cfg.get('scenecut', 40)}",
            f"aq={cfg.get('aq', '1:1.00')}",
        ]

        if cfg.get("weightb", True):
            parts.append("weightb=1")
        if cfg.get("mbtree", True):
            parts.append("mbtree=1")
        else:
            parts.append("mbtree=0")

        if cfg.get("mixed_ref"):
            parts.append("mixed_ref=1")
        if cfg.get("chroma_qp_offset"):
            parts.append(f"chroma_qp_offset={cfg['chroma_qp_offset']}")
        if cfg.get("psy_rd"):
            parts.append(f"psy_rd={cfg['psy_rd']}")
        if cfg.get("analyse"):
            parts.append(f"analyse={cfg['analyse']}")

        return ["-x264-params", ":".join(parts)]

    def _build_ffmpeg_cmd(self, cfg: dict, pass_log: Optional[str] = None) -> list[str]:
        cmd = [
            "ffmpeg",
            "-i", str(self.input_path),
            "-map", "0",
            "-c:v", "libx264",
            "-preset", cfg.get("preset", "veryfast"),
        ]

        if cfg.get("mode") == "2pass":
            cmd.extend(["-b:v", cfg["bitrate"]])
            cmd.extend(["-maxrate", cfg["maxrate"]])
            cmd.extend(["-bufsize", cfg["bufsize"]])
            cmd.extend(["-pass", "1" if pass_log else "2"])
            if pass_log:
                cmd.extend(["-passlogfile", pass_log])
        else:
            cmd.extend(["-crf", str(cfg["crf"])])

        cmd.extend(self._build_x264_params(cfg))

        scale = cfg.get("scale")
        if scale:
            cmd.extend(["-vf", f"scale={scale}"])

        if cfg.get("audio_codec") == "libopus":
            cmd.extend([
                "-c:a", "libopus",
                "-b:a", cfg.get("audio_bitrate", "128k"),
                "-ar", str(cfg.get("audio_samplerate", 48000)),
            ])
        else:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", cfg.get("audio_bitrate", "128k"),
                "-ar", str(cfg.get("audio_samplerate", 44100)),
            ])

        cmd.extend(["-c:s", "copy", "-y"])

        return cmd

    async def run(self) -> Path:
        if not Config.ENCODING_ENABLED:
            logger.info("Encoding disabled, returning input as-is")
            return self.input_path

        cfg = get_preset(self.quality)
        self.output_path = get_temp_path(cfg.get("extension", ".mkv"))

        if cfg.get("mode") == "2pass":
            return await self._run_two_pass(cfg)
        return await self._run_single_pass(cfg)

    async def _run_single_pass(self, cfg: dict) -> Path:
        cmd = self._build_ffmpeg_cmd(cfg)
        cmd.append(str(self.output_path))

        logger.info(f"Encode: {self.input_path.name} → {self.output_path.name} [{self.quality}p]")

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = await self._process.communicate()

        if self._cancelled:
            raise asyncio.CancelledError("Encoding cancelled")
        if self._process.returncode != 0:
            error = stderr.decode(errors="ignore") if stderr else "ffmpeg error"
            logger.error(f"Encode failed: {error[:500]}")
            raise RuntimeError(f"Encoding failed for {self.input_path.name}")

        self._log_result()
        return self.output_path

    async def _run_two_pass(self, cfg: dict) -> Path:
        log_base = str(get_temp_path("_log"))
        passlog = log_base.replace("_log", "")

        for pass_num in (1, 2):
            is_first = pass_num == 1
            cmd = self._build_ffmpeg_cmd(cfg, pass_log=passlog if is_first else None)

            if is_first:
                null = "/dev/null"
                cmd.extend([null])
                logger.info(f"Pass 1: {self.input_path.name}")
            else:
                cmd.append(str(self.output_path))
                logger.info(f"Pass 2: {self.input_path.name} → {self.output_path.name}")

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = await self._process.communicate()

            if self._cancelled:
                raise asyncio.CancelledError("Encoding cancelled")
            if self._process.returncode != 0:
                error = stderr.decode(errors="ignore") if stderr else "ffmpeg error"
                logger.error(f"Pass {pass_num} failed: {error[:500]}")
                raise RuntimeError(f"2-pass pass {pass_num} failed")

        for f in Path(passlog).parent.glob(f"{Path(passlog).name}*"):
            cleanup_file(Path(f))

        self._log_result()
        return self.output_path

    def _log_result(self):
        in_size = self.input_path.stat().st_size
        out_size = self.output_path.stat().st_size
        ratio = (1 - out_size / in_size) * 100
        logger.info(f"Done: {self.output_path.name} | {in_size//1024**2}MB → {out_size//1024**2}MB ({ratio:.1f}% saved)")

    async def cancel(self):
        self._cancelled = True
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
