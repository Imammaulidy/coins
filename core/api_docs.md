# 📖 Dokumentasi REST API - Coins.ph Payment Gateway

Sistem API Payment Gateway ini memungkinkan Anda membuat QR Code pembayaran resmi standar nasional Filipina (**QR Ph / InstaPay**) dengan nominal berapa pun secara instan dan otomatis tanpa perlu membuka aplikasi Coins.ph di ponsel.

---

## 🚀 Base URL
```text
http://<IP-SERVER>:5000
```
*(Jika di-hosting di VPS atau Domain, ganti `<IP-SERVER>:5000` dengan domain/IP VPS Anda).*

---

## 1. Buat Invoice Pembayaran (Create Payment)

Endpoint untuk membuat transaksi baru dan mendapatkan QR Code Dynamic dengan nominal terkunci.

- **URL:** `/api/payment/create`
- **Method:** `POST`
- **Content-Type:** `application/json`

### Request Body
```json
{
  "amount": 70.00,
  "order_id": "ORDER-99881",
  "customer_name": "Budi Santoso",
  "customer_phone": "08123456789",
  "note": "Topup Koin 500 Pcs",
  "callback_url": "https://website-anda.com/api/webhook/coins",
  "timeout_minutes": 15
}
```

| Field | Tipe | Wajib | Keterangan |
| :--- | :--- | :--- | :--- |
| `amount` | Float / Number | **Ya** | Nominal dalam PHP (Peso Filipina), misal: `70.00` atau `150` |
| `order_id` | String | Tidak | ID unik pesanan Anda (jika kosong, diisi otomatis) |
| `customer_name` | String | Tidak | Nama pembeli / pelanggan |
| `customer_phone` | String | Tidak | Nomor HP pelanggan |
| `note` | String | Tidak | Catatan / nama produk / pesanan |
| `callback_url` | String | Tidak | URL webhook yang akan dipanggil saat pembayaran lunas |
| `timeout_minutes`| Integer | Tidak | Waktu kadaluarsa dalam menit (Default: `15`) |

### Response Sukses (200 OK)
```json
{
  "success": true,
  "order_id": "ORDER-99881",
  "amount": 70.0,
  "currency": "PHP",
  "status": "PENDING",
  "qr_payload": "00020101021227590012com.p2pqrpay0111DCPHPHM1XXX02089996440304126391700000005204601653036085402705802PH5911JUANDELACRUZ6006Manila62510012com.p2pqrpay0511ORDER-998810708123456786304XXXX",
  "qr_image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...",
  "qr_image_url": "http://<IP-SERVER>:5000/api/qr/image?order_id=ORDER-99881",
  "checkout_url": "http://<IP-SERVER>:5000/pay/ORDER-99881",
  "created_at": "2026-08-28 02:25:00",
  "expires_at": "2026-08-28 02:40:00"
}
```

---

## 2. Cek Status Pembayaran (Check Payment Status)

Endpoint untuk memeriksa status pembayaran invoice.

- **URL:** `/api/payment/<order_id>`
- **Method:** `GET`

### Contoh Response:
```json
{
  "success": true,
  "order": {
    "order_id": "ORDER-99881",
    "amount": 70.0,
    "currency": "PHP",
    "status": "PAID",
    "customer_name": "Budi Santoso",
    "note": "Topup Koin 500 Pcs",
    "created_at": "2026-08-28 02:25:00",
    "paid_at": "2026-08-28 02:26:15",
    "payment_method": "Coins.ph Auto-Notification (ADB)",
    "payer_info": "Cash In +₱70.00"
  }
}
```

---

## 3. Direct QR Image Generator

Dapatkan gambar QR PNG secara instan langsung dari URL tanpa perlu membuat order di database:

- **URL:** `/api/qr/image?amount=70`
- **Method:** `GET`
- **Content-Type:** `image/png`

Cocok langsung dimasukkan ke tag HTML:
```html
<img src="http://<IP-SERVER>:5000/api/qr/image?amount=70" alt="Scan to Pay ₱70" />
```

---

## 4. Webhook Callback (Notifikasi Otomatis)

Jika Anda menyertakan `callback_url` saat membuat payment, server akan otomatis mengirimkan HTTP POST payload berikut segera setelah dana masuk:

```json
{
  "event": "payment.success",
  "order_id": "ORDER-99881",
  "amount": 70.0,
  "currency": "PHP",
  "status": "PAID",
  "paid_at": "2026-08-28 02:26:15",
  "customer_name": "Budi Santoso",
  "note": "Topup Koin 500 Pcs",
  "payer_info": "Coins.ph QR Ph Transfer"
}
```

---

## 💻 Contoh Kode Integrasi

### Python
```python
import requests

url = "http://<IP-SERVER>:5000/api/payment/create"
payload = {
    "amount": 150.00,
    "customer_name": "John Doe",
    "note": "Order #5544"
}
res = requests.post(url, json=payload).json()
print("Link Pembayaran:", res["checkout_url"])
print("QR Base64:", res["qr_image_base64"])
```

### PHP / cURL
```php
<?php
$data = [
    'amount' => 70.00,
    'order_id' => 'INV-' . time(),
    'note' => 'Pembelian Layanan'
];

$ch = curl_init('http://<IP-SERVER>:5000/api/payment/create');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);

$response = json_decode(curl_exec($ch), true);
curl_close($ch);

echo "Buka link bayar: " . $response['checkout_url'];
?>
```

### JavaScript / Node.js (Fetch)
```javascript
const response = await fetch('http://<IP-SERVER>:5000/api/payment/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        amount: 250.00,
        customer_name: 'Alex'
    })
});
const data = await response.json();
console.log('Checkout URL:', data.checkout_url);
```
