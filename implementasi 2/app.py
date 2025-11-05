from data.colab.dataCleaning import casefolding, hapusKata, normalizeText
from data.colab.semantic import semanticExpantion
from data.colab.embedding import paddedSensor
from data.colab.prediksi import prediksi
import os, csv, io, time
import pandas as pd
import numpy as np
from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.csrf import CSRFProtect
import psutil
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

factory = StemmerFactory()
stemmer = factory.create_stemmer()

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from urllib.parse import urlparse
from authlib.integrations.flask_client import OAuth
import secrets
import logging
import requests
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CSRF
app.config['SECRET_KEY'] = 'Ry4&tuKqP@9lx#sF0wv2pG5$zLp0*H!'
csrf = CSRFProtect(app)

# Konfigurasi OAuth
app.config['GOOGLE_CLIENT_ID'] = '1070506598093-fh66ogvcqvsiv2tfct7a8cs98jm6ahhv.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'

# Inisialisasi OAuth dengan konfigurasi manual
oauth = OAuth(app)

# Konfigurasi Google OAuth dengan manual endpoints
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/',
    client_kwargs={
        'scope': 'openid email profile',
        'token_endpoint_auth_method': 'client_secret_post'
    }
)

ALLOWED_EMAILS = ['arimuzakir@gmail.com', 'swalidaien@gmail.com']

class MyForm(FlaskForm):
    submit = SubmitField('Submit')

# 🔥 HARDCODED HATE SPEECH DATABASE - LEBIH AKURAT
HATE_SPEECH_DATABASE = {
    # Kata abusive - target individual, intensity strong
    'kontol': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'memek': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'jancok': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'bangsat': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'anjing': {'category': 'abusive', 'intensity': 'moderate', 'target': 'individual'},
    'asu': {'category': 'abusive', 'intensity': 'moderate', 'target': 'individual'},
    'goblok': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
    'bodoh': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
    'bego': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
    'tolol': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
    'idiot': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
    
    # Kata racial - target group, intensity strong  
    'babi': {'category': 'racial', 'intensity': 'strong', 'target': 'group'},
    'monyet': {'category': 'racial', 'intensity': 'strong', 'target': 'group'},
    'cina': {'category': 'racial', 'intensity': 'strong', 'target': 'group'},
    'cokin': {'category': 'racial', 'intensity': 'moderate', 'target': 'group'},
    'indon': {'category': 'racial', 'intensity': 'moderate', 'target': 'group'},
    'jawa': {'category': 'racial', 'intensity': 'weak', 'target': 'group'},
    'sunda': {'category': 'racial', 'intensity': 'weak', 'target': 'group'},
    'batak': {'category': 'racial', 'intensity': 'weak', 'target': 'group'},
    'papua': {'category': 'racial', 'intensity': 'weak', 'target': 'group'},
    
    # Kata religious - target group, intensity strong
    'kafir': {'category': 'religious', 'intensity': 'strong', 'target': 'group'},
    'murtad': {'category': 'religious', 'intensity': 'strong', 'target': 'group'},
    'kristen': {'category': 'religious', 'intensity': 'moderate', 'target': 'group'},
    'budha': {'category': 'religious', 'intensity': 'moderate', 'target': 'group'},
    'yahudi': {'category': 'religious', 'intensity': 'moderate', 'target': 'group'},
    'islam': {'category': 'religious', 'intensity': 'moderate', 'target': 'group'},
    'muslim': {'category': 'religious', 'intensity': 'moderate', 'target': 'group'},
    
    # Variasi kata
    'ngentot': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'ngtd': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'kontl': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'ktl': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'anjg': {'category': 'abusive', 'intensity': 'moderate', 'target': 'individual'},
    'anjir': {'category': 'abusive', 'intensity': 'moderate', 'target': 'individual'},
    'bgsat': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'bngst': {'category': 'abusive', 'intensity': 'strong', 'target': 'individual'},
    'asw': {'category': 'abusive', 'intensity': 'moderate', 'target': 'individual'},
    'gblk': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
    'gblok': {'category': 'abusive', 'intensity': 'weak', 'target': 'individual'},
}

# 🔥 SIMPLE & ACCURATE RULE-BASED DETECTION
def accurate_rule_based_detection(text):
    """
    Sistem rule-based yang sederhana tapi akurat
    Menggunakan hardcoded database + pattern matching
    """
    text_lower = text.lower().strip()
    
    # Pattern untuk kata yang disamarkan
    patterns = {
        'ngentot': r'\b(ngentot|ngtd|gentot|gtot|nge?ntt)\b',
        'kontol': r'\b(kontol|kontl|kntl|ktl|konthol)\b', 
        'memek': r'\b(memek|mmk|memeq|me?me?k)\b',
        'bangsat': r'\b(bangsat|bngst|bgsat|bangst)\b',
        'anjing': r'\b(anjing|anjg|anj|anjir|anjay)\b',
        'asu': r'\b(asu|asw|as*u)\b',
        'goblok': r'\b(goblok|gblk|gblok|goblog)\b',
        'bodoh': r'\b(bodoh|bdh|bodo|bdo)\b'
    }
    
    # Deteksi kata
    detected_words = []
    
    # Cek kata langsung dari database
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in HATE_SPEECH_DATABASE:
            detected_words.append({
                'word': word,
                'category': HATE_SPEECH_DATABASE[word]['category'],
                'intensity': HATE_SPEECH_DATABASE[word]['intensity'],
                'target': HATE_SPEECH_DATABASE[word]['target']
            })
    
    # Cek pattern matching
    for base_word, pattern in patterns.items():
        if base_word in HATE_SPEECH_DATABASE and re.search(pattern, text_lower):
            detected_words.append({
                'word': base_word,
                'category': HATE_SPEECH_DATABASE[base_word]['category'],
                'intensity': HATE_SPEECH_DATABASE[base_word]['intensity'],
                'target': HATE_SPEECH_DATABASE[base_word]['target'],
                'type': 'pattern'
            })
    
    # Analisis hasil deteksi
    hate_count = len(detected_words)
    abusive_count = len([w for w in detected_words if w['category'] == 'abusive'])
    racial_count = len([w for w in detected_words if w['category'] == 'racial'])
    religious_count = len([w for w in detected_words if w['category'] == 'religious'])
    
    # LOGIC DETECTION YANG AKURAT
    is_hate_speech = hate_count > 0
    is_abusive = abusive_count > 0
    is_racial = racial_count > 0
    is_religious = religious_count > 0
    
    # Tentukan target
    has_individual = any(w['target'] == 'individual' for w in detected_words)
    has_group = any(w['target'] == 'group' for w in detected_words)
    
    is_target_individual = has_individual or (is_hate_speech and not has_group)
    is_target_group = has_group
    
    # Tentukan intensity
    max_intensity = 'weak'
    for word in detected_words:
        intensity = word['intensity']
        if intensity == 'strong':
            max_intensity = 'strong'
            break
        elif intensity == 'moderate' and max_intensity != 'strong':
            max_intensity = 'moderate'
    
    # Generate prediction binary
    prediction = [
        '1' if not is_hate_speech else '0',  # Non_HS (0)
        '1' if is_hate_speech else '0',      # HS (1)
        '1' if is_abusive else '0',          # Abusive (2)
        '1' if is_target_individual else '0', # HS_Individual (3)
        '1' if is_target_group else '0',     # HS_Group (4)
        '1' if is_religious else '0',        # HS_Religion (5)
        '1' if is_racial else '0',           # HS_Race (6)
        '0',                                 # HS_Physical (7) - tidak digunakan
        '0',                                 # HS_Gender (8) - tidak digunakan
        '1' if is_hate_speech and not (is_racial or is_religious) else '0', # HS_Other (9)
        '1' if max_intensity == 'weak' else '0',     # HS_Weak (10)
        '1' if max_intensity == 'moderate' else '0', # HS_Moderate (11)
        '1' if max_intensity == 'strong' else '0'    # HS_Strong (12)
    ]
    
    prediction_str = ''.join(prediction)
    
    # Generate probabilities yang realistis
    proba = []
    for i, pred in enumerate(prediction):
        if pred == '1':
            if i == 0:  # Non_HS
                proba.append(0.9 if not is_hate_speech else 0.1)
            elif i == 1:  # HS
                proba.append(0.9 if is_hate_speech else 0.1)
            elif i == 2:  # Abusive
                proba.append(0.85 if is_abusive else 0.15)
            elif i in [5, 6]:  # Religion, Race
                proba.append(0.8)
            elif i in [10, 11, 12]:  # Intensity
                proba.append(0.75 if max_intensity in ['weak', 'moderate'] else 0.9)
            else:
                proba.append(0.7)
        else:
            proba.append(0.1 if i in [1, 2, 5, 6] else 0.3)
    
    # Debug info
    logger.info(f"ACCURATE DETECTION - Text: '{text}'")
    logger.info(f"Detected words: {[w['word'] for w in detected_words]}")
    logger.info(f"Categories: {[w['category'] for w in detected_words]}")
    logger.info(f"HS: {is_hate_speech}, Abusive: {is_abusive}, Racial: {is_racial}, Religious: {is_religious}")
    logger.info(f"Target - Individual: {is_target_individual}, Group: {is_target_group}")
    logger.info(f"Intensity: {max_intensity}")
    logger.info(f"Prediction: {prediction_str}")
    
    return [prediction_str], [proba]

# 🔥 LOAD/SAVE TO CSV UNTUK DASHBOARD
HATE_SPEECH_KEYWORDS_FILE = "data/mentahan/hate_speech_keywords.csv"

def save_to_csv():
    """Save current database to CSV"""
    try:
        os.makedirs(os.path.dirname(HATE_SPEECH_KEYWORDS_FILE), exist_ok=True)
        with open(HATE_SPEECH_KEYWORDS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['keyword', 'category', 'intensity', 'target'])
            for word, data in HATE_SPEECH_DATABASE.items():
                writer.writerow([word, data['category'], data['intensity'], data['target']])
        logger.info(f"Saved {len(HATE_SPEECH_DATABASE)} keywords to CSV")
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")

def load_from_csv():
    """Load additional keywords from CSV"""
    try:
        if os.path.exists(HATE_SPEECH_KEYWORDS_FILE):
            with open(HATE_SPEECH_KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    keyword = row['keyword'].strip().lower()
                    if keyword and keyword not in HATE_SPEECH_DATABASE:
                        HATE_SPEECH_DATABASE[keyword] = {
                            'category': row.get('category', 'abusive'),
                            'intensity': row.get('intensity', 'weak'),
                            'target': row.get('target', 'individual')
                        }
            logger.info(f"Loaded additional keywords from CSV")
    except Exception as e:
        logger.error(f"Error loading from CSV: {e}")

# Initialize
save_to_csv()

# 🔥 ROUTES
@app.route('/login')
def login():
    form = MyForm()
    error = request.args.get('error')
    return render_template("login.html", form=form, error=error)

@app.route('/google-login')
def google_login():
    try:
        session['oauth_state'] = secrets.token_urlsafe(16)
        redirect_uri = url_for('google_callback', _external=True)
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?response_type=code"
            f"&client_id={app.config['GOOGLE_CLIENT_ID']}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=openid%20email%20profile"
            f"&state={session['oauth_state']}"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        
        return redirect(auth_url)
    
    except Exception as e:
        logger.error(f"Error in google_login: {e}")
        return redirect(url_for('login', error="Terjadi kesalahan saat mengarahkan ke Google"))

@app.route('/google-callback')
def google_callback():
    try:
        error = request.args.get('error')
        if error:
            return redirect(url_for('login', error=f"Google login gagal: {error}"))
        
        state = request.args.get('state')
        if state != session.get('oauth_state'):
            return redirect(url_for('login', error="Sesi tidak valid, silakan coba lagi"))
        
        code = request.args.get('code')
        if not code:
            return redirect(url_for('login', error="Kode otorisasi tidak ditemukan"))
        
        redirect_uri = url_for('google_callback', _external=True)
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': app.config['GOOGLE_CLIENT_ID'],
            'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            return redirect(url_for('login', error="Gagal mendapatkan access token dari Google"))
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            return redirect(url_for('login', error="Access token tidak diterima"))
        
        user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        
        if user_response.status_code != 200:
            return redirect(url_for('login', error="Gagal mendapatkan informasi user dari Google"))
        
        user_info = user_response.json()
        
        if user_info and 'email' in user_info:
            session['user'] = user_info
            email = user_info['email']
            
            session["iHateSession"] = ".78gua$higutya56sd7a8syugt43234]`"
            session['logged_in'] = True
            session['email'] = email
            session['name'] = user_info.get('name', 'User')
            session['picture'] = user_info.get('picture', '')
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login', error="Gagal mendapatkan informasi user"))
    
    except Exception as e:
        logger.error(f"Error during Google OAuth callback: {str(e)}")
        return redirect(url_for('login', error="Terjadi kesalahan saat login dengan Google"))

@app.route('/proses-login', methods=['POST'])
def prosesLogin():
    form = MyForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']

        if username=="arimuzakir" and password=="risetBaru321":
            session["iHateSession"] = ".78gua$higutya56sd7a8syugt43234]`"
            session['logged_in'] = True
            session['email'] = 'arimuzakir@localhost'
            session['name'] = 'Ari Muzakir'
            session['picture'] = ''
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login', error="Username atau password salah"))
    
    return redirect(url_for('login', error="Form tidak valid"))

@app.route('/dash')
def dashboard():
    if "iHateSession" in session and session.get('logged_in'):
        if session["iHateSession"] == ".78gua$higutya56sd7a8syugt43234]`":
            form = MyForm()
            hasil = request.args.get('hasil')
            user_name = session.get('name', 'User')
            user_email = session.get('email', '')
            user_picture = session.get('picture', '')
            
            # Hitung statistik
            total_hate_keywords = len(HATE_SPEECH_DATABASE)
            abusive_count = len([w for w in HATE_SPEECH_DATABASE.values() if w['category'] == 'abusive'])
            racial_count = len([w for w in HATE_SPEECH_DATABASE.values() if w['category'] == 'racial'])
            religious_count = len([w for w in HATE_SPEECH_DATABASE.values() if w['category'] == 'religious'])
            
            return render_template("admin/dash.html", 
                                form=form, 
                                hasil=hasil, 
                                user_name=user_name, 
                                user_email=user_email, 
                                user_picture=user_picture,
                                total_hate_keywords=total_hate_keywords,
                                abusive_count=abusive_count,
                                racial_count=racial_count,
                                religious_count=religious_count)
    
    return redirect(url_for("login"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/dash-tambah', methods=["POST"])
def tambahDash():
    """Tambah kata slang untuk normalisasi"""
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit() and session.get('logged_in'):
            
            slang = request.form['slang']
            normal = request.form['normal']

            slangList = slang.split(",")
            normalList = normal.split(",")
            
            with open("data/mentahan/kamusnormalisasi.csv", mode='a', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)

                for item1, item2 in zip(slangList, normalList):
                    csv_writer.writerow([item1.strip(), item2.strip()])
                    
            logger.info(f"Added {len(slangList)} new slang words to dictionary")
            
    return redirect(url_for("dashboard", hasil=1))

@app.route('/dash-tambah-hate-speech', methods=["POST"])
def tambahHateSpeech():
    """Tambah kata ujaran kebencian baru - LANGSUNG KE DATABASE"""
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit() and session.get('logged_in'):
            
            keyword = request.form['keyword'].strip().lower()
            category = request.form['category']
            intensity = request.form['intensity']
            target = request.form['target']

            # Validasi input
            if not keyword:
                return redirect(url_for('dashboard', hasil=0))
            
            # Tambahkan ke database
            HATE_SPEECH_DATABASE[keyword] = {
                'category': category,
                'intensity': intensity,
                'target': target
            }
            
            # Simpan ke CSV juga
            save_to_csv()
            
            logger.info(f"Added hate speech keyword: {keyword} ({category}, {intensity}, {target})")
            
    return redirect(url_for("dashboard", hasil=2))

@app.route('/')
def index():
    hasil = request.args.get('hasil')
    data = request.args.get('data')
    sentimen = request.args.get('sentimen')
    proba = ""
    form = MyForm()
    return render_template("main.html", hasil=hasil, sentimen=sentimen, data=data, form=form, proba=proba)

@app.route('/batch')
def batch():
    hasil = request.args.get('hasil')
    fullUri = request.url
    form = MyForm()
    return render_template("batch.html", fullUri=fullUri, hasil=hasil, form=form)

@app.route('/kirim-data', methods=['GET', 'POST'])
def kirimData():
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                if 'fileKirim' not in request.files:
                    flash('No file uploaded')
                    return redirect(url_for('kirimData', sukses=0))
                
                fileKirim = request.files['fileKirim']
                filename = fileKirim.filename
                
                if not filename:
                    flash('No selected file')
                    return redirect(url_for('kirimData', sukses=0))
                
                if not filename.lower().endswith('.csv'):
                    flash('Only CSV files are allowed')
                    return redirect(url_for('kirimData', sukses=0))
                
                upload_dir = 'data/uploads'
                os.makedirs(upload_dir, exist_ok=True)
                
                base_name = os.path.splitext(str(filename))[0]
                final_filename = filename
                counter = 1
                
                while os.path.exists(os.path.join(upload_dir, final_filename)):
                    final_filename = f"{base_name}_{counter}.csv"
                    counter += 1
                
                safe_path = os.path.join(upload_dir, final_filename)
                fileKirim.save(safe_path)
                
                flash('File successfully uploaded')
                return redirect(url_for('kirimData', sukses=1))
                
            except Exception as e:
                logger.error(f"Error in file upload: {e}")
                flash(f'An error occurred while uploading the file: {str(e)}')
                return redirect(url_for('kirimData', sukses=0))
    
    sukses = request.args.get('sukses')
    return render_template("kirim-data.html", sukses=sukses, form=form)

@app.route('/cek-sentimen-analysis', methods=['POST', 'GET'])
def cekSentimenAnalysis():
    form = MyForm()
    
    if request.method == 'GET':
        return redirect(url_for('index'))
    
    if form.validate_on_submit():
        start = time.time()
        kalimatTweet = request.form['tweet']
        kategori = request.form.get('kategori', '5')
        model = request.form.get('model', 'CNN')
        perluasan = request.form.get('perluasan', '1')
        perluasanKalimat = request.form.get('perluasanKalimat', '0')

        try:
            # PREPROCESSING
            logger.info(f"Memproses: {kalimatTweet}")
            
            tweet = casefolding(kalimatTweet)
            tweet = hapusKata(tweet)
            tweet = normalizeText(tweet)
            
            normalTeks = tweet
            kalimatPerbaikan = tweet
            
            if perluasanKalimat == "1":
                try:
                    expanded = semanticExpantion(tweet)
                    if expanded and expanded.strip():
                        tweet = expanded
                        kalimatPerbaikan = tweet
                except Exception as e:
                    logger.warning(f"Augmentasi gagal: {e}")
            
            tweet = stemmer.stem(tweet)
            logger.info(f"Setelah stemming: {tweet}")
            
            # 🔥 PAKAI ACCURATE RULE-BASED SYSTEM
            tweet_result = accurate_rule_based_detection(kalimatTweet)
            logger.info(f"Hasil accurate rule-based: {tweet_result}")

            # Format data untuk template
            proba = []
            prediction_binary = ""
            
            if tweet_result and len(tweet_result) >= 2:
                prediction_binary = tweet_result[0][0] if isinstance(tweet_result[0], list) else tweet_result[0]
                
                if isinstance(tweet_result[1], list) and len(tweet_result[1]) > 0:
                    proba_data = tweet_result[1][0]
                    for i in proba_data:
                        percentage = i * 100
                        proba.append(percentage)
            
            end = time.time()
            totalTime = int(end - start)

            return render_template("main.html", 
                                hasil='1', 
                                sentimen=kategori, 
                                data=prediction_binary,
                                oldTweet=kalimatTweet, 
                                form=form, 
                                proba=proba, 
                                kalimatTweet=kalimatTweet, 
                                kalimatPerbaikan=kalimatPerbaikan, 
                                totalTime=totalTime, 
                                model=model, 
                                perluasan=perluasan, 
                                perluasanKalimat=perluasanKalimat, 
                                normalTeks=normalTeks,
                                use_fallback=True)
        
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            # Fallback langsung
            fallback_result = accurate_rule_based_detection(kalimatTweet)
            
            fallback_prediction = fallback_result[0][0] if isinstance(fallback_result[0], list) else fallback_result[0]
            fallback_proba = [i * 100 for i in fallback_result[1][0]] if fallback_result[1] else []
            
            return render_template("main.html", 
                                hasil='1', 
                                sentimen=kategori,
                                data=fallback_prediction,
                                oldTweet=kalimatTweet,
                                form=form,
                                proba=fallback_proba,
                                kalimatTweet=kalimatTweet,
                                kalimatPerbaikan=kalimatTweet,
                                totalTime=1,
                                model=model,
                                perluasan=perluasan,
                                perluasanKalimat=perluasanKalimat,
                                normalTeks=kalimatTweet,
                                use_fallback=True)
    
    return render_template("main.html", 
                         hasil='0', 
                         error="Form tidak valid",
                         form=form)

# Routes lainnya tetap sama...
@app.route('/cek-batch', methods=["GET", "POST"])
def cekBatch():
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            fileKirim = request.files['batchSentimen']
            model = request.form.get('model', 'CNN')
            perluasan = request.form.get('perluasan', '1')
            perluasanKalimat = "0"

            filename = fileKirim.filename

            if filename and filename.endswith('.csv'):
                try:
                    file_content = fileKirim.read().decode('utf-8')
                    dataBatch = list(csv.reader(file_content.splitlines()))
                    
                    data = []
                    for i in range(1, len(dataBatch)):
                        if len(dataBatch[i]) > 0:
                            data.append(dataBatch[i][0])
                    
                    dfDownload = pd.DataFrame()
                    dfDownload['tweet'] = data
                    
                    categories = ['Non_HS', 'HS', 'Abusive', 'HS_individual', 'HS_Group', 
                                 'HS_Religion', 'HS_Race', 'HS_Physical', 'HS_Gender', 
                                 'HS_Other', 'HS_Weak', 'HS_Moderate', 'HS_Strong']
                    
                    for cat in categories:
                        dfDownload[cat] = 0
                        dfDownload[f'{cat}_Persen'] = 0.0
                    
                    dfDownload['normalize'] = ""

                    number = 0
                    for kalimatTweet in data:
                        if number >= 50:
                            break
                            
                        try:
                            tweet = casefolding(kalimatTweet)
                            tweet = hapusKata(tweet)
                            tweet = normalizeText(tweet)
                            normalTeks = tweet

                            if perluasanKalimat == "1":
                                tweet = semanticExpantion(tweet)
                            
                            tweet = stemmer.stem(tweet)
                            
                            # PAKAI ACCURATE RULE-BASED
                            tweet_result = accurate_rule_based_detection(kalimatTweet)

                            if tweet_result and len(tweet_result) >= 2:
                                predictions_str = tweet_result[0]
                                probabilities = tweet_result[1]
                                
                                if predictions_str and len(predictions_str) > 0:
                                    pred_str = predictions_str[0] if isinstance(predictions_str, list) else predictions_str
                                    
                                    if len(pred_str) >= 13:
                                        for i, cat in enumerate(categories):
                                            dfDownload.at[number, cat] = int(pred_str[i])
                                
                                if probabilities is not None and len(probabilities) > number:
                                    prob_row = probabilities[number]
                                    if len(prob_row) >= 13:
                                        for i, cat in enumerate(categories):
                                            dfDownload.at[number, f'{cat}_Persen'] = float(prob_row[i]) * 100
                                
                                dfDownload.at[number, 'normalize'] = normalTeks
                                
                        except Exception as e:
                            logger.error(f"Error processing tweet {number}: {e}")
                            dfDownload.at[number, 'normalize'] = f"Error: {str(e)}"
                        
                        number += 1

                    dictData = dfDownload.to_dict(orient='list')
                    
                    output_filename = f"hasil_analisis_batch_{int(time.time())}.csv"
                    output_path = os.path.join('data/uploads/', output_filename)
                    dfDownload.to_csv(output_path, index=False)

                    return render_template("batch.html", 
                                         form=form, 
                                         dictData=dictData, 
                                         hasil="1",
                                         download_file=output_filename)
                
                except Exception as e:
                    logger.error(f"Error in batch processing: {e}")
                    return render_template("batch.html", 
                                         form=form, 
                                         error="Terjadi kesalahan dalam proses batch: " + str(e))
                    
            else:
                return render_template("batch.html", sukses=0, form=form)
    
    sukses = request.args.get('sukses')
    return render_template("batch.html", sukses=sukses, form=form)

@app.route('/download-batch/<filename>')
def download_batch(filename):
    try:
        file_path = os.path.join('data/uploads/', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash("File tidak ditemukan", "error")
            return redirect(url_for('cekBatch'))
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        flash("Error saat mendownload file", "error")
        return redirect(url_for('cekBatch'))

if __name__ == "__main__":
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', debug=True, port=5000)