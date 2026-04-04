import hashlib
import json
import time
import os
import datetime
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not found. Environment variables must be set manually.")

# Set up module logger
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Contract ABI – loaded from JSON file if available, otherwise inline minimal
# ---------------------------------------------------------------------------
_ABI_PATH = os.path.join(os.path.dirname(__file__), "contracts", "GrievanceRegistry.json")


def _load_contract_abi():
    """Load the full ABI from the JSON artifact, with a hardcoded fallback."""
    if os.path.exists(_ABI_PATH):
        try:
            with open(_ABI_PATH, "r") as f:
                artifact = json.load(f)
                return artifact.get("abi", artifact)
        except Exception:
            pass

    # Minimal inline ABI covering registerGrievance, getGrievance, grievanceExists
    return [
        {
            "inputs": [
                {"internalType": "string", "name": "_grievanceId", "type": "string"},
                {"internalType": "bytes32", "name": "_audioHash", "type": "bytes32"},
            ],
            "name": "registerGrievance",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "string", "name": "_grievanceId", "type": "string"}
            ],
            "name": "getGrievance",
            "outputs": [
                {
                    "components": [
                        {"internalType": "string", "name": "grievanceId", "type": "string"},
                        {"internalType": "bytes32", "name": "audioHash", "type": "bytes32"},
                        {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                        {"internalType": "address", "name": "registeredBy", "type": "address"},
                    ],
                    "internalType": "struct GrievanceRegistry.Grievance",
                    "name": "",
                    "type": "tuple",
                }
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "string", "name": "_grievanceId", "type": "string"}
            ],
            "name": "grievanceExists",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "getTotalGrievances",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "string", "name": "_grievanceId", "type": "string"},
                {"internalType": "bytes32", "name": "_audioHash", "type": "bytes32"},
            ],
            "name": "verifyHash",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "string", "name": "grievanceId", "type": "string"},
                {"indexed": False, "internalType": "bytes32", "name": "audioHash", "type": "bytes32"},
                {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "registeredBy", "type": "address"},
            ],
            "name": "GrievanceRegistered",
            "type": "event",
        },
    ]


class Blockchain:
    """Hybrid blockchain: Ethereum (Sepolia) primary + local chain fallback.

    If the three environment variables ``ETH_RPC_URL``, ``CONTRACT_ADDRESS``,
    and ``ETH_PRIVATE_KEY`` are all set **and** the RPC endpoint is reachable,
    every grievance is written to the deployed ``GrievanceRegistry`` smart
    contract on Ethereum/Sepolia.  A parallel *local* chain is always
    maintained as an offline backup so the application never loses data even
    if the Ethereum node goes down.

    When none of the ETH variables are configured the class operates in
    **local-only** mode with zero external dependencies.
    """

    def __init__(self):
        # ----- Local chain (always active) -----
        self.chain = []
        self.pending_data = []
        self.create_block(proof=1, previous_hash="0", data="Genesis Block")

        # ----- Ethereum state -----
        self.use_eth = False
        self.w3 = None
        self.contract = None
        self.account = None

        self._init_ethereum()

    # ------------------------------------------------------------------
    # Ethereum bootstrap
    # ------------------------------------------------------------------
    def _init_ethereum(self):
        """Attempt to connect to an Ethereum RPC and bind the smart contract."""
        try:
            rpc_url = os.getenv("ETH_RPC_URL")
            contract_addr = os.getenv("CONTRACT_ADDRESS")
            private_key = os.getenv("ETH_PRIVATE_KEY")

            if not all([rpc_url, contract_addr, private_key]):
                logger.info("Ethereum env vars not fully configured – running in local-only mode.")
                return

            from web3 import Web3

            # Import POA middleware (package name changed across web3 versions)
            try:
                from web3.middleware import geth_poa_middleware
            except ImportError:
                try:
                    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
                except ImportError:
                    geth_poa_middleware = None

            self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))

            if geth_poa_middleware:
                try:
                    self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                except Exception:
                    pass  # Some providers don't need it

            if not self.w3.is_connected():
                logger.warning("⚠️  Ethereum RPC unreachable (%s). Falling back to local mode.", rpc_url)
                return

            logger.info("✅ Connected to Ethereum RPC: %s", rpc_url)

            self.account = self.w3.eth.account.from_key(private_key)
            contract_abi = _load_contract_abi()

            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_addr),
                abi=contract_abi,
            )
            self.use_eth = True
            logger.info("✅ Ethereum blockchain active  |  Wallet: %s", self.account.address)

        except ImportError:
            logger.warning("⚠️  web3 package not installed – running in local-only mode.")
        except Exception as exc:
            logger.warning("⚠️  Ethereum setup error: %s – running in local-only mode.", exc)

    # ------------------------------------------------------------------
    # Local chain helpers
    # ------------------------------------------------------------------
    def create_block(self, proof, previous_hash, data=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "data": data or self.pending_data,
            "proof": proof,
            "previous_hash": previous_hash,
        }
        self.pending_data = []
        self.chain.append(block)
        return block

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_last_block(self):
        return self.chain[-1]

    # ------------------------------------------------------------------
    # Core write – dual-write to ETH + local
    # ------------------------------------------------------------------
    def add_data(self, grievance_id, audio_hash, status):
        """Register a grievance.  Writes to Ethereum if connected, always to local chain."""
        data = {
            "grievance_id": grievance_id,
            "audio_hash": audio_hash,
            "status": status,
            "timestamp": time.time(),
        }
        self.pending_data.append(data)

        eth_tx_hash = None

        # ---- Ethereum write ----
        if self.use_eth:
            try:
                balance = self.w3.eth.get_balance(self.account.address)
                if balance == 0:
                    logger.error("❌ Wallet %s has 0 ETH – cannot send transaction.", self.account.address)
                else:
                    logger.info("🔗 Mining grievance %s to Ethereum…", grievance_id)

                    # Convert SHA-256 hex string → bytes32
                    clean_hash = audio_hash.replace("0x", "")
                    # Pad or truncate to exactly 32 bytes
                    hash_bytes = bytes.fromhex(clean_hash.ljust(64, "0")[:64])

                    tx = self.contract.functions.registerGrievance(
                        str(grievance_id),
                        hash_bytes,
                    ).build_transaction(
                        {
                            "from": self.account.address,
                            "nonce": self.w3.eth.get_transaction_count(self.account.address, "pending"),
                            "gas": 200_000,
                            "gasPrice": self.w3.eth.gas_price,
                        }
                    )

                    signed_tx = self.w3.eth.account.sign_transaction(tx, os.getenv("ETH_PRIVATE_KEY"))
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    eth_tx_hash = self.w3.to_hex(tx_hash)
                    logger.info("✅ ETH transaction sent — hash: %s", eth_tx_hash)

            except Exception as exc:
                logger.error("❌ Ethereum write failed for %s: %s", grievance_id, exc)

        # Store tx hash in the data dict BEFORE creating the block
        # so it persists in the local chain as well
        data["eth_tx_hash"] = eth_tx_hash

        # ---- Local chain write (always) ----
        previous_block = self.get_last_block()
        previous_hash = self.hash(previous_block)
        self.create_block(proof=len(self.chain), previous_hash=previous_hash)

        return data

    # ------------------------------------------------------------------
    # Read / Verify
    # ------------------------------------------------------------------
    def get_verification_report(self):
        """Return a summary of chain health for the admin / public UI."""
        is_valid = self._validate_local_chain()
        message = "✅ Local Chain Valid" if is_valid else "⚠️ Local Chain Integrity Issue"

        if self.use_eth:
            eth_status = "CONNECTED (Sepolia)"
            try:
                on_chain_count = self.contract.functions.getTotalGrievances().call()
                eth_status = f"CONNECTED (Sepolia) — {on_chain_count} on-chain records"
            except Exception:
                eth_status = "CONNECTED (Sepolia) — count unavailable"
        else:
            eth_status = "LOCAL MODE ONLY"

        return {
            "is_valid": is_valid,
            "message": message,
            "total_blocks": len(self.chain),
            "chain_integrity": "VERIFIED" if is_valid else "COMPROMISED",
            "ethereum_status": eth_status,
            "blocks": self.chain[-5:],
        }

    def _find_tx_hash_in_local_chain(self, grievance_id):
        """Check local chain for a stored eth_tx_hash (set during add_data)."""
        for block in self.chain:
            data_list = block.get("data")
            if isinstance(data_list, list):
                for entry in data_list:
                    if isinstance(entry, dict) and entry.get("grievance_id") == grievance_id:
                        return entry.get("eth_tx_hash")
        return None

    def _search_event_logs(self, grievance_id):
        """Try multiple web3 APIs to find the tx hash from contract events."""
        # Strategy 1: web3 v6+ get_logs (preferred)
        try:
            events = self.contract.events.GrievanceRegistered.get_logs(
                from_block=0,
                to_block="latest",
            )
            for evt in events:
                # Compare grievanceId from the event data
                evt_gid = evt.get("args", {}).get("grievanceId", "")
                if evt_gid == str(grievance_id):
                    return evt["transactionHash"].hex()
        except Exception as e1:
            logger.debug("get_logs attempt failed: %s", e1)

        # Strategy 2: create_filter with web3 v6 kwarg style
        try:
            event_filter = self.contract.events.GrievanceRegistered.create_filter(
                from_block=0,
                to_block="latest",
            )
            for evt in event_filter.get_all_entries():
                evt_gid = evt.get("args", {}).get("grievanceId", "")
                if evt_gid == str(grievance_id):
                    return evt["transactionHash"].hex()
        except Exception as e2:
            logger.debug("create_filter attempt failed: %s", e2)

        return None

    def find_grievance_in_chain(self, grievance_id):
        """Look up a grievance: Ethereum first, then local chain fallback."""

        # ---- Ethereum lookup ----
        if self.use_eth:
            try:
                data_struct = self.contract.functions.getGrievance(str(grievance_id)).call()
                returned_hash = data_struct[1].hex()

                # Try to find the tx hash (multiple strategies)
                tx_hash = self._find_tx_hash_in_local_chain(grievance_id)

                if not tx_hash:
                    try:
                        tx_hash = self._search_event_logs(grievance_id)
                    except Exception as log_err:
                        logger.warning("⚠️  Event log search failed: %s", log_err)

                return {
                    "found": True,
                    "source": "ETHEREUM_BLOCKCHAIN",
                    "timestamp": datetime.datetime.fromtimestamp(data_struct[2]).strftime("%Y-%m-%d %H:%M:%S"),
                    "block_hash": f"ETH_BLOCK_{data_struct[3]}",
                    "audio_hash": returned_hash,
                    "tx_hash": tx_hash,
                }
            except Exception:
                pass  # Not found on ETH, try local chain

        # ---- Local chain fallback ----
        for block in self.chain:
            data_list = block.get("data")
            if isinstance(data_list, list):
                for entry in data_list:
                    if isinstance(entry, dict) and entry.get("grievance_id") == grievance_id:
                        return {
                            "found": True,
                            "source": "LOCAL_CHAIN" if not self.use_eth else "LOCAL_CHAIN_FALLBACK",
                            "block_index": block["index"],
                            "block_hash": self.hash(block),
                            "timestamp": datetime.datetime.fromtimestamp(
                                block.get("timestamp", 0)
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            "tx_hash": entry.get("eth_tx_hash"),
                        }

        return {"found": False}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate_local_chain(self):
        """Walk the local chain and verify hash linkage."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current["previous_hash"] != self.hash(previous):
                return False
        return True