"""
ADB Helper Module
-----------------
Modul untuk otomasi perintah ADB: Force stop, Clear Cache, Toggle Airplane Mode (Reset IP), dan Launch Multi App.

Mendukung mode operasi:
  - MODE PC    : ADB via USB (Windows/Linux/Mac). Otomatis mendeteksi device terhubung.
  - MODE TERMUX: ADB via TCP ke localhost:5555 atau Shizuku (rish) atau Root (su).
"""

import os
import sys
import subprocess
import asyncio
import logging
import html
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ADBHelper")

# ─────────────────────────────────────────────────────────────
# Deteksi Platform: apakah sedang berjalan di dalam Termux?
# ─────────────────────────────────────────────────────────────
def _is_termux() -> bool:
    """Kembalikan True jika proses berjalan di lingkungan Termux (Android)."""
    if os.environ.get("TERMUX_VERSION"):
        return True
    termux_prefix = "/data/data/com.termux/files/usr"
    if os.path.isdir(termux_prefix):
        return True
    try:
        with open("/proc/version", "r") as f:
            return "android" in f.read().lower()
    except Exception:
        return False

IS_TERMUX: bool = _is_termux()

def _has_root() -> bool:
    """Kembalikan True jika su tersedia dan dapat dieksekusi (device rooted)."""
    try:
        result = subprocess.run(["su", "-c", "id"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and "uid=0" in result.stdout
    except Exception:
        return False

CACHED_RISH_CMD: Optional[List[str]] = None

def _get_rish_cmd() -> Optional[List[str]]:
    """Cari binary rish yang valid untuk eksekusi Shizuku (Non-Root)"""
    global CACHED_RISH_CMD
    env = os.environ.copy()
    env["RISH_APPLICATION_ID"] = "com.termux"

    if CACHED_RISH_CMD:
        try:
            res = subprocess.run(CACHED_RISH_CMD + ["-c", "id"], capture_output=True, text=True, timeout=6, env=env)
            if "uid=" in (res.stdout or "") + (res.stderr or ""):
                return CACHED_RISH_CMD
        except Exception:
            pass

    candidates = [
        ["sh", "/data/data/com.termux/files/usr/bin/rish"],
        ["/data/data/com.termux/files/usr/bin/rish"],
        ["sh", "rish"],
        ["rish"]
    ]

    for base_cmd in candidates:
        try:
            res = subprocess.run(base_cmd + ["-c", "id"], capture_output=True, text=True, timeout=8, env=env)
            out = (res.stdout or "") + (res.stderr or "")
            logger.info(f"Test Shizuku {base_cmd} -> {out.strip()[:100]}")
            if "uid=" in out:
                CACHED_RISH_CMD = base_cmd
                return CACHED_RISH_CMD
        except Exception as e:
            logger.debug(f"Test Shizuku {base_cmd} error: {e}")
    return None

def _has_rish() -> bool:
    """Kembalikan True jika rish (Shizuku) tersedia dan aktif (Non-Root)."""
    return _get_rish_cmd() is not None


class ADBManager:

    @staticmethod
    def _run(cmd: List[str], timeout: int = 15, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Jalankan perintah shell dengan timeout. Capture stdout & stderr dengan aman."""
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        except FileNotFoundError:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=127,
                stdout="",
                stderr=f"Command '{cmd[0]}' tidak ditemukan di sistem (PATH)."
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=124,
                stdout="",
                stderr=f"Command '{' '.join(cmd)}' timed out after {timeout}s."
            )

    @classmethod
    def _run_adb(cls, args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
        """Jalankan perintah `adb [args]`."""
        return cls._run(["adb"] + args, timeout=timeout)

    @classmethod
    def _run_su(cls, shell_cmd: str, timeout: int = 15) -> subprocess.CompletedProcess:
        """Jalankan perintah shell via `su -c` (root). Hanya di Termux/Android."""
        return cls._run(["su", "-c", shell_cmd], timeout=timeout)

    @classmethod
    def _run_rish(cls, shell_cmd: str, timeout: int = 25) -> subprocess.CompletedProcess:
        """Jalankan perintah shell via `rish -c` (Shizuku Non-Root). Hanya di Termux/Android."""
        env = os.environ.copy()
        env["RISH_APPLICATION_ID"] = "com.termux"
        base_cmd = _get_rish_cmd() or ["sh", "/data/data/com.termux/files/usr/bin/rish"]
        return cls._run(base_cmd + ["-c", shell_cmd], timeout=timeout, env=env)

    @classmethod
    def _ensure_adb_tcp_connected(cls) -> Optional[str]:
        """Khusus Termux: cari device ADB yang sudah aktif atau hubungkan ke localhost:5555."""
        dev_chk = cls._run_adb(["devices"])
        lines = [l for l in dev_chk.stdout.strip().splitlines() if "\tdevice" in l]
        if lines:
            did = lines[0].split()[0]
            logger.info(f"ADB device aktif terdeteksi: {did}")
            return did

        try:
            cls._run_adb(["connect", "localhost:5555"], timeout=8)
        except Exception as e:
            logger.warning(f"Gagal connect localhost:5555: {e}")

        dev_chk2 = cls._run_adb(["devices"])
        lines2 = [l for l in dev_chk2.stdout.strip().splitlines() if "\tdevice" in l]
        if lines2:
            did = lines2[0].split()[0]
            logger.info(f"ADB TCP terhubung ke: {did}")
            return did

        return None

    @classmethod
    async def reset_multi_app(cls) -> Dict[str, Any]:
        """
        Eksekusi 5 tahap reset Multi App dan jaringan:
        1. Force stop app & sub-process
        2. Hapus cache
        3. Airplane mode ON (reset IP)
        4. Airplane mode OFF (koneksi baru)
        5. Buka kembali Multi App
        """
        loop = asyncio.get_running_loop()

        def _execute():
            mode = "TERMUX" if IS_TERMUX else "PC"
            logger.info(f"ADB mode: {mode}")

            device_id: Optional[str] = None
            has_root = IS_TERMUX and _has_root()
            has_rish = IS_TERMUX and (not has_root) and _has_rish()

            if IS_TERMUX:
                logger.info(f"Root: {has_root} | Shizuku (rish): {has_rish}")

            if IS_TERMUX:
                if has_root:
                    device_id = "localhost (Root / su)"
                    mode = "ROOT"
                elif has_rish:
                    device_id = "localhost (Shizuku / rish)"
                    mode = "SHIZUKU"
                else:
                    mode = "WIRELESS_ADB"
                    device_id = cls._ensure_adb_tcp_connected()
                    if not device_id:
                        rish_diag = ""
                        try:
                            env = os.environ.copy()
                            env["RISH_APPLICATION_ID"] = "com.termux"
                            res = subprocess.run(["sh", "/data/data/com.termux/files/usr/bin/rish", "-c", "id"], capture_output=True, text=True, timeout=5, env=env)
                            rish_diag = (res.stdout or "") + (res.stderr or "")
                        except Exception as e:
                            rish_diag = str(e)

                        return {
                            "success": False,
                            "error": (
                                "❌ <b>Koneksi ADB / Shizuku Terputus!</b>\n"
                                "━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🔍 <b>Status Shizuku:</b> <code>{html.escape(rish_diag.strip()[:100]) or 'Service terhenti / timeout'}</code>\n\n"
                                "💡 <b>Solusi:</b>\n"
                                "1. <b>Opsi Pengembang:</b> Aktifkan <code>Nonaktifkan batas waktu otorisasi ADB</code>.\n"
                                "2. <b>Shizuku:</b> Pastikan service Shizuku sedang berjalan.\n"
                                "3. Jalankan menu setup Termux untuk pairing ulang."
                            )
                        }
            else:
                mode = "PC"
                dev_chk = cls._run_adb(["devices"])
                lines = [l for l in dev_chk.stdout.strip().splitlines() if "\tdevice" in l]
                if not lines:
                    return {
                        "success": False,
                        "error": "Tidak ada perangkat Android terhubung via USB ADB. Pastikan USB Debugging aktif."
                    }
                device_id = lines[0].split()[0]

            logger.info(f"Target execution: {device_id} (Mode: {mode})")
            package_name = "com.waxmoon.ma.gp"

            shell_script = (
                f"am force-stop {package_name}; "
                f"am force-stop {package_name}:core; "
                f"am force-stop {package_name}:clone; "
                f"rm -rf /sdcard/Android/data/{package_name}/cache/*; "
                f"rm -rf /data/data/{package_name}/cache/*; "
                f"rm -rf /data/data/{package_name}/code_cache/*; "
                f"cmd connectivity airplane-mode enable; "
                f"settings put global airplane_mode_on 1; "
                f"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true; "
                f"sleep 2; "
                f"cmd connectivity airplane-mode disable; "
                f"settings put global airplane_mode_on 0; "
                f"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false; "
                f"sleep 2; "
                f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
            )

            logger.info(f"Menjalankan rangkaian reset atomic via {mode}...")
            if has_root:
                cls._run_su(shell_script, timeout=25)
            elif has_rish:
                cls._run_rish(shell_script, timeout=25)
            else:
                cls._run_adb(["shell", shell_script], timeout=25)

            logger.info("Rangkaian reset Multi App & Jaringan selesai dieksekusi")

            return {
                "success": True,
                "device_id": device_id,
                "package": package_name,
                "mode": mode,
                "root": has_root,
                "rish": has_rish
            }

        try:
            return await loop.run_in_executor(None, _execute)
        except Exception as e:
            logger.error(f"Error executing ADB reset: {e}")
            return {"success": False, "error": str(e)}
