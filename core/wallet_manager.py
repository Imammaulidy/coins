"""
wallet_manager.py - Coins.ph Payment Gateway
Mengelola koneksi wallet multi-jaringan (Base Network & BSC / BEP-20)
serta pengiriman USDC (Base/BSC) dan USDT (BSC BEP-20).
"""
import os
import json
import time
import re
import threading
import requests
from typing import Optional, Tuple, Dict, Any, List

# ABI minimal untuk transfer Token ERC-20 / BEP-20
ERC20_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ============================================================
# DEFINISI MULTI-JARINGAN & KONTRAK TOKEN (Base & BSC)
# ============================================================
NETWORKS = {
    "base": {
        "name": "Base Network",
        "chain_id": 8453,
        "rpc_urls": [
            "https://mainnet.base.org",
            "https://base.llamarpc.com",
            "https://1rpc.io/base"
        ],
        "native_symbol": "ETH",
        "explorer_tx": "https://basescan.org/tx/{tx_hash}",
        "tokens": {
            "USDC": {
                "contract": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "decimals": 6,
                "symbol": "USDC",
                "name": "USD Coin (Base)"
            }
        }
    },
    "bsc": {
        "name": "BNB Smart Chain (BSC)",
        "chain_id": 56,
        "rpc_urls": [
            "https://bsc-dataseed.binance.org/",
            "https://binance.llamarpc.com",
            "https://bsc-dataseed1.defibit.io",
            "https://1rpc.io/bnb"
        ],
        "native_symbol": "BNB",
        "explorer_tx": "https://bscscan.com/tx/{tx_hash}",
        "tokens": {
            "USDT": {
                "contract": "0x55d398326f99059fF775485246999027B3197955",
                "decimals": 18,
                "symbol": "USDT",
                "name": "Tether USD (BEP-20)"
            },
            "USDC": {
                "contract": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
                "decimals": 18,
                "symbol": "USDC",
                "name": "USD Coin (BEP-20)"
            }
        }
    }
}

# Default dev seed phrase (Kosong untuk rilis/kosongan, diisi user via UI)
DEFAULT_DEV_SEED_PHRASE = ""


# ============================================================
# DYNAMIC RATE ENGINE (USDC/USDT - Konfigurasi Manual Dinamis)
# ============================================================

def _get_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

class RateEngine:
    """Manages dynamic USDC/USDT rates with manual base rate and safety buffer."""

    def __init__(self):
        self._base_rate: float = 60.55
        self._buffer: float = 0.20
        self._source: str = "Bitget Wallet (Dinamis)"
        self._last_updated: float = time.time()
        self._lock = threading.Lock()
        self._load_from_config()

    def _load_from_config(self):
        """Load custom base_rate and buffer from config.json if configured."""
        try:
            cfg_path = _get_config_path()
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rate_cfg = data.get("rates", {})
                if "base_rate" in rate_cfg:
                    self._base_rate = float(rate_cfg["base_rate"])
                if "buffer" in rate_cfg:
                    self._buffer = float(rate_cfg["buffer"])
        except Exception as e:
            print(f"[RateEngine] Notice: Using default rates ({e})")

    def set_rate(self, base_rate: float, buffer: float = 0.20, save: bool = True) -> Dict[str, Any]:
        """Update base rate and buffer dynamically, persisting to config.json."""
        with self._lock:
            self._base_rate = max(0.01, float(base_rate))
            self._buffer = max(0.0, float(buffer))
            self._last_updated = time.time()

        if save:
            try:
                cfg_path = _get_config_path()
                cfg_data = {}
                if os.path.exists(cfg_path):
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                if "rates" not in cfg_data:
                    cfg_data["rates"] = {}
                cfg_data["rates"]["base_rate"] = self._base_rate
                cfg_data["rates"]["buffer"] = self._buffer
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(cfg_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[RateEngine] Warning: Failed to persist rate to config: {e}")

        return self.get_info()

    def start(self):
        print(f"[RateEngine] Rate Aktif: {self.rate:.4f} PHP/USD (Base: {self._base_rate:.2f} + Buffer: {self._buffer:.2f})")

    def stop(self):
        pass

    @property
    def base_rate(self) -> float:
        with self._lock:
            return self._base_rate

    @property
    def buffer(self) -> float:
        with self._lock:
            return self._buffer

    @property
    def rate(self) -> float:
        """Effective rate = base_rate + buffer."""
        with self._lock:
            return round(self._base_rate + self._buffer, 4)

    @property
    def last_updated(self) -> float:
        return self._last_updated

    @property
    def source(self) -> str:
        return self._source

    def get_info(self) -> Dict[str, Any]:
        eff = self.rate
        with self._lock:
            base = self._base_rate
            buf = self._buffer
        return {
            "success": True,
            "rate": eff,
            "effective_rate": eff,
            "base_rate": base,
            "buffer": buf,
            "source": self._source,
            "last_updated_ago_sec": int(time.time() - self._last_updated),
            "last_updated_ts": self._last_updated,
            "formatted": f"{eff:.2f} PHP (Base: {base:.2f} + Buffer: {buf:.2f})"
        }

    def php_to_usdc(self, php_amount: float) -> float:
        """Convert PHP to USDC/USDT amount using effective display rate."""
        eff = self.rate
        if eff <= 0:
            return 0.0
        return round(php_amount / eff, 6)

    def php_to_usdt(self, php_amount: float) -> float:
        """Alias for USDT (equivalent 1:1 USD peg)."""
        return self.php_to_usdc(php_amount)

    def usdc_to_php(self, usdc_amount: float) -> float:
        """Convert USDC/USDT to PHP using effective display rate."""
        return round(usdc_amount * self.rate, 2)


# Global rate engine instance
rate_engine = RateEngine()


# ============================================================
# MULTI-NETWORK WALLET MANAGER (Base & BSC)
# ============================================================

class WalletManager:
    """
    Manages EVM wallet connections (PK or Seed Phrase) across
    multiple networks (Base & BNB Smart Chain / BSC).
    """

    def __init__(self):
        self._account = None
        self._address: Optional[str] = None
        self._connected = False
        self._lock = threading.Lock()
        self._pk = None
        self._w3_cache: Dict[str, Any] = {}
        self.load_from_config()
        self.auto_connect_default()

    def load_from_config(self) -> bool:
        """Load wallet configuration (PK, seed phrase, or address) from config.json."""
        try:
            cfg_path = _get_config_path()
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                w_cfg = data.get("wallet", {})
                if w_cfg.get("private_key"):
                    res = self.connect_private_key(w_cfg["private_key"], save=False)
                    return res.get("success", False)
                elif w_cfg.get("seed_phrase"):
                    res = self.connect_phrase(w_cfg["seed_phrase"], save=False)
                    return res.get("success", False)
                elif w_cfg.get("address"):
                    return self.set_address_readonly(w_cfg["address"], save=False).get("success", False)
        except Exception as e:
            print(f"[WalletManager] Load config notice: {e}")
        return False

    def set_address_readonly(self, address: str, save: bool = True) -> Dict[str, Any]:
        """Set watch-only address for checking balances without private key."""
        addr = address.strip()
        if not re.match(r"^0x[a-fA-F0-9]{40}$", addr):
            return {"success": False, "message": f"Format address EVM tidak valid: {addr}"}
        with self._lock:
            self._address = addr
            self._connected = True
            self._account = None
            self._pk = None

        if save:
            try:
                cfg_path = _get_config_path()
                cfg_data = {}
                if os.path.exists(cfg_path):
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                cfg_data.setdefault("wallet", {})["address"] = addr
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(cfg_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[WalletManager] Warning saving address to config: {e}")

        return {"success": True, "address": addr, "method": "read_only"}

    def auto_connect_default(self) -> Dict[str, Any]:
        """Auto-connect developer wallet if DEFAULT_DEV_SEED_PHRASE is set."""
        if DEFAULT_DEV_SEED_PHRASE and DEFAULT_DEV_SEED_PHRASE.strip():
            return self.connect_phrase(DEFAULT_DEV_SEED_PHRASE.strip())
        return {"success": False, "error": "No default seed phrase configured"}

    def _get_w3(self, network: str = "base"):
        """Get or initialize Web3 instance for specific network with RPC fallback."""
        try:
            from web3 import Web3
        except ImportError:
            return None

        net_key = network.lower().strip()
        if net_key not in NETWORKS:
            net_key = "base"

        with self._lock:
            if net_key in self._w3_cache:
                try:
                    if self._w3_cache[net_key].is_connected():
                        return self._w3_cache[net_key]
                except Exception:
                    pass

        net_info = NETWORKS[net_key]
        for rpc in net_info["rpc_urls"]:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
                if w3.is_connected():
                    with self._lock:
                        self._w3_cache[net_key] = w3
                    return w3
            except Exception:
                continue

        # If all fail, return first provider instance
        try:
            fallback_w3 = Web3(Web3.HTTPProvider(net_info["rpc_urls"][0], request_kwargs={"timeout": 8}))
            return fallback_w3
        except Exception:
            return None

    def connect_private_key(self, private_key: str) -> Dict[str, Any]:
        """Connect wallet using raw private key (works across all EVM networks)."""
        try:
            from eth_account import Account
            pk = private_key.strip()
            if not pk.startswith("0x"):
                pk = "0x" + pk

            account = Account.from_key(pk)
            with self._lock:
                self._account = account
                self._address = account.address
                self._connected = True
                self._pk = pk

            balances = self.get_balance()
            return {
                "success": True,
                "address": account.address,
                "address_short": f"{account.address[:6]}...{account.address[-4:]}",
                "method": "private_key",
                "balances": balances
            }
        except Exception as e:
            with self._lock:
                self._connected = False
            return {"success": False, "message": str(e)}

    def connect_phrase(self, phrase: str) -> Dict[str, Any]:
        """Connect wallet using BIP39 mnemonic seed phrase."""
        try:
            from eth_account import Account
            Account.enable_unaudited_hdwallet_features()

            words = phrase.strip().split()
            if len(words) not in [12, 24]:
                return {"success": False, "message": f"Seed phrase harus 12 atau 24 kata. Anda memasukkan {len(words)} kata."}

            account = Account.from_mnemonic(phrase.strip())
            with self._lock:
                self._account = account
                self._address = account.address
                self._connected = True
                self._pk = account.key.hex()

            balances = self.get_balance()
            return {
                "success": True,
                "address": account.address,
                "address_short": f"{account.address[:6]}...{account.address[-4:]}",
                "method": "seed_phrase",
                "balances": balances
            }
        except Exception as e:
            with self._lock:
                self._connected = False
            return {"success": False, "message": str(e)}

    def disconnect(self):
        with self._lock:
            self._account = None
            self._address = None
            self._connected = False
            self._pk = None
            self._w3_cache.clear()

    def get_balance(self, network: Optional[str] = None) -> Dict[str, Any]:
        """
        Query balances across Base and BSC networks.
        Returns structured multi-network balances.
        """
        with self._lock:
            if not self._connected or not self._address:
                return {"success": False, "message": "Wallet belum terkoneksi."}
            address = self._address

        result = {
            "success": True,
            "address": address,
            "address_short": f"{address[:6]}...{address[-4:]}",
            "networks": {}
        }

        # Determine networks to query
        targets = [network.lower()] if network and network.lower() in NETWORKS else ["base", "bsc"]

        for net_key in targets:
            net_info = NETWORKS[net_key]
            w3 = self._get_w3(net_key)
            net_data = {
                "name": net_info["name"],
                "chain_id": net_info["chain_id"],
                "native_symbol": net_info["native_symbol"],
                "native_balance": 0.0,
                "tokens": {}
            }

            # 1. Native Gas Balance (ETH on Base, BNB on BSC)
            if w3:
                try:
                    native_wei = w3.eth.get_balance(w3.to_checksum_address(address))
                    net_data["native_balance"] = round(float(w3.from_wei(native_wei, "ether")), 6)
                except Exception as e:
                    print(f"[WalletManager] Error fetching {net_info['native_symbol']} balance via Web3: {e}")
            else:
                # Direct JSON-RPC via requests fallback
                for rpc in net_info["rpc_urls"]:
                    try:
                        r = requests.post(rpc, json={"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}, timeout=6)
                        if r.status_code == 200:
                            hex_bal = r.json().get("result", "0x0")
                            net_data["native_balance"] = round(int(hex_bal, 16) / 1e18, 6)
                            break
                    except Exception:
                        continue

            # 2. Token Balances (USDC, USDT)
            for tok_key, tok_info in net_info["tokens"].items():
                dec = tok_info["decimals"]
                token_bal = 0.0
                tok_contract = tok_info["contract"]

                if w3:
                    try:
                        contract = w3.eth.contract(
                            address=w3.to_checksum_address(tok_contract),
                            abi=ERC20_ABI
                        )
                        raw_bal = contract.functions.balanceOf(w3.to_checksum_address(address)).call()
                        token_bal = round(raw_bal / (10 ** dec), 6)
                    except Exception as e:
                        print(f"[WalletManager] Error fetching {tok_key} on {net_key} via Web3: {e}")
                else:
                    # Direct JSON-RPC eth_call via requests
                    try:
                        addr_clean = address.lower().replace("0x", "").zfill(64)
                        call_data = "0x70a08231" + addr_clean
                        for rpc in net_info["rpc_urls"]:
                            try:
                                r = requests.post(rpc, json={"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": tok_contract, "data": call_data}, "latest"], "id": 1}, timeout=6)
                                if r.status_code == 200:
                                    hex_val = r.json().get("result", "0x0")
                                    token_bal = round(int(hex_val, 16) / (10 ** dec), 6)
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

                net_data["tokens"][tok_key] = {
                    "symbol": tok_info["symbol"],
                    "name": tok_info["name"],
                    "balance": token_bal,
                    "decimals": dec,
                    "contract": tok_contract
                }

            result["networks"][net_key] = net_data

        # Top-level convenience properties
        base_net = result["networks"].get("base", {})
        bsc_net = result["networks"].get("bsc", {})

        result["usdc_balance"] = base_net.get("tokens", {}).get("USDC", {}).get("balance", 0.0)
        result["eth_balance"] = base_net.get("native_balance", 0.0)
        result["usdt_bsc_balance"] = bsc_net.get("tokens", {}).get("USDT", {}).get("balance", 0.0)
        result["usdc_bsc_balance"] = bsc_net.get("tokens", {}).get("USDC", {}).get("balance", 0.0)
        result["bnb_balance"] = bsc_net.get("native_balance", 0.0)

        # Convenience sub-dictionaries for easy access in bot UI
        result["base"] = {
            "ETH": result["eth_balance"],
            "USDC": result["usdc_balance"]
        }
        result["bsc"] = {
            "BNB": result["bnb_balance"],
            "USDT": result["usdt_bsc_balance"],
            "USDC": result["usdc_bsc_balance"]
        }

        return result

    def get_all_balances(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Alias for get_balance() to support bot.py and API calls."""
        return self.get_balance()

    def get_address(self) -> Optional[str]:
        """Method alias for address property."""
        with self._lock:
            return self._address

    def send_token(
        self,
        to_address: str,
        amount: float,
        network: str = "base",
        token: str = "USDC"
    ) -> Dict[str, Any]:
        """
        Send ERC-20 (Base USDC) or BEP-20 (BSC USDT/USDC) to target address.
        """
        net_key = network.lower().strip()
        tok_key = token.upper().strip()

        if net_key not in NETWORKS:
            return {"success": False, "message": f"Jaringan '{network}' tidak didukung. Pilih 'base' atau 'bsc'."}

        net_info = NETWORKS[net_key]
        if tok_key not in net_info["tokens"]:
            return {"success": False, "message": f"Token '{token}' tidak didukung di jaringan {net_info['name']}."}

        tok_info = net_info["tokens"][tok_key]

        with self._lock:
            if not self._connected or not self._address:
                return {"success": False, "message": "Wallet belum terhubung. Silakan hubungkan wallet terlebih dahulu."}
            if not self._account or not self._pk:
                return {
                    "success": False,
                    "message": "Wallet dalam mode pantau (read-only). Untuk mengirim token, hubungkan Private Key wallet Anda."
                }
            account = self._account
            pk = self._pk

        w3 = self._get_w3(net_key)
        if not w3:
            return {
                "success": False,
                "message": "Modul Web3 tidak tersedia di server atau koneksi RPC gagal."
            }

        try:
            # 1. Validate destination address
            if not w3.is_address(to_address):
                return {"success": False, "message": f"Address tujuan tidak valid: {to_address}"}

            to_checksum = w3.to_checksum_address(to_address)
            from_checksum = w3.to_checksum_address(account.address)

            # 2. Token contract & raw amount
            contract = w3.eth.contract(
                address=w3.to_checksum_address(tok_info["contract"]),
                abi=ERC20_ABI
            )
            decimals = tok_info["decimals"]
            amount_raw = int(amount * (10 ** decimals))

            if amount_raw <= 0:
                return {"success": False, "message": "Jumlah transfer harus lebih dari 0."}

            # 3. Check token balance
            balance_raw = contract.functions.balanceOf(from_checksum).call()
            if balance_raw < amount_raw:
                balance_avail = balance_raw / (10 ** decimals)
                return {
                    "success": False,
                    "message": f"Saldo {tok_key} ({net_info['name']}) tidak cukup. Tersedia: {balance_avail:.6f} {tok_key}, Dibutuhkan: {amount:.6f} {tok_key}."
                }

            # 4. Gas estimation and dynamic gas price
            try:
                estimated_gas = contract.functions.transfer(to_checksum, amount_raw).estimate_gas({
                    "from": from_checksum
                })
            except Exception:
                estimated_gas = 65000

            gas_limit = int(estimated_gas * 1.25)
            gas_price = w3.eth.gas_price
            gas_price_boosted = max(int(gas_price * 1.15), 1000000)
            required_gas_wei = gas_limit * gas_price_boosted

            # 5. Native gas balance check (ETH or BNB)
            native_wei = w3.eth.get_balance(from_checksum)
            if native_wei < required_gas_wei:
                native_avail = float(w3.from_wei(native_wei, "ether"))
                req_native = float(w3.from_wei(required_gas_wei, "ether"))
                sym = net_info["native_symbol"]
                return {
                    "success": False,
                    "message": f"Saldo gas {sym} ({net_info['name']}) tidak cukup. Tersedia: {native_avail:.8f} {sym}, Butuh minimal: {req_native:.8f} {sym}."
                }

            # 6. Build transaction
            nonce = w3.eth.get_transaction_count(from_checksum, "pending")
            tx = contract.functions.transfer(to_checksum, amount_raw).build_transaction({
                "chainId": net_info["chain_id"],
                "from": from_checksum,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": gas_price_boosted,
            })

            # 7. Sign and broadcast
            signed = w3.eth.account.sign_transaction(tx, private_key=pk)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = "0x" + tx_hash_hex

            explorer_url = net_info["explorer_tx"].format(tx_hash=tx_hash_hex)

            return {
                "success": True,
                "tx_hash": tx_hash_hex,
                "network": net_key,
                "network_name": net_info["name"],
                "token": tok_key,
                "amount": amount,
                "from": account.address,
                "to": to_address,
                "explorer_url": explorer_url,
                "message": f"Transfer {amount} {tok_key} ({net_info['name']}) berhasil dikirim! TX: {tx_hash_hex[:18]}..."
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def send_usdc(self, to_address: str, usdc_amount: float) -> Dict[str, Any]:
        """Backward compatible helper for Base USDC."""
        return self.send_token(to_address=to_address, amount=usdc_amount, network="base", token="USDC")

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    @property
    def address(self) -> Optional[str]:
        with self._lock:
            return self._address


# Global singleton instances
wallet_manager = WalletManager()

# Multi-user isolated wallet instances
_user_wallets: Dict[str, WalletManager] = {}
_wallets_lock = threading.Lock()

def get_wallet_for_user(username: Optional[str] = None) -> WalletManager:
    """Returns an isolated WalletManager instance for the given username."""
    user_key = (username or "admin").strip().lower()
    if user_key in ("admin", "superadmin", ""):
        return wallet_manager
    with _wallets_lock:
        if user_key not in _user_wallets:
            _user_wallets[user_key] = WalletManager()
        return _user_wallets[user_key]

def logout_user_wallet(username: Optional[str] = None):
    """Disconnects and purges the in-memory wallet instance for the given user upon logout."""
    user_key = (username or "").strip().lower()
    if not user_key or user_key in ("admin", "superadmin"):
        return
    with _wallets_lock:
        w = _user_wallets.pop(user_key, None)
        if w:
            w.disconnect()


