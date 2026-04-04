# SAMVAAD — Blockchain-Secured Grievance Management System

A secure, transparent, and accessible grievance management platform that combines **Ethereum blockchain** immutability, **AI-powered audio analysis**, and **voice-based IVR** for seamless complaint registration and verification.

---

## Overview

SAMVAAD is a citizen-centric system that lets people register complaints via a simple phone call in **Hinglish** (Hindi + English). Every grievance is:

1. **Transcribed & categorized** by Google Gemini AI.
2. **Hashed (SHA-256)** and written to an **Ethereum smart contract** on the Sepolia testnet for tamper-proof public auditability.
3. **Backed up** on a parallel local blockchain so the system never loses data, even if the ETH node is unreachable.
4. **Tracked end-to-end** — citizens receive SMS confirmations and resolution notifications automatically.

---

## Key Features

### 🔗 Ethereum Blockchain Integration
- **Dual-write architecture** — every grievance is written to both the Ethereum Sepolia smart contract *and* a local blockchain.
- **`GrievanceRegistry` Solidity contract** — stores grievance ID, SHA-256 audio hash, timestamp, and registering wallet address.
- **Auto-detection** — if `ETH_RPC_URL`, `CONTRACT_ADDRESS`, and `ETH_PRIVATE_KEY` are set in `.env`, the system automatically connects to Sepolia at startup; otherwise it gracefully runs in local-only mode.
- **Public verifiability** — any citizen can look up their grievance on [Sepolia Etherscan](https://sepolia.etherscan.io) using the transaction hash.
- **Tamper-proof audit trail** — once a grievance is mined, neither admins nor developers can alter the record.

### 🎙️ Voice-Based IVR System
- Twilio-powered voice interface with Hinglish prompts
- No app or internet required — just a phone call
- Speech recognition for state, city, and area
- Keypad input for 6-digit pincode
- 60-second audio recording for detailed complaints
- **Smart 10-digit ticket ID**: `[STATE_CODE][PINCODE][HEX]` (e.g. `MH400001A5`)

### 📱 SMS Notifications
- **Registration confirmation** — instant SMS with tracking ID and verification link
- **Resolution updates** — automatic SMS when admin resolves a complaint
- Works on any phone — no smartphone required

### 🤖 AI-Powered Analysis
- Google Gemini AI for automatic audio transcription
- Intelligent categorization (Water / Road / Electricity / Medical / Corruption / Other)
- Sentiment analysis (Urgent / Calm / Angry)
- Priority detection (High / Medium / Low)
- One-sentence summary generation

### 📊 Admin Dashboard
- Session-protected admin panel
- Real-time grievance management (Pending → Resolved)
- Analytics with category breakdown
- Audio playback and AI report viewing
- Full blockchain verification status

### 🔍 Public Verification Portal
- Citizens can verify complaints using their 10-digit ticket ID
- Ethereum transaction hash + Etherscan deep-link when available
- No login required — full transparency by design
- Shows source (Ethereum Network / Local Node) explicitly

---

## Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌───────────────────┐
│  Citizen     │─────▶│  Twilio IVR      │─────▶│  Flask Backend    │
│  (Phone)     │      │  (Voice + DTMF)  │      │  (app.py)         │
└──────────────┘      └──────────────────┘      └────────┬──────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────┐
                       │                                 │                 │
                       ▼                                 ▼                 ▼
              ┌─────────────────┐           ┌─────────────────┐  ┌─────────────────┐
              │  Gemini AI      │           │  Ethereum       │  │  Local Chain    │
              │  (Transcribe &  │           │  (Sepolia)      │  │  (Backup)       │
              │   Categorize)   │           │  Smart Contract │  │  In-Memory      │
              └─────────────────┘           └─────────────────┘  └─────────────────┘
```

---

## Technology Stack

| Component     | Technology                              |
|---------------|-----------------------------------------|
| Backend       | Flask (Python 3.8+)                     |
| AI/ML         | Google Gemini AI                        |
| Voice/IVR     | Twilio Voice API                        |
| Blockchain    | Ethereum Sepolia + Local Chain Fallback |
| Smart Contract| Solidity 0.8.20 (`GrievanceRegistry`)   |
| ETH Library   | Web3.py ≥ 6.0                           |
| Frontend      | Vanilla JavaScript, CSS                 |
| Database      | In-memory (Python dict)                 |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Twilio account with a voice-capable phone number
- Google AI API key (Gemini)
- *(Optional)* Ethereum wallet with Sepolia ETH for on-chain writes
- *(Optional)* Deployed `GrievanceRegistry` smart contract on Sepolia
- Git

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd samvaad
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy `env_template.txt` to `.env` and fill in your values:

   ```env
   # Application
   SECRET_KEY=your-secret-key-change-in-production
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=samvaad@2024

   # Google Gemini AI
   GOOGLE_API_KEY=your_google_gemini_api_key

   # Twilio IVR
   account_sid=your_twilio_account_sid
   auth_token=your_twilio_auth_token
   twilio_number=+1234567890
   my_mobile_number=+1234567890

   # Ethereum Blockchain (auto-detected at startup)
   # Set all three to enable on-chain writes; leave empty for local-only mode.
   ETH_RPC_URL=https://ethereum-sepolia.publicnode.com
   CONTRACT_ADDRESS=0xYourDeployedContractAddress
   ETH_PRIVATE_KEY=0xYourWalletPrivateKey
   ```

5. **Run the application**
   ```bash
   python app.py
   ```
   On startup you will see either:
   - `✅ Connected to Ethereum RPC` + `✅ Ethereum blockchain active` — ETH mode enabled
   - `Ethereum env vars not fully configured – running in local-only mode` — local fallback

6. **Set up ngrok for Twilio** *(development only)*
   ```bash
   ngrok http 5000
   ```
   Copy the HTTPS URL and set it as the webhook in the Twilio Console → Phone Numbers → Voice → *A call comes in* → `https://<ngrok-url>/voice`

7. **Access the system**
   - Admin Dashboard: [http://localhost:5000/login](http://localhost:5000/login)
   - Public Verification: [http://localhost:5000/verify_blockchain](http://localhost:5000/verify_blockchain)
   - IVR: Call your Twilio number
   - ngrok Inspector: [http://localhost:4040](http://localhost:4040)

---

## Project Structure

```
samvaad/
├── app.py                          # Main Flask application
├── blockchain.py                   # Hybrid blockchain (ETH + local)
├── trigger.py                      # Manual IVR trigger script
├── requirements.txt                # Python dependencies
├── env_template.txt                # .env template
├── .env                            # Environment variables (create this)
├── README.md                       # This file
│
├── contracts/                      # Smart contract artifacts
│   ├── GrievanceRegistry.sol       # Solidity source (^0.8.20)
│   └── GrievanceRegistry.json      # Compiled ABI
│
├── templates/
│   ├── admin.html                  # Admin dashboard
│   ├── login.html                  # Login page
│   └── verify.html                 # Public verification portal
│
├── static/
│   ├── style.css                   # Styles
│   ├── script.js                   # Client-side logic
│   └── recordings/                 # Audio files (auto-created)
│
└── eth_logic_backup/               # Original ETH reference files
    ├── blockchain.py
    ├── contracts/
    ├── BLOCKCHAIN.md
    ├── README_ETH.md
    └── REIMPLEMENT_ETH.md
```

---

## Smart Contract

### `GrievanceRegistry.sol`

Deployed on **Ethereum Sepolia** testnet. Key functions:

| Function | Description |
|----------|-------------|
| `registerGrievance(string _id, bytes32 _audioHash)` | Stores a new grievance with its audio SHA-256 hash |
| `getGrievance(string _id)` → `Grievance` | Retrieves grievance details (ID, hash, timestamp, registrant) |
| `grievanceExists(string _id)` → `bool` | Checks if a grievance ID is already recorded |
| `verifyHash(string _id, bytes32 _hash)` → `bool` | Verifies that a given hash matches the on-chain record |
| `getTotalGrievances()` → `uint256` | Returns total number of registered grievances |

**Event emitted**: `GrievanceRegistered(string indexed grievanceId, bytes32 audioHash, uint256 timestamp, address indexed registeredBy)`

### Deploying the Contract

1. Open [Remix IDE](https://remix.ethereum.org)
2. Paste `contracts/GrievanceRegistry.sol`
3. Compile with Solidity 0.8.20+
4. Deploy to Sepolia using MetaMask
5. Copy the deployed contract address into `.env` → `CONTRACT_ADDRESS`

---

## Usage Guide

### For Citizens

1. **Register a Complaint**
   - Call the Twilio number
   - Press **1** to register a new complaint
   - Provide your state (voice), city (voice), pincode (keypad), area (voice)
   - Record your complaint after the beep (max 60 seconds)
   - Note the **10-digit ticket ID** announced
   - Receive an **SMS confirmation** with a tracking link

2. **Check Status via Phone**
   - Call the Twilio number → Press **2** → Enter your 10-digit ticket ID

3. **Verify on Blockchain**
   - Visit `/verify_blockchain`
   - Enter your 10-digit ticket ID
   - View Ethereum transaction hash, block hash, and Etherscan link

4. **Get Resolution Updates**
   - Automatic SMS when admin resolves your complaint

### Ticket ID Format

**`[STATE][PINCODE][HEX]`** — e.g. `MH400001A5`
- `MH` = Maharashtra (2-letter state code)
- `400001` = Pincode (6 digits)
- `A5` = Random hex suffix (2 characters)

### For Administrators

1. Login at `/login` (default: `admin` / `samvaad@2024`)
2. **Dashboard** — view pending grievances
3. **All Grievances** — complete list with status
4. **Analytics** — category breakdown, resolution rate
5. **Resolve** — mark grievances as Resolved (triggers citizen SMS and on-chain status)

---

## API Endpoints

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/verify_blockchain?id=<ticket>` | Public verification portal |
| `GET`  | `/verify_grievance/<id>` | JSON verification data |
| `GET`  | `/api/verify` | Chain health report (JSON) |
| `GET`  | `/api/check_analysis/<id>` | AI analysis status (JSON) |
| `POST` | `/voice` | Twilio IVR webhook |
| `GET`  | `/diagnostic` | System diagnostic info |

### Protected (login required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/admin` | Admin dashboard |
| `GET`  | `/all_grievances` | All grievances view |
| `GET`  | `/analytics` | Analytics dashboard |
| `POST` | `/update_status` | Update grievance status |

---

## Security Features

- **Ethereum immutability** — on-chain records cannot be altered by anyone
- **Local chain integrity validation** — hash-linkage verified on every report
- **SHA-256 audio hashing** — proves the audio file has not been tampered with
- **Session-based admin authentication** with secure cookies
- **Environment variable protection** — secrets never hardcoded
- **Graceful degradation** — system runs fully functional even without ETH connectivity

---

## Blockchain Modes

| Mode | When Active | What Happens |
|------|------------|--------------|
| **Ethereum + Local** | All 3 ETH env vars set & RPC reachable | Grievances dual-written to Sepolia contract and local chain |
| **Local Only** | ETH vars missing or RPC unreachable | Grievances stored in local chain only (no external dependency) |

The system auto-detects the mode at startup — no code changes needed.

---

## Configuration

### Twilio Setup
1. Create account at [twilio.com](https://www.twilio.com)
2. Get a phone number with voice capabilities
3. Set webhook: `https://your-domain.com/voice` (POST)
4. Add credentials to `.env`

### Google AI Setup
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env` as `GOOGLE_API_KEY`

### Ethereum Setup
1. Get Sepolia ETH from a [faucet](https://sepoliafaucet.com)
2. Deploy `contracts/GrievanceRegistry.sol` via [Remix](https://remix.ethereum.org)
3. Add `ETH_RPC_URL`, `CONTRACT_ADDRESS`, and `ETH_PRIVATE_KEY` to `.env`

---

## Troubleshooting

### Ethereum Not Connecting
- Verify all three env vars (`ETH_RPC_URL`, `CONTRACT_ADDRESS`, `ETH_PRIVATE_KEY`) are set
- Check that the RPC URL is reachable: `curl https://ethereum-sepolia.publicnode.com`
- Ensure the wallet has Sepolia ETH for gas fees
- Check console for `⚠️ Ethereum setup error` messages

### Audio Not Recording
- Check Twilio webhook configuration points to your ngrok URL
- Verify Twilio credentials in `.env`
- Ensure `static/recordings/` has write permissions

### SMS Not Sending
- Verify `twilio_number` format includes country code (e.g. `+1...`)
- Check Twilio account capabilities and balance
- Review console for `❌ SMS failed` messages

### AI Analysis Failing
- Verify `GOOGLE_API_KEY` is valid and has Gemini access
- Check audio file size (must be > 1KB)
- Review console for `❌ Processing error` messages

---

## Deployment Checklist

- [ ] Change default admin credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`)
- [ ] Use a strong, random `SECRET_KEY`
- [ ] Configure production Twilio number
- [ ] Set up HTTPS with SSL certificate
- [ ] Deploy `GrievanceRegistry` contract to Sepolia (or mainnet)
- [ ] Fund the ETH wallet with sufficient gas
- [ ] Add persistent database (replace in-memory dict) for production
- [ ] Configure backup strategy for audio recordings
- [ ] Review and rotate all API keys periodically

---

## Default Credentials

> **⚠️ Change these before any production or public deployment!**

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `samvaad@2024` |

---

## Contributing

Contributions are welcome! Please submit a pull request for any improvements.

## License

MIT License — see LICENSE file for details.

## Acknowledgments

- [Twilio](https://www.twilio.com) for voice infrastructure
- [Google](https://ai.google.dev) for Gemini AI
- [Ethereum](https://ethereum.org) for decentralized blockchain infrastructure
- SAMVAAD Open Source Community

---

**Built with ❤️ for transparent governance and citizen empowerment**
