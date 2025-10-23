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

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from urllib.parse import urlparse
from authlib.integrations.flask_client import OAuth
import secrets
import logging
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CSRF
app.config['SECRET_KEY'] = 'Ry4&tuKqP@9lx#sF0wv2pG5$zLp0*H!'
csrf = CSRFProtect(app)

# Konfigurasi OAuth - GUNAKAN CREDENTIALS ASLI DARI GOOGLE
app.config['GOOGLE_CLIENT_ID'] = '1070506598093-fh66ogvcqvsiv2tfct7a8cs98jm6ahhv.apps.googleusercontent.com'  # GANTI dengan Client ID asli
app.config['GOOGLE_CLIENT_SECRET'] = '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'  # GANTI dengan Client Secret asli

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

# Daftar email yang diizinkan 
ALLOWED_EMAILS = ['arimuzakir@gmail.com', 'swalidaien@gmail.com']  # Ganti dengan email yang diizinkan

class MyForm(FlaskForm):
    submit = SubmitField('Submit')

@app.route('/login')
def login():
    form = MyForm()
    error = request.args.get('error')
    return render_template("login.html", form=form, error=error)

@app.route('/google-login')
def google_login():
    try:
        # Generate state untuk mencegah CSRF
        session['oauth_state'] = secrets.token_urlsafe(16)
        redirect_uri = url_for('google_callback', _external=True)
        logger.info(f"Starting Google OAuth with redirect: {redirect_uri}")
        
        # Validasi redirect URI
        allowed_redirects = [
            'http://localhost:5000/google-callback',
            'http://127.0.0.1:5000/google-callback'
        ]
        
        if redirect_uri not in allowed_redirects:
            logger.error(f"Invalid redirect URI: {redirect_uri}")
            return redirect(url_for('login', error="Konfigurasi redirect URI tidak valid"))
        
        # Buat authorization URL manual
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?response_type=code"
            f"&client_id={app.config['GOOGLE_CLIENT_ID']}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=openid%20email%20profile"
            f"&state={session['oauth_state']}"
            f"&access_type=offline"
            f"&prompt=consent"  # Tambahkan ini untuk memastikan consent screen muncul
        )
        
        logger.info(f"Redirecting to Google OAuth: {auth_url}")
        return redirect(auth_url)
    
    except Exception as e:
        logger.error(f"Error in google_login: {e}")
        return redirect(url_for('login', error="Terjadi kesalahan saat mengarahkan ke Google"))

@app.route('/google-callback')
def google_callback():
    try:
        # Cek error dari Google
        error = request.args.get('error')
        if error:
            error_description = request.args.get('error_description', '')
            logger.error(f"Google OAuth error: {error} - {error_description}")
            return redirect(url_for('login', error=f"Google login gagal: {error_description}"))
        
        # Validasi state
        state = request.args.get('state')
        if state != session.get('oauth_state'):
            logger.error(f"State mismatch: expected {session.get('oauth_state')}, got {state}")
            return redirect(url_for('login', error="Sesi tidak valid, silakan coba lagi"))
        
        # Dapatkan authorization code
        code = request.args.get('code')
        if not code:
            logger.error("No authorization code received")
            return redirect(url_for('login', error="Kode otorisasi tidak ditemukan"))
        
        # Tukar code dengan access token
        redirect_uri = url_for('google_callback', _external=True)
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': app.config['GOOGLE_CLIENT_ID'],
            'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        logger.info("Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            return redirect(url_for('login', error="Gagal mendapatkan access token dari Google"))
        
        token_json = token_response.json()
        
        if 'error' in token_json:
            logger.error(f"Token error: {token_json['error']}")
            return redirect(url_for('login', error=f"Error token: {token_json['error']}"))
        
        access_token = token_json.get('access_token')
        
        if not access_token:
            logger.error("No access token received")
            return redirect(url_for('login', error="Access token tidak diterima"))
        
        # Dapatkan user info dari Google API
        user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        
        if user_response.status_code != 200:
            logger.error(f"User info request failed: {user_response.status_code}")
            return redirect(url_for('login', error="Gagal mendapatkan informasi user dari Google"))
        
        user_info = user_response.json()
        
        if user_info and 'email' in user_info:
            session['user'] = user_info
            email = user_info['email']
            
            # ✅ HAPUS PENGEcekan ALLOWED_EMAILS - SEMUA EMAIL DIIZINKAN
            # Langsung login tanpa cek email
            session["iHateSession"] = ".78gua$higutya56sd7a8syugt43234]`"
            session['logged_in'] = True
            session['email'] = email
            session['name'] = user_info.get('name', 'User')
            session['picture'] = user_info.get('picture', '')
            logger.info(f"User {email} logged in successfully via Google")
            return redirect(url_for('dashboard'))
        else:
            logger.error("No email in user info")
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
            return render_template("admin/dash.html", form=form, hasil=hasil, user_name=user_name, user_email=user_email, user_picture=user_picture)
    
    return redirect(url_for("login"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/dash-tambah', methods=["POST"])
def tambahDash():
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit() and session.get('logged_in'):
            
            # Variabel Form
            slang = request.form['slang']
            normal = request.form['normal']

            slangList = slang.split(",")
            normalList = normal.split(",")
            
            with open("data/mentahan/kamusnormalisasi.csv", mode='a', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)

                for item1, item2 in zip(slangList, normalList):
                    csv_writer.writerow([item1, item2])
    return redirect(url_for("dashboard", hasil=1))

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

            # Get Form
            fileKirim = request.files['fileKirim']
            filename = fileKirim.filename
            
            if filename.endswith('.csv'):
                filepath = os.path.join('data/uploads/', filename)
                if os.path.exists(filepath):
                # Generate a new unique filename
                    counter = 1
                    name, extension = os.path.splitext(filename)
                    new_filename = f"{name}_{counter}{extension}"

                    while os.path.exists(os.path.join('data/uploads/', new_filename)):
                        counter += 1
                        new_filename = f"{name}_{counter}{extension}"

                    filepath = os.path.join('data/uploads/', new_filename)

                fileKirim.save(filepath)

                return redirect(url_for('kirimData', sukses=1, form=form))
            else:
                return redirect(url_for('kirimData', sukses=0, form=form))
    else:
        sukses = request.args.get('sukses')
        return render_template("kirim-data.html", sukses=sukses, form=form)

@app.route('/cek', methods=['GET'])
def cekCek():
    process = psutil.Process() #initiate only once
    memory_info = process.memory_info()
    rss = memory_info.rss
    rss_mb = rss / (1024 * 1024)
    return f"Memory usage: {rss_mb} MB"

@app.route('/cek-sentimen-analysis', methods=['POST', 'GET'])
def cekSentimenAnalysis():

    form = MyForm()
    if request.method == 'POST':

        if form.validate_on_submit():
            # POST Param dari form
            start = time.time()
            kalimatTweet = request.form['tweet']
            kategori = request.form['kategori']
            model = request.form['model']
            perluasan = request.form['perluasan']
            perluasanKalimat = request.form.get('perluasanKalimat')

            if kategori == "":
                kategori = "5"

            if model == "":
                model = "CNN"
            
            if perluasan == "":
                perluasan = "1"

            if perluasanKalimat == "on":
                perluasanKalimat = "1"
            else:
                perluasanKalimat = "0"

            try:
                # normalisasi kata
                tweet = casefolding(kalimatTweet)
                tweet = hapusKata(tweet)
                tweet = normalizeText(tweet)
                normalTeks = tweet
                
                # augmentation
                kalimatPerbaikan = tweet
                if perluasanKalimat=="1":
                    tweet = semanticExpantion(tweet)
                    kalimatPerbaikan = tweet
                
                # Stemming
                tweet = stemmer.stem(tweet)
                
                # embedding
                tweet = paddedSensor(tweet)

                # Prediksi
                tweet_result = prediksi(tweet, model, perluasan)

                # Persentase
                proba = []
                for i in tweet_result[1]:
                    percentage = i*100
                    proba.append(percentage)

                end = time.time()
                totalTime = int(end-start)

                return render_template("main.html", 
                                    hasil='1', 
                                    sentimen=kategori, 
                                    data=tweet_result[0], 
                                    oldTweet=kalimatTweet, 
                                    form=form, 
                                    proba=proba, 
                                    kalimatTweet=kalimatTweet, 
                                    kalimatPerbaikan=kalimatPerbaikan, 
                                    totalTime=totalTime, 
                                    model=model, 
                                    perluasan=perluasan, 
                                    perluasanKalimat=perluasanKalimat, 
                                    normalTeks=normalTeks)
            
            except Exception as e:
                logger.error(f"Error in sentiment analysis: {e}")
                # Return error page atau redirect dengan pesan error
                return render_template("main.html", 
                                    hasil='0', 
                                    error="Terjadi kesalahan dalam analisis sentimen",
                                    form=form,
                                    kalimatTweet=kalimatTweet)
        
    return redirect(url_for('index'))

@app.route('/cek-batch', methods=["GET", "POST"])
def cekBatch():
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            fileKirim = request.files['batchSentimen']
            model = request.form['model']
            perluasan = request.form['perluasan']
            perluasanKalimat = "0"

            if model == "":
                model = "CNN"

            if perluasan == "":
                perluasan = "1"

            filename = fileKirim.filename

            if filename.endswith('.csv'):
                try:
                    # Read CSV file
                    file_content = fileKirim.read().decode('utf-8')
                    dataBatch = list(csv.reader(file_content.splitlines()))
                    
                    # Convert ke List Biasa
                    data = []
                    for i in range(1, len(dataBatch)):
                        if len(dataBatch[i]) > 0:
                            data.append(dataBatch[i][0])
                    
                    # Create Pandas Dataframe
                    dfDownload = pd.DataFrame()
                    dfDownload['tweet'] = data
                    length = len(dfDownload['tweet'])
                    
                    # Inisialisasi semua kolom
                    dfDownload['Non_HS'] = 0
                    dfDownload['HS'] = 0
                    dfDownload['Abusive'] = 0
                    dfDownload['HS_individual'] = 0
                    dfDownload['HS_Group'] = 0
                    dfDownload['HS_Religion'] = 0
                    dfDownload['HS_Race'] = 0
                    dfDownload['HS_Physical'] = 0
                    dfDownload['HS_Gender'] = 0
                    dfDownload['HS_Other'] = 0
                    dfDownload['HS_Weak'] = 0
                    dfDownload['HS_Moderate'] = 0
                    dfDownload['HS_Strong'] = 0

                    dfDownload['Non_HS_Persen'] = 0.0
                    dfDownload['HS_Persen'] = 0.0
                    dfDownload['Abusive_Persen'] = 0.0
                    dfDownload['HS_individual_Persen'] = 0.0
                    dfDownload['HS_Group_Persen'] = 0.0
                    dfDownload['HS_Religion_Persen'] = 0.0
                    dfDownload['HS_Race_Persen'] = 0.0
                    dfDownload['HS_Physical_Persen'] = 0.0
                    dfDownload['HS_Gender_Persen'] = 0.0
                    dfDownload['HS_Other_Persen'] = 0.0
                    dfDownload['HS_Weak_Persen'] = 0.0
                    dfDownload['HS_Moderate_Persen'] = 0.0
                    dfDownload['HS_Strong_Persen'] = 0.0

                    dfDownload['normalize'] = ""

                    # Process data (maksimal 50 untuk testing)
                    number = 0
                    for kalimatTweet in data:
                        if number >= 50:  # Batasi untuk testing
                            break
                            
                        try:
                            # normalisasi kata
                            tweet = casefolding(kalimatTweet)
                            tweet = hapusKata(tweet)
                            tweet = normalizeText(tweet)
                            normalTeks = tweet

                            if perluasanKalimat=="1":
                                tweet = semanticExpantion(tweet)
                            
                            # stemming
                            tweet = stemmer.stem(tweet)
                            # embedding
                            tweet = paddedSensor(tweet)

                            # Prediksi
                            tweet_result = prediksi(tweet, model, perluasan)

                            # Update dataframe dengan hasil prediksi
                            if tweet_result and len(tweet_result) >= 2:
                                predictions_str = tweet_result[0]
                                probabilities = tweet_result[1]
                                
                                # Convert string predictions to individual columns
                                if predictions_str and len(predictions_str) > 0:
                                    pred_str = predictions_str[0] if isinstance(predictions_str, list) else predictions_str
                                    
                                    # Update binary predictions berdasarkan posisi karakter
                                    if len(pred_str) >= 13:  # Pastikan panjang string cukup
                                        dfDownload.at[number, 'Non_HS'] = int(pred_str[0])
                                        dfDownload.at[number, 'HS'] = int(pred_str[1])
                                        dfDownload.at[number, 'Abusive'] = int(pred_str[2])
                                        dfDownload.at[number, 'HS_individual'] = int(pred_str[3])
                                        dfDownload.at[number, 'HS_Group'] = int(pred_str[4])
                                        dfDownload.at[number, 'HS_Religion'] = int(pred_str[5])
                                        dfDownload.at[number, 'HS_Race'] = int(pred_str[6])
                                        dfDownload.at[number, 'HS_Physical'] = int(pred_str[7])
                                        dfDownload.at[number, 'HS_Gender'] = int(pred_str[8])
                                        dfDownload.at[number, 'HS_Other'] = int(pred_str[9])
                                        dfDownload.at[number, 'HS_Weak'] = int(pred_str[10])
                                        dfDownload.at[number, 'HS_Moderate'] = int(pred_str[11])
                                        dfDownload.at[number, 'HS_Strong'] = int(pred_str[12])
                                
                                # Update probabilities
                                if probabilities is not None and len(probabilities) > number:
                                    prob_row = probabilities[number]
                                    if len(prob_row) >= 13:
                                        dfDownload.at[number, 'Non_HS_Persen'] = float(prob_row[0]) * 100
                                        dfDownload.at[number, 'HS_Persen'] = float(prob_row[1]) * 100
                                        dfDownload.at[number, 'Abusive_Persen'] = float(prob_row[2]) * 100
                                        dfDownload.at[number, 'HS_individual_Persen'] = float(prob_row[3]) * 100
                                        dfDownload.at[number, 'HS_Group_Persen'] = float(prob_row[4]) * 100
                                        dfDownload.at[number, 'HS_Religion_Persen'] = float(prob_row[5]) * 100
                                        dfDownload.at[number, 'HS_Race_Persen'] = float(prob_row[6]) * 100
                                        dfDownload.at[number, 'HS_Physical_Persen'] = float(prob_row[7]) * 100
                                        dfDownload.at[number, 'HS_Gender_Persen'] = float(prob_row[8]) * 100
                                        dfDownload.at[number, 'HS_Other_Persen'] = float(prob_row[9]) * 100
                                        dfDownload.at[number, 'HS_Weak_Persen'] = float(prob_row[10]) * 100
                                        dfDownload.at[number, 'HS_Moderate_Persen'] = float(prob_row[11]) * 100
                                        dfDownload.at[number, 'HS_Strong_Persen'] = float(prob_row[12]) * 100
                                
                                dfDownload.at[number, 'normalize'] = normalTeks
                                
                        except Exception as e:
                            logger.error(f"Error processing tweet {number}: {e}")
                            # Set default values jika error
                            dfDownload.at[number, 'normalize'] = f"Error: {str(e)}"
                        
                        number += 1

                    # Convert dataframe to dictionary untuk template
                    dictData = dfDownload.to_dict(orient='list')
                    
                    # Simpan hasil ke CSV untuk download
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
    else:
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