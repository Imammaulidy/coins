import time
import threading
import re

try:
    import cv2
    import zxingcpp
    import numpy as np
    DESKTOP_CV_AVAILABLE = True
except ImportError:
    cv2 = None
    zxingcpp = None
    np = None
    DESKTOP_CV_AVAILABLE = False

class CameraScanner:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.lock = threading.Lock()
        self.current_frame_jpeg = None
        self.last_detected = None
        self.last_active_time = 0
        self.thread = None

    def start(self):
        if not DESKTOP_CV_AVAILABLE or not cv2:
            return False
        with self.lock:
            self.last_active_time = time.time()
            self.last_detected = None
            if self.is_running and self.cap and self.cap.isOpened():
                return True

            # Open camera 0
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                self.is_running = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.is_running = True

            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            return True

    def stop(self):
        with self.lock:
            self.is_running = False
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.current_frame_jpeg = None

    def _capture_loop(self):
        scan_interval = 0.1
        last_scan_time = 0

        while self.is_running:
            if not self.cap or not self.cap.isOpened():
                break

            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.02)
                continue

            now = time.time()
            if now - self.last_active_time > 90:
                break

            if now - last_scan_time > scan_interval:
                last_scan_time = now
                try:
                    res = zxingcpp.read_barcode(frame)
                    if res and res.text:
                        raw_text = res.text.strip()
                        m_addr = re.search(r'0x[a-fA-F0-9]{40}', raw_text)
                        m_pk = re.search(r'(?:0x)?[a-fA-F0-9]{64}', raw_text)

                        self.last_detected = {
                            'text': raw_text,
                            'address': m_addr.group(0) if m_addr else None,
                            'pk': m_pk.group(0) if m_pk else None,
                            'timestamp': now
                        }

                        if hasattr(res, 'position'):
                            pts = [(p.x, p.y) for p in res.position]
                            pts_np = np.array(pts, np.int32).reshape((-1, 1, 2))
                            cv2.polylines(frame, [pts_np], isClosed=True, color=(0, 255, 0), thickness=3)
                except Exception:
                    pass

            ret_enc, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
            if ret_enc:
                with self.lock:
                    self.current_frame_jpeg = jpeg.tobytes()

            time.sleep(0.03)

        self.stop()

    def get_frame(self):
        self.last_active_time = time.time()
        with self.lock:
            return self.current_frame_jpeg

    def get_status(self):
        self.last_active_time = time.time()
        with self.lock:
            det = self.last_detected
            if det:
                self.last_detected = None
            return {
                'active': self.is_running,
                'detected': det
            }

camera_scanner = CameraScanner()
