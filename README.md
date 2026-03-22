# SAMVAAD - Local Blockchain-Based Grievance Management System

A secure, transparent, and accessible grievance management system that combines local blockchain technology, AI analysis, and voice-based IVR for seamless complaint registration and verification.

## Overview

SAMVAAD is a citizen-centric platform that enables people to register complaints via phone calls in their native language (Hinglish), with automatic AI-powered analysis and immutable custom blockchain storage for transparency and accountability.

## Key Features

### 📱 SMS Notifications
- **Registration Confirmation**: Instant SMS with tracking ID and verification link
- **Resolution Updates**: Automatic SMS when admin resolves complaint
- No need for citizens to repeatedly call back
- Works on any phone - no smartphone required

### 🎙️ Voice-Based IVR System
- Twilio-powered voice interface with Hinglish prompts
- No app or internet required - just a phone call
- Speech recognition for state, city, and area
- Keypad input for 6-digit pincode
- Time-based greetings for personalized experience
- 60-second audio recording for detailed complaints
- **Smart 10-digit ticket ID** with state code + pincode + hex
- **SMS acknowledgment** with tracking ID sent immediately after registration
- **SMS notification** when grievance is resolved by admin

### 🤖 AI-Powered Analysis
- Google Gemini AI for automatic transcription
- Intelligent categorization (Water/Road/Electricity/Medical/Corruption/Other)
- Sentiment analysis (Urgent/Calm/Angry)
- Priority detection (High/Medium/Low)
- Automated summary generation

### 🔗 Blockchain Security
- Immutable record storage using custom local blockchain
- Tamper-proof audit trail with SHA-256 hashing
- Transparent verification without login

### 📊 Admin Dashboard
- Clean, minimal interface for grievance management
- Real-time status updates (Pending/Resolved)
- Analytics with category breakdown
- Audio playback and AI report viewing
- Complete blockchain verification

### 🔍 Public Verification
- Citizens can verify complaints using 6-digit ticket ID
- No login required for transparency
- Blockchain-backed proof of registration
- Transaction hash and timestamp verification

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python 3.8+) |
| AI/ML | Google Gemini AI |
| Voice/IVR | Twilio Voice API |
| Blockchain | Custom Local Chain |
| Frontend | Vanilla JavaScript, CSS |
| Database | In-memory (Python dict) |

## Installation

### Prerequisites

- Python 3.8 or higher
- Twilio account with phone number
- Google AI API key (Gemini)
- Git

### Quick Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd samvaad
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the root directory:

```env
# Twilio Configuration
account_sid=your_twilio_account_sid
auth_token=your_twilio_auth_token
twilio_number=+1234567890
my_mobile_number=+1234567890

# Google AI Configuration
GOOGLE_API_KEY=your_google_gemini_api_key

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=samvaad@2024
SECRET_KEY=your_secret_session_key
```

4. **Run the application**
```bash
python app.py
```

5. **Set up ngrok for Twilio (Development)**
```bash
# In a new terminal
ngrok http 5000
```
Copy the HTTPS URL and configure it in Twilio (see Configuration section below)

6. **Access the system**
- Admin Dashboard: http://localhost:5000/login
- Public Verification: http://localhost:5000/verify_blockchain
- IVR: Call your Twilio number
- ngrok Dashboard: http://localhost:4040

## Project Structure

```
samvaad/
├── app.py                      # Main Flask application
├── blockchain.py               # Local blockchain implementation
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── README.md                   # This file
├── templates/
│   ├── admin.html             # Admin dashboard
│   ├── login.html             # Login page
│   └── verify.html            # Public verification page
└── static/
    ├── style.css              # Styles
    ├── script.js              # Client-side logic
    └── recordings/            # Audio files storage (auto-created)
```

## Usage Guide

### For Citizens

1. **Register a Complaint**
   - Call the Twilio number
   - Press 1 to register a new complaint
   - Provide your state when prompted (voice)
   - Provide your city when prompted (voice)
   - Enter your 6-digit pincode (keypad)
   - Provide your area/locality when prompted (voice)
   - Record your complaint after the beep (max 60 seconds)
   - Note down the **10-digit ticket ID** announced
   - **Receive SMS confirmation** with tracking link

2. **Check Status**
   - Call the Twilio number
   - Press 2 to check status
   - Enter your 10-digit ticket ID
   - Or click the link in your SMS

3. **Verify on Blockchain**
   - Visit http://localhost:5000/verify_blockchain
   - Enter your 10-digit ticket ID
   - View blockchain verification details

### Ticket ID Format

SAMVAAD uses a smart 10-digit ticket ID system:

**Format**: `[STATE][PINCODE][HEX]`

**Example**: `MH400001A5`
- `MH` = Maharashtra (2-letter state code)
- `400001` = Pincode (6 digits)
- `A5` = Random hex code (2 characters)

4. **Get Resolution Updates**
   - **Automatic SMS notification** when admin resolves your complaint
   - No need to keep calling back

### For Administrators

1. **Login**
   - Navigate to http://localhost:5000/login
   - Enter credentials (default: admin/samvaad@2024)

2. **Dashboard Views**
   - **Dashboard**: View pending grievances
   - **All Grievances**: View complete list
   - **Analytics**: View statistics and category breakdown

3. **Manage Grievances**
   - Click on any grievance to view details
   - Listen to audio recordings
   - Read AI analysis reports
   - Update status (Pending → Resolved)
   - **SMS automatically sent** to citizen when marked as Resolved

## Security Features

- **Session-based authentication** with secure cookies
- **Blockchain immutability** prevents data tampering
- **Cryptographic hashing (SHA-256)** for audio files
- **Public verification** without exposing admin access
- **Environment variable protection** for sensitive keys

## Default Credentials

**⚠️ IMPORTANT: Change these in production!**

- Username: `admin`
- Password: `samvaad@2024`

## API Endpoints

### Public Endpoints
- `GET /verify_blockchain?id=123456` - Verify grievance on blockchain
- `GET /verify_grievance/<id>` - Get grievance verification JSON
- `POST /voice` - Twilio IVR webhook

### Protected Endpoints (Login Required)
- `GET /admin` - Admin dashboard
- `GET /all_grievances` - View all grievances
- `GET /analytics` - View analytics
- `POST /update_status` - Update grievance status

## Future Implementation

### 🛡️ Ethereum Blockchain Integration
We plan to integrate the Ethereum blockchain (Sepolia/Mainnet) to provide even greater decentralization and public verifiability. This will allow:
- Smart contract-based grievance registry.
- Global auditability via public block explorers like Etherscan.
- Enhanced resistance to any form of local tampering.

## Configuration

### Twilio Setup
1. Create account at https://www.twilio.com
2. Get a phone number with voice capabilities
3. Configure webhook URL: `https://your-domain.com/voice`
4. Add credentials to `.env`

### Using ngrok for Local Development
1. Start your Flask app: `python app.py`
2. Start ngrok in a new terminal: `ngrok http 5000`
3. Configure Twilio Dashboard with the ngrok URL

### Google AI Setup
1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env` as `GOOGLE_API_KEY`

## Troubleshooting

### Audio Not Recording
- Check Twilio webhook configuration
- Verify credentials in `.env`
- Ensure recordings folder has write permissions
- **Check ngrok is running**

### SMS Not Sending
- Verify `twilio_number` is set correctly in `.env`
- Check Twilio account capabilities
- Check console logs for errors

### AI Analysis Failing
- Verify `GOOGLE_API_KEY` is valid
- Check audio file size
- Review console logs

### Blockchain Issues
- System uses a custom local blockchain for immutable storage.
- Check console for any integrity warnings.

## Deployment

### Production Checklist
- [ ] Change default admin credentials
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production Twilio number
- [ ] Set up HTTPS with SSL certificate
- [ ] Review security best practices
- [ ] Configure backup strategy

## Contributing

Contributions are welcome! Please submit a pull request for any improvements.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub or check the troubleshooting guide above.

## Acknowledgments

- Twilio for voice infrastructure
- Google for Gemini AI
- SAMVAAD Open Source Community

---
**Built with ❤️ for transparent governance and citizen empowerment**
