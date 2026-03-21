import os
import requests
import hashlib
import random
import datetime
import threading
from flask import Flask, request, render_template, redirect, url_for, jsonify, session
from functools import wraps
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
import google.generativeai as genai
from blockchain import Blockchain

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
samvaad_chain = Blockchain()
grievance_db = {}  # in-memory storage for grievances

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# initialize Twilio client for SMS
twilio_client = Client(os.getenv('account_sid'), os.getenv('auth_token'))
TWILIO_NUMBER = os.getenv('twilio_number')
my_mobile_number=os.getenv('my_mobile_number')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

def get_greeting():
    """Returns time-appropriate greeting in Hinglish"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Namaste. Aap ka swagat hai Samvaad mein."
    elif hour < 18:
        return "Namaste. Samvaad helpline mein aapka swagat hai."
    else:
        return "Namaste. Samvaad mein aapka swagat hai."

def get_state_code(state_name):
    """Extracts 2-letter code from state name"""
    state_mapping = {
        'andhra pradesh': 'AP', 'arunachal pradesh': 'AR', 'assam': 'AS',
        'bihar': 'BR', 'chhattisgarh': 'CG', 'goa': 'GA', 'gujarat': 'GJ',
        'haryana': 'HR', 'himachal pradesh': 'HP', 'jharkhand': 'JH',
        'karnataka': 'KA', 'kerala': 'KL', 'madhya pradesh': 'MP',
        'maharashtra': 'MH', 'manipur': 'MN', 'meghalaya': 'ML',
        'mizoram': 'MZ', 'nagaland': 'NL', 'odisha': 'OR', 'punjab': 'PB',
        'rajasthan': 'RJ', 'sikkim': 'SK', 'tamil nadu': 'TN',
        'telangana': 'TG', 'tripura': 'TR', 'uttar pradesh': 'UP',
        'uttarakhand': 'UK', 'west bengal': 'WB', 'delhi': 'DL',
        'jammu and kashmir': 'JK', 'ladakh': 'LA', 'puducherry': 'PY',
        'chandigarh': 'CH', 'andaman and nicobar': 'AN',
        'dadra and nagar haveli': 'DN', 'daman and diu': 'DD',
        'lakshadweep': 'LD'
    }
    
    state_lower = state_name.lower().strip()
    
    # try exact match first
    if state_lower in state_mapping:
        return state_mapping[state_lower]
    
    # try partial match
    for key, code in state_mapping.items():
        if key in state_lower or state_lower in key:
            return code
    
    # fallback: use first two letters
    return state_name[:2].upper()

def generate_ticket_id(state_name, pincode):
    """Generates 10-digit ticket: 2-letter state code + 6-digit pincode + 2-char hex"""
    state_code = get_state_code(state_name)
    hex_suffix = format(random.randint(0, 255), '02X')  # 2-digit hex (00-FF)
    ticket_id = f"{state_code}{pincode}{hex_suffix}"
    return ticket_id

def send_sms_acknowledgment(phone_number, grievance_id):
    """Sends SMS confirmation after grievance registration"""
    try:
        message = twilio_client.messages.create(
            body=f"Grievance Registered. Your Tracking ID is {grievance_id}. Track at https://codi-interpressure-jacqui.ngrok-free.dev/verify_blockchain",
            from_=TWILIO_NUMBER,
            to=my_mobile_number
        )
        print(f"✅ SMS sent to {my_mobile_number}: {message.sid}")
    except Exception as e:
        print(f"❌ SMS failed: {str(e)}")

def send_resolution_sms(phone_number, grievance_id):
    """Sends SMS when grievance is resolved"""
    try:
        message = twilio_client.messages.create(
            body=f"Your grievance (ID: {grievance_id}) has been resolved. Thank you for using SAMVAAD.",
            from_=TWILIO_NUMBER,
            to=my_mobile_number
        )
        print(f"✅ Resolution SMS sent to {my_mobile_number}: {message.sid}")
    except Exception as e:
        print(f"❌ Resolution SMS failed: {str(e)}")

def analyze_audio_with_ai(file_path):
    """Uses Gemini AI to transcribe and categorize audio complaints"""
    try:
        if not os.path.exists(file_path):
            return f"Error: Audio file not found"
        
        audio_file = genai.upload_file(file_path)
        
        prompt = """Listen to this audio grievance complaint and analyze it. Return a summary in this format:
        
        Transcription: [What the person said]
        Category: [Water/Road/Electricity/Medical/Corruption/Other]
        Summary: [1 sentence summary of the complaint]
        Sentiment: [Urgent/Calm/Angry]
        Priority: [High/Medium/Low]"""
        
        gemini_response = gemini_model.generate_content([prompt, audio_file])
        return gemini_response.text
        
    except Exception as e:
        return f"AI Analysis Failed: {str(e)}"

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    resp = VoiceResponse()
    greeting = get_greeting()
    full_message = f"{greeting} Apni shikayat register karne ke liye 1 dabayein. Status check karne ke liye 2 dabayein."
    
    gather = Gather(num_digits=1, action='/gather', method='POST')
    gather.say(full_message, voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.redirect('/voice')
    return str(resp)

@app.route("/gather", methods=['GET', 'POST'])
def gather():
    digit = request.values.get('Digits', None)
    resp = VoiceResponse()

    if digit == '1':
        resp.redirect('/ask_state')
    elif digit == '2':
        gather = Gather(num_digits=10, action='/status_result', method='POST')
        gather.say("Apna 10 digit tracking number enter karein.", voice='Polly.Aditi', language='en-IN')
        resp.append(gather)
    else:
        resp.say("Galat option. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
        resp.redirect('/voice')

    return str(resp)

@app.route("/ask_state", methods=['GET', 'POST'])
def ask_state():
    resp = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/save_state', method='POST', language='en-IN', speechTimeout='auto')
    gather.say("Pehle batayein, aap kis state se bol rahe hain?", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_state')
    return str(resp)

@app.route("/save_state", methods=['GET', 'POST'])
def save_state():
    state = request.values.get('SpeechResult', None)
    if not state:
        return redirect('/ask_state')
    
    session_id = request.values.get('CallSid')
    if session_id not in grievance_db:
        grievance_db[session_id] = {}
    grievance_db[session_id]['state'] = state
    
    resp = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/save_city', method='POST', language='en-IN', speechTimeout='auto')
    gather.say("Theek hai. Ab batayein aapka shehar ya Jilla kya hai?", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_city')
    return str(resp)

@app.route("/ask_city", methods=['GET', 'POST'])
def ask_city():
    resp = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/save_city', method='POST', language='en-IN', speechTimeout='auto')
    gather.say("Aapka shehar ya Jilla kya hai?", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_city')
    return str(resp)

@app.route("/save_city", methods=['GET', 'POST'])
def save_city():
    city = request.values.get('SpeechResult', None)
    if not city:
        return redirect('/ask_city')
    
    session_id = request.values.get('CallSid')
    if session_id in grievance_db:
        grievance_db[session_id]['city'] = city
    
    resp = VoiceResponse()
    gather = Gather(num_digits=6, action='/save_pincode', method='POST')
    gather.say("Ab apna 6 digit pincode enter karein.", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_pincode')
    return str(resp)

@app.route("/ask_pincode", methods=['GET', 'POST'])
def ask_pincode():
    resp = VoiceResponse()
    gather = Gather(num_digits=6, action='/save_pincode', method='POST')
    gather.say("Apna 6 digit pincode enter karein.", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_pincode')
    return str(resp)

@app.route("/save_pincode", methods=['GET', 'POST'])
def save_pincode():
    pincode = request.values.get('Digits', None)
    if not pincode or len(pincode) != 6:
        return redirect('/ask_pincode')
    
    session_id = request.values.get('CallSid')
    if session_id in grievance_db:
        grievance_db[session_id]['pincode'] = pincode
    
    resp = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/save_location', method='POST', language='en-IN', speechTimeout='auto')
    gather.say("Theek hai. Ab aapka area ya mohalla batayein.", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_location')
    return str(resp)

@app.route("/ask_location", methods=['GET', 'POST'])
def ask_location():
    resp = VoiceResponse()
    gather = Gather(input='speech', timeout=5, action='/save_location', method='POST', language='en-IN', speechTimeout='auto')
    gather.say("Aapka area ya mohalla kya hai?", voice='Polly.Aditi', language='en-IN')
    resp.append(gather)
    resp.say("Koi jawab nahi mila. Dobara try karein.", voice='Polly.Aditi', language='en-IN')
    resp.redirect('/ask_location')
    return str(resp)

@app.route("/save_location", methods=['GET', 'POST'])
def save_location():
    location = request.values.get('SpeechResult', None)
    if not location:
        return redirect('/ask_location')
    
    session_id = request.values.get('CallSid')
    if session_id in grievance_db:
        grievance_db[session_id]['location'] = location
    
    resp = VoiceResponse()
    resp.say("Dhanyavaad. Ab beep ke baad apni shikayat clearly bolein.", voice='Polly.Aditi', language='en-IN')
    resp.record(maxLength=60, finishOnKey='#', playBeep=True, action='/handle_recording')
    return str(resp)

@app.route("/handle_recording", methods=['GET', 'POST'])
def handle_recording():
    """Handles audio recording from Twilio and generates ticket ID"""
    recording_url = request.values.get("RecordingUrl")
    caller_number = request.values.get("From")  # get caller's phone number
    
    session_id = request.values.get('CallSid')
    location_data = grievance_db.get(session_id, {})
    state = location_data.get('state', 'Not provided')
    city = location_data.get('city', 'Not provided')
    pincode = location_data.get('pincode', '000000')
    location = location_data.get('location', 'Not provided')
    
    # generate smart 10-digit ticket ID
    g_id = generate_ticket_id(state, pincode)
    
    ai_analysis = "🔄 AI Analysis in Progress..."
    file_hash = "Pending"
    local_audio_path = None
    
    # clean up temporary session data
    if session_id in grievance_db:
        del grievance_db[session_id]
    
    grievance_db[g_id] = {
        'url': 'pending',
        'hash': 'pending',
        'status': 'Pending',
        'ai_report': ai_analysis,
        'state': state,
        'city': city,
        'pincode': pincode,
        'location': location,
        'phone': caller_number,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    resp = VoiceResponse()
    # format ID for voice: MH 400001 A5 -> M H 4 0 0 0 0 1 A 5
    formatted_id = " ".join(list(g_id))
    resp.say("Aapki shikayat register ho gayi hai aur blockchain par secure kar di gayi hai.", voice='Polly.Aditi', language='en-IN')
    resp.say(f"Aapka tracking number hai {formatted_id}. Ek baar phir, {formatted_id}.", voice='Polly.Aditi', language='en-IN')
    resp.say("Aapko SMS bhi bheja jayega. Dhanyavaad.", voice='Polly.Aditi', language='en-IN')
    
    # send SMS acknowledgment
    if caller_number:
        send_sms_acknowledgment(caller_number, g_id)
    
    if recording_url:
        thread = threading.Thread(target=process_audio_async, args=(recording_url, g_id))
        thread.daemon = True
        thread.start()
    
    return str(resp)

def process_audio_async(recording_url, g_id):
    """Background task to download audio, generate hash, and run AI analysis"""
    try:
        os.makedirs('static/recordings', exist_ok=True)
        saved_filename = f"static/recordings/{g_id}.wav"
        temp_filename = f"temp_{g_id}.wav"
        
        account_sid = os.getenv('account_sid')
        auth_token = os.getenv('auth_token')
        
        # download audio from Twilio
        response = requests.get(recording_url + ".wav", auth=(account_sid, auth_token), timeout=30)
        
        if response.status_code == 200 and len(response.content) > 1000:
            with open(temp_filename, 'wb') as f:
                f.write(response.content)
            
            # generate SHA-256 hash for blockchain
            with open(temp_filename, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # run AI analysis
            ai_analysis = analyze_audio_with_ai(temp_filename)
            
            # save permanent copy
            with open(temp_filename, 'rb') as src:
                with open(saved_filename, 'wb') as dst:
                    dst.write(src.read())
            
            local_audio_path = f"recordings/{g_id}.wav"
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            
            if g_id in grievance_db:
                grievance_db[g_id]['url'] = local_audio_path
                grievance_db[g_id]['hash'] = file_hash
                grievance_db[g_id]['ai_report'] = ai_analysis
                
                # register on blockchain
                blockchain_result = samvaad_chain.add_data(g_id, file_hash, 'Pending')
                
                # maintain local chain as backup
                previous_block = samvaad_chain.get_last_block()
                if previous_block:
                    previous_hash = samvaad_chain.hash(previous_block)
                    samvaad_chain.create_block(proof=len(grievance_db), previous_hash=previous_hash)
                
                print(f"✅ Background processing complete for {g_id}")
        else:
            if g_id in grievance_db:
                grievance_db[g_id]['ai_report'] = "❌ Audio download failed"
                grievance_db[g_id]['url'] = "error"
                
    except Exception as e:
        print(f"❌ Background processing error for {g_id}: {str(e)}")
        if g_id in grievance_db:
            grievance_db[g_id]['ai_report'] = f"❌ Processing error: {str(e)}"
            grievance_db[g_id]['url'] = "error"

@app.route("/status_result", methods=['GET', 'POST'])
def status_result():
    entered_id = request.values.get('Digits', None)
    resp = VoiceResponse()

    if entered_id in grievance_db:
        status = grievance_db[entered_id]['status']
        resp.say(f"Aapki shikayat ka status hai {status}.", voice='Polly.Aditi', language='en-IN')
    else:
        resp.say("Yeh number nahi mila. Kripya dobara check karein.", voice='Polly.Aditi', language='en-IN')

    return str(resp)

@app.route("/")
def index():
    if 'logged_in' in session:
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/admin")
@app.route("/dashboard")
@login_required
def admin():
    chain_length = len(samvaad_chain.chain) if hasattr(samvaad_chain, 'chain') else 0
    pending_db = {k: v for k, v in grievance_db.items() if v.get('status') == 'Pending'}
    return render_template('admin.html', db=pending_db, chain_len=chain_length, view='dashboard', all_db=grievance_db)

@app.route("/all_grievances")
@login_required
def all_grievances():
    chain_length = len(samvaad_chain.chain) if hasattr(samvaad_chain, 'chain') else 0
    return render_template('admin.html', db=grievance_db, chain_len=chain_length, view='all', all_db=grievance_db)

@app.route("/analytics")
@login_required
def analytics():
    """Generates analytics dashboard with category breakdown"""
    chain_length = len(samvaad_chain.chain) if hasattr(samvaad_chain, 'chain') else 0
    
    total = len(grievance_db)
    pending = sum(1 for v in grievance_db.values() if v.get('status') == 'Pending')
    resolved = sum(1 for v in grievance_db.values() if v.get('status') == 'Resolved')
    
    # extract categories from AI reports
    categories = {}
    for v in grievance_db.values():
        report = v.get('ai_report', '')
        if 'Category:' in report:
            cat_line = [line for line in report.split('\n') if 'Category:' in line]
            if cat_line:
                cat_text = cat_line[0].split('Category:')[1].strip()
                if '[' in cat_text and ']' in cat_text:
                    cat = cat_text.split('[')[1].split(']')[0].strip()
                else:
                    cat = cat_text.split()[0].strip() if cat_text else 'Unknown'
                categories[cat] = categories.get(cat, 0) + 1
        else:
            categories['Unknown'] = categories.get('Unknown', 0) + 1
    
    analytics_data = {
        'total': total,
        'pending': pending,
        'resolved': resolved,
        'categories': categories
    }
    
    return render_template('admin.html', db=grievance_db, chain_len=chain_length, view='analytics', analytics=analytics_data, all_db=grievance_db)

@app.route("/update_status", methods=['POST'])
@login_required
def update_status():
    """Updates grievance status and sends SMS if resolved"""
    g_id = request.form.get('g_id')
    new_status = request.form.get('new_status')
    
    if g_id in grievance_db:
        old_status = grievance_db[g_id]['status']
        grievance_db[g_id]['status'] = new_status
        
        # send SMS if status changed to Resolved
        if new_status == 'Resolved' and old_status != 'Resolved':
            phone_number = grievance_db[g_id].get('phone')
            if phone_number:
                send_resolution_sms(phone_number, g_id)
    
    return redirect(url_for('admin'))

@app.route("/verify_blockchain")
def verify_blockchain():
    search_id = request.args.get('id', None)
    report = samvaad_chain.get_verification_report()
    
    search_result = None
    if search_id:
        search_result = samvaad_chain.find_grievance_in_chain(search_id)
        if search_result.get('found'):
            if search_id in grievance_db:
                search_result['grievance'] = grievance_db[search_id]
    
    return render_template('verify.html', report=report, search_id=search_id, search_result=search_result)

@app.route("/api/verify", methods=['GET'])
def api_verify():
    report = samvaad_chain.get_verification_report()
    return jsonify(report)

@app.route("/verify_grievance/<grievance_id>")
def verify_grievance(grievance_id):
    result = samvaad_chain.find_grievance_in_chain(grievance_id)
    return jsonify(result)

@app.route("/api/check_analysis/<g_id>")
def check_analysis(g_id):
    if g_id in grievance_db:
        grievance = grievance_db[g_id]
        is_pending = '🔄' in grievance['ai_report'] or 'Progress' in grievance['ai_report']
        return jsonify({
            'status': 'found',
            'pending': is_pending,
            'ai_report': grievance['ai_report'],
            'hash': grievance['hash'],
            'url': grievance['url']
        })
    return jsonify({'status': 'not_found'}), 404

@app.route("/diagnostic")
def diagnostic():
    import os
    return jsonify({
        'status': 'ok',
        'grievances_count': len(grievance_db),
        'blockchain_length': len(samvaad_chain.chain) if hasattr(samvaad_chain, 'chain') else 0,
        'script_exists': os.path.exists('static/script.js'),
        'script_size': os.path.getsize('static/script.js') if os.path.exists('static/script.js') else 0,
        'recordings_exist': os.path.exists('static/recordings'),
        'recordings_count': len(os.listdir('static/recordings')) if os.path.exists('static/recordings') else 0
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)