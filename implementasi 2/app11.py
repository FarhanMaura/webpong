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

from flask import Flask, render_template, request, redirect, url_for, session
from urllib.parse import urlparse

app = Flask(__name__)

# CSRF
app.config['SECRET_KEY'] = 'Ry4&tuKqP@9lx#sF0wv2pG5$zLp0*H!'
csrf = CSRFProtect(app)

class MyForm(FlaskForm):
    submit = SubmitField('Submit')

@app.route('/login')
def login():
    form = MyForm()
    return render_template("login.html", form=form)

@app.route('/proses-login', methods=['POST'])
def prosesLogin():
    form = MyForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']

        if username=="arimuzakir" and password=="risetBaru321":
            session["iHateSession"] = ".78gua$higutya56sd7a8syugt43234]`"
            return redirect(url_for('dashboard'))
    
    return redirect(url_for('login'))
        

@app.route('/dash')
def dashboard():
    if "iHateSession" in session:
        if session["iHateSession"] == ".78gua$higutya56sd7a8syugt43234]`":
            form = MyForm()
            hasil = request.args.get('hasil')
            return render_template("admin/dash.html", form=form, hasil=hasil)
    
    return redirect(url_for("login"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))
    
@app.route('/dash-tambah', methods=["POST"])
def tambahDash():
    form = MyForm()

    if request.method == 'POST':

        if form.validate_on_submit():
            
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

            # normalisasi kata
            tweet = casefolding(kalimatTweet)
            tweet = hapusKata(tweet)
            tweet = normalizeText(tweet)
            normalTeks = tweet
            # augmentation
            kalimatPerbaikan = tweet
            if perluasanKalimat=="1":
                # tweet = backTranslate(tweet, target_language='fr')
                # tweet = backTranslate(tweet, target_language='en')
                # tweet = backTranslate(tweet, target_language='id')

                # semantic
                tweet = semanticExpantion(tweet)

                # Kalimat Perbaikan
                kalimatPerbaikan = tweet
            
            # Stemming
            tweet = stemmer.stem(tweet)
            # embedding
            tweet = paddedSensor(tweet)

            # Prediksi
            tweet = prediksi(tweet, model, perluasan)

            # Persentase
            proba = []
            for i in tweet[1]:
                percentage = i*100
                proba.append(percentage)

            end = time.time()
            totalTime = int(end-start)

            return render_template("main.html", hasil='1', sentimen=kategori, data=tweet[0], oldTweet=kalimatTweet, form=form, proba=proba, kalimatTweet=kalimatTweet, kalimatPerbaikan=kalimatPerbaikan, totalTime=totalTime, model=model, perluasan=perluasan, perluasanKalimat=perluasanKalimat, normalTeks = normalTeks)
        
    return redirect(url_for('index'))

@app.route('/cek-batch', methods=["GET", "POST"])
def cekBatch():
    form = MyForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            fileKirim = request.files['batchSentimen']
            model = request.form['model']
            perluasan = request.form['perluasan']
            # perluasanKalimat = request.form.get('perluasanKalimat')

            if model == "":
                model = "CNN"

            if perluasan == "":
                perluasan = "1"

            perluasanKalimat = "0"

            # if perluasanKalimat == "on":
            #     perluasanKalimat = "1"
            # else:
            #     perluasanKalimat = "0"

            
            filename = fileKirim.filename

            if filename.endswith('.csv'):
                dataBatch = list(csv.reader(fileKirim.read().decode('utf-8').splitlines()))

                # Convert ke List Biasa
                data = []
                for i in range(1, len(dataBatch)):
                    data.append(dataBatch[i][0])
                
                # Create Pandas Dataframe
                dfDownload = pd.DataFrame()
                dfDownload['tweet'] = data
                length = len(dfDownload['tweet'])
                dummyData = np.random.randint(2, 3, size=length)
                
                # Klasifikasi
                dfDownload['Non_HS'] = dummyData
                dfDownload['HS'] = dummyData
                dfDownload['Abusive'] = dummyData
                dfDownload['HS_individual'] = dummyData
                dfDownload['HS_Group'] = dummyData
                dfDownload['HS_Religion'] = dummyData
                dfDownload['HS_Race'] = dummyData
                dfDownload['HS_Physical'] = dummyData
                dfDownload['HS_Gender'] = dummyData
                dfDownload['HS_Other'] = dummyData
                dfDownload['HS_Weak'] = dummyData
                dfDownload['HS_Moderate'] = dummyData
                dfDownload['HS_Strong'] = dummyData

                dfDownload['Non_HS_Persen'] = 0
                dfDownload['HS_Persen'] = 0
                dfDownload['Abusive_Persen'] = 0
                dfDownload['HS_individual_Persen'] = 0
                dfDownload['HS_Group_Persen'] = 0
                dfDownload['HS_Religion_Persen'] = 0
                dfDownload['HS_Race_Persen'] = 0
                dfDownload['HS_Physical_Persen'] = 0
                dfDownload['HS_Gender_Persen'] = 0
                dfDownload['HS_Other_Persen'] = 0
                dfDownload['HS_Weak_Persen'] = 0
                dfDownload['HS_Moderate_Persen'] = 0
                dfDownload['HS_Strong_Persen'] = 0

                dfDownload['normalize'] = ""

                # normalisasi kata
                number = 0
                for kalimatTweet in data:
                    if number > 50:
                        break
                    tweet = casefolding(kalimatTweet)
                    tweet = hapusKata(tweet)
                    tweet = normalizeText(tweet)
                    normalTeks = tweet

                    if perluasanKalimat=="1":
                        # tweet = backTranslate(tweet, target_language='fr')
                        # tweet = backTranslate(tweet, target_language='en')
                        # tweet = backTranslate(tweet, target_language='id')

                        # semantic
                        tweet = semanticExpantion(tweet)
                    
                    # stemming
                    tweet = stemmer.stem(tweet)
                    # embedding
                    tweet = paddedSensor(tweet)

                    # Prediksi
                    tweet = prediksi(tweet, model, perluasan)

                    # Adding To Dataframe

                    ## KLasifikasi
                    dfDownload.at[number, 'Non_HS'] = tweet[0][0]
                    dfDownload.at[number, 'HS'] = tweet[0][1]
                    dfDownload.at[number, 'Abusive'] = tweet[0][2]
                    dfDownload.at[number, 'HS_individual'] = tweet[0][3]
                    dfDownload.at[number, 'HS_Group'] = tweet[0][4]
                    dfDownload.at[number, 'HS_Religion'] = tweet[0][5]
                    dfDownload.at[number, 'HS_Race'] = tweet[0][6]
                    dfDownload.at[number, 'HS_Physical'] = tweet[0][7]
                    dfDownload.at[number, 'HS_Gender'] = tweet[0][8]
                    dfDownload.at[number, 'HS_Other'] = tweet[0][9]
                    dfDownload.at[number, 'HS_Weak'] = tweet[0][10]
                    dfDownload.at[number, 'HS_Moderate'] = tweet[0][11]
                    dfDownload.at[number, 'HS_Strong'] = tweet[0][12]

                    ## Persentase
                    proba = []
                    for i in tweet[1]:
                        percentage = i*100
                        proba.append(percentage)

                    dfDownload.at[number, 'Non_HS_Persen'] = proba[0][0]
                    dfDownload.at[number, 'HS_Persen'] = proba[0][1]
                    dfDownload.at[number, 'Abusive_Persen'] = proba[0][2]
                    dfDownload.at[number, 'HS_individual_Persen'] = proba[0][3]
                    dfDownload.at[number, 'HS_Group_Persen'] = proba[0][4]
                    dfDownload.at[number, 'HS_Religion_Persen'] = proba[0][5]
                    dfDownload.at[number, 'HS_Race_Persen'] = proba[0][6]
                    dfDownload.at[number, 'HS_Physical_Persen'] = proba[0][7]
                    dfDownload.at[number, 'HS_Gender_Persen'] = proba[0][8]
                    dfDownload.at[number, 'HS_Other_Persen'] = proba[0][9]
                    dfDownload.at[number, 'HS_Weak_Persen'] = proba[0][10]
                    dfDownload.at[number, 'HS_Moderate_Persen'] = proba[0][11]
                    dfDownload.at[number, 'HS_Strong_Persen'] = proba[0][12]

                    dfDownload.at[number, 'normalize'] = normalTeks
                    number+=1

                dictData = dfDownload.to_dict()

                return render_template("batch.html", form=form, dictData=dictData, hasil="1")
                # Send Download To User
                # csv_data = dfDownload.to_csv(index=False)

                # # Create an in-memory file object
                # downloadData = io.BytesIO()
                # downloadData.write(csv_data.encode())
                # downloadData.seek(0)

                # return send_file(downloadData,
                #     mimetype='text/csv',
                #     as_attachment=True,
                #     download_name='batch-sentiment.csv')
            else:
                sukses = request.args.get('sukses')
                return render_template("batch.html", sukses=sukses, form=form)
    else:
        sukses = request.args.get('sukses')
        return render_template("batch.html", sukses=sukses, form=form)

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True)
