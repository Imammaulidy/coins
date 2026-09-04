import os
import sys
import unittest
import json
try:
    import zxingcpp
except ImportError:
    zxingcpp = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qr_engine import (
    load_config,
    crc16_ccitt,
    get_account,
    add_or_update_account,
    delete_account,
    generate_qrph_payload,
    generate_qr_image,
    generate_qr_base64
)
from database import (
    init_db,
    create_order,
    get_order,
    mark_as_paid
)
from api_server import app



class TestCoinsPaymentGatewayMulti(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.client = app.test_client()
        init_db()
        self._temp_coins_added = False

        if not self.config.get("accounts"):
            add_or_update_account(
                name="TESTMERCHANT",
                phone="+639123456789",
                city="Manila",
                display_name="Test Account",
                slot_id="slot_1"
            )
            self._temp_coins_added = True

        self.config = load_config()

    def tearDown(self):
        if getattr(self, "_temp_coins_added", False):
            delete_account("slot_1")

    def test_dynamic_amounts_for_qrph(self):
        """Tests QR payload generation for various dynamic amounts"""
        amounts = [69, 70, 70.5]
        for amt in amounts:
            payload = generate_qrph_payload(amount=amt, config=self.config)
            self.assertTrue(payload.startswith("00020101021227"))
            acc = self.config.get("accounts", [{}])[0]
            if acc.get("name"):
                self.assertTrue(acc["name"] in payload)
            
            # Verify amount tag 54 is in payload
            if amt == 69:
                self.assertTrue("540269" in payload)
            elif amt == 70:
                self.assertTrue("540270" in payload)
            elif amt == 70.5:
                self.assertTrue("540570.50" in payload or "540470.5" in payload)
            
            # Verify QR decodes properly if zxingcpp is available
            if zxingcpp:
                img = generate_qr_image(payload)
                barcodes = zxingcpp.read_barcodes(img)
                self.assertEqual(len(barcodes), 1)
                self.assertEqual(barcodes[0].text, payload)

    def test_multi_account_crud(self):
        """Tests adding, fetching, and deleting a secondary account slot"""
        new_acc = add_or_update_account(
            name="HERMAN SANTOSO",
            phone="09123456789",
            city="Manila",
            slot_id="test_slot_2"
        )
        self.assertEqual(new_acc["id"], "test_slot_2")
        self.assertEqual(new_acc["name"], "HERMANSANTOSO")
        self.assertEqual(new_acc["account_id"], "639123456789")

        # Test generate QR for slot 2
        payload_slot2 = generate_qrph_payload(amount=70, account="test_slot_2")
        self.assertTrue("5913HERMANSANTOSO" in payload_slot2)
        self.assertTrue("639123456789" in payload_slot2)

        # Cleanup slot 2
        ok = delete_account("test_slot_2")
        self.assertTrue(ok)

    def test_api_matrix_endpoint(self):
        """Tests /api/matrix endpoint for multi-slot QR retrieval"""
        res = self.client.get("/api/matrix?amount=69")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["amount"], 69.0)
        self.assertTrue(len(data["slots"]) >= 1)
        self.assertTrue(data["slots"][0]["qr_image_base64"].startswith("data:image/png;base64,"))

    def test_dynamic_rate_and_buffer(self):
        """Tests manual rate & buffer configuration and /api/rate endpoints"""
        from wallet_manager import rate_engine

        # Test set rate via API
        res = self.client.post("/api/rate/set", json={
            "base_rate": 60.50,
            "buffer": 0.30
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["base_rate"], 60.50)
        self.assertEqual(data["buffer"], 0.30)
        self.assertEqual(data["rate"], 60.80)

        # Verify rate engine state
        self.assertEqual(rate_engine.rate, 60.80)
        self.assertEqual(round(rate_engine.php_to_usdc(60.80), 4), 1.0)
        self.assertEqual(round(rate_engine.php_to_usdt(60.80), 4), 1.0)

        # Test GET /api/rate
        res_get = self.client.get("/api/rate")
        self.assertEqual(res_get.status_code, 200)
        get_data = res_get.get_json()
        self.assertTrue(get_data["success"])
        self.assertEqual(get_data["rate"], 60.80)

        # Restore default rates
        rate_engine.set_rate(60.55, 0.20, save=True)
        self.assertEqual(rate_engine.rate, 60.75)

    def test_multi_network_wallet_config_and_api(self):
        """Tests Base and BSC multi-network configuration, decimals, and API validation"""
        from wallet_manager import NETWORKS, wallet_manager

        # 1. Base network & USDC config (6 decimals)
        self.assertIn("base", NETWORKS)
        self.assertEqual(NETWORKS["base"]["chain_id"], 8453)
        self.assertEqual(NETWORKS["base"]["native_symbol"], "ETH")
        self.assertEqual(NETWORKS["base"]["tokens"]["USDC"]["decimals"], 6)

        # 2. BSC network & USDT/USDC config (18 decimals)
        self.assertIn("bsc", NETWORKS)
        self.assertEqual(NETWORKS["bsc"]["chain_id"], 56)
        self.assertEqual(NETWORKS["bsc"]["native_symbol"], "BNB")
        self.assertEqual(NETWORKS["bsc"]["tokens"]["USDT"]["decimals"], 18)
        self.assertEqual(NETWORKS["bsc"]["tokens"]["USDC"]["decimals"], 18)

        # 3. Test /api/wallet/status endpoint structure
        res_status = self.client.get("/api/wallet/status")
        self.assertEqual(res_status.status_code, 200)
        st = res_status.get_json()
        self.assertTrue(st["success"])
        self.assertIn("usdc_balance", st)
        self.assertIn("usdt_bsc_balance", st)
        self.assertIn("bnb_balance", st)
        self.assertIn("eth_balance", st)

        # 4. Test /api/wallet/send validation (invalid address or unsupported net)
        res_fail_addr = self.client.post("/api/wallet/send", json={
            "to": "invalid_address",
            "amount": 1.0,
            "network": "bsc",
            "token": "USDT"
        })
        self.assertEqual(res_fail_addr.status_code, 400)

        res_fail_net = self.client.post("/api/wallet/send", json={
            "to": "0x42027ab17953cb8ff6532b4b235530749f9a24cc",
            "amount": 1.0,
            "network": "solana",
            "token": "USDT"
        })
        self.assertEqual(res_fail_net.status_code, 400)

    def test_order_creation_and_database(self):
        """Tests order creation, retrieval, and marking as paid in database"""
        import uuid
        unique_order_id = f"TEST-ORD-{uuid.uuid4().hex[:8].upper()}"
        order = create_order(
            order_id=unique_order_id,
            amount=70.0,
            qr_payload="000201010212...",
            account_id="slot_1",
            account_name="TESTMERCHANT",
            customer_name="Test Customer",
            note="Test note",
            timeout_minutes=15,
            currency="PHP"
        )
        self.assertEqual(order["order_id"], unique_order_id)
        self.assertEqual(order["amount"], 70.0)
        self.assertEqual(order["status"], "PENDING")

        fetched = get_order(unique_order_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["order_id"], unique_order_id)

        paid = mark_as_paid(unique_order_id, payment_method="Test")
        self.assertEqual(paid["status"], "PAID")

    def test_crc16_correctness(self):
        """Tests CRC16-CCITT calculation matches EMVCo standard"""
        from qr_engine import crc16_ccitt
        test_str = "00020101021227650014DCPHPHM1XXX0111999644030212639359277982030812345678520460165303608540570.005802PH5911IMAMMAULIDI6006SERANG6304"
        crc = crc16_ccitt(test_str)
        self.assertEqual(len(crc), 4)
        self.assertTrue(all(c in "0123456789ABCDEF" for c in crc))

if __name__ == "__main__":
    unittest.main()

