from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ahp_topsis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# ============================================
# IMPORT TOPSIS MURNI
# ============================================
try:
    from topsis_murni import (
        calculate_topsis_murni,
        get_detail_perhitungan,
        get_ahp_info as get_ahp_info_murni,
        expected_subs,
        benefit_criteria,
        cost_criteria
    )
    TOPSIS_MURNI_AVAILABLE = True
except ImportError:
    TOPSIS_MURNI_AVAILABLE = False
    print("⚠️ Warning: topsis_murni.py tidak ditemukan. Fitur TOPSIS Murni tidak tersedia.")

# ============================================
# DATABASE MODELS
# ============================================

class Perusahaan(db.Model):
    __tablename__ = 'perusahaan'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(200), nullable=False)
    
    # Profitabilitas
    roa = db.Column(db.Float, nullable=False)
    laba_operasional = db.Column(db.Float, nullable=False)
    
    # Likuiditas
    rasio_lancar = db.Column(db.Float, nullable=False)
    rasio_cepat = db.Column(db.Float, nullable=False)
    
    # Solvabilitas
    utang_nilai_bersih = db.Column(db.Float, nullable=False)
    rasio_utang = db.Column(db.Float, nullable=False)
    nilai_bersih_aset = db.Column(db.Float, nullable=False)
    
    # Efisiensi
    arus_kas = db.Column(db.Float, nullable=False)
    arus_kas_liabilitas = db.Column(db.Float, nullable=False)
    perputaran_aset = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Perusahaan {self.nama}>'


class HasilAnalisis(db.Model):
    __tablename__ = 'hasil_analisis'
    id = db.Column(db.Integer, primary_key=True)
    perusahaan_id = db.Column(db.Integer, db.ForeignKey('perusahaan.id'), nullable=False)
    skor_ahp = db.Column(db.Float)
    skor_topsis = db.Column(db.Float)
    rank_topsis = db.Column(db.Integer)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    perusahaan = db.relationship('Perusahaan', backref=db.backref('hasil', lazy=True))


# ============================================
# FUNGSI PERHITUNGAN AHP
# ============================================

def ahp_weights(matrix):
    """Hitung bobot dari matriks perbandingan berpasangan"""
    matrix = np.array(matrix, dtype=float)
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights


def calculate_consistency_ratio(matrix):
    """Hitung Consistency Ratio (CR)"""
    matrix = np.array(matrix, dtype=float)
    n = len(matrix)
    
    weights = ahp_weights(matrix)
    weighted_sum = matrix.dot(weights)
    lambda_max = np.mean(weighted_sum / weights)
    
    CI = (lambda_max - n) / (n - 1) if n > 1 else 0
    
    RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 
          7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    
    CR = CI / RI.get(n, 1.45) if n in RI and RI[n] != 0 else 0
    
    return CR, lambda_max, CI


def get_ahp_matrices():
    """Return matriks perbandingan AHP yang sudah didefinisikan"""
    
    M_kriteria = [
        [1,   3,   4,   5],
        [1/3, 1,   3,   4],
        [1/4, 1/3, 1,   3],
        [1/5, 1/4, 1/3, 1],
    ]
    kriteria = ["Profitabilitas", "Likuiditas", "Solvabilitas", "Efisiensi"]
    
    M_profit = [[1, 2], [0.5, 1]]
    sub_profit = ["ROA", "Tingkat Laba Operasional"]
    
    M_likuid = [[1, 0.5], [2, 1]]
    sub_likuid = ["Rasio Lancar", "Rasio Cepat"]
    
    M_solv = [[1, 2, 3], [0.5, 1, 2], [0.333, 0.5, 1]]
    sub_solv = ["Total Utang/Total Nilai Bersih", "Rasio Utang", "Nilai Bersih/Aset"]
    
    M_efisiensi = [[1, 2, 3], [0.5, 1, 2], [0.333, 0.5, 1]]
    sub_efisiensi = ["Tingkat Arus Kas", "Arus Kas terhadap Liabilitas", "Perputaran Total Aset"]
    
    M_rating = [
        [1, 2, 3, 4],
        [0.5, 1, 2, 3],
        [0.333, 0.5, 1, 2],
        [0.25, 0.333, 0.5, 1]
    ]
    rating_labels = ["BS", "B", "C", "K"]
    
    return {
        'kriteria': (M_kriteria, kriteria),
        'profit': (M_profit, sub_profit),
        'likuid': (M_likuid, sub_likuid),
        'solv': (M_solv, sub_solv),
        'efisiensi': (M_efisiensi, sub_efisiensi),
        'rating': (M_rating, rating_labels)
    }


def calculate_ahp_weights():
    """Hitung semua bobot AHP"""
    matrices = get_ahp_matrices()
    
    w_kriteria = ahp_weights(matrices['kriteria'][0])
    w_profit = ahp_weights(matrices['profit'][0])
    w_likuid = ahp_weights(matrices['likuid'][0])
    w_solv = ahp_weights(matrices['solv'][0])
    w_efisiensi = ahp_weights(matrices['efisiensi'][0])
    
    w_rating = ahp_weights(matrices['rating'][0])
    bobot_rating = dict(zip(matrices['rating'][1], w_rating))
    
    bobot_global_sub = {}
    
    for sub, w in zip(matrices['profit'][1], w_profit):
        bobot_global_sub[sub] = w * w_kriteria[0]
    
    for sub, w in zip(matrices['likuid'][1], w_likuid):
        bobot_global_sub[sub] = w * w_kriteria[1]
    
    for sub, w in zip(matrices['solv'][1], w_solv):
        bobot_global_sub[sub] = w * w_kriteria[2]
    
    for sub, w in zip(matrices['efisiensi'][1], w_efisiensi):
        bobot_global_sub[sub] = w * w_kriteria[3]
    
    cr, lambda_max, ci = calculate_consistency_ratio(matrices['kriteria'][0])
    
    return {
        'kriteria': dict(zip(matrices['kriteria'][1], w_kriteria)),
        'bobot_global': bobot_global_sub,
        'bobot_rating': bobot_rating,
        'cr': cr,
        'lambda_max': lambda_max,
        'ci': ci
    }


def map_to_rating(series):
    """Mapping nilai ke rating BS/B/C/K berdasarkan kuartil"""
    q1 = series.quantile(0.25)
    q2 = series.quantile(0.50)
    q3 = series.quantile(0.75)
    labels = []
    for v in series:
        if v >= q3:
            labels.append("BS")
        elif v >= q2:
            labels.append("B")
        elif v >= q1:
            labels.append("C")
        else:
            labels.append("K")
    return labels


def calculate_topsis():
    """Hitung TOPSIS untuk semua perusahaan"""
    
    perusahaan_list = Perusahaan.query.all()
    
    if len(perusahaan_list) == 0:
        return None, None
    
    data = []
    for p in perusahaan_list:
        data.append({
            'id': p.id,
            'kode': p.kode,
            'nama': p.nama,
            'ROA': p.roa,
            'Tingkat Laba Operasional': p.laba_operasional,
            'Rasio Lancar': p.rasio_lancar,
            'Rasio Cepat': p.rasio_cepat,
            'Total Utang/Total Nilai Bersih': p.utang_nilai_bersih,
            'Rasio Utang': p.rasio_utang,
            'Nilai Bersih/Aset': p.nilai_bersih_aset,
            'Tingkat Arus Kas': p.arus_kas,
            'Arus Kas terhadap Liabilitas': p.arus_kas_liabilitas,
            'Perputaran Total Aset': p.perputaran_aset
        })
    
    df = pd.DataFrame(data)
    
    kriteria_cols = [
        'ROA', 'Tingkat Laba Operasional',
        'Rasio Lancar', 'Rasio Cepat',
        'Total Utang/Total Nilai Bersih', 'Rasio Utang', 'Nilai Bersih/Aset',
        'Tingkat Arus Kas', 'Arus Kas terhadap Liabilitas', 'Perputaran Total Aset'
    ]
    
    ahp_results = calculate_ahp_weights()
    bobot_global_sub = ahp_results['bobot_global']
    bobot_rating = ahp_results['bobot_rating']
    
    for col in kriteria_cols:
        df[f"{col}_rating"] = map_to_rating(df[col])
    
    df["Skor_AHP_final"] = 0.0
    for col in kriteria_cols:
        w_sub = bobot_global_sub[col]
        df["Skor_AHP_final"] += df[f"{col}_rating"].map(bobot_rating) * w_sub
    
    X = df[kriteria_cols].values
    
    X_squared_sum = np.sqrt((X ** 2).sum(axis=0))
    R = X / X_squared_sum
    
    weights = np.array([bobot_global_sub[col] for col in kriteria_cols])
    
    V = R * weights
    
    A_plus = V.max(axis=0)
    A_minus = V.min(axis=0)
    
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    
    C = D_minus / (D_plus + D_minus)
    
    df['Skor_TOPSIS'] = C
    df['Rank_TOPSIS'] = df['Skor_TOPSIS'].rank(ascending=False, method='min').astype(int)
    
    def get_status(skor):
        if skor >= 0.7:
            return "Sangat Baik"
        elif skor >= 0.5:
            return "Baik"
        elif skor >= 0.3:
            return "Cukup"
        else:
            return "Perlu Perhatian"
    
    df['Status'] = df['Skor_TOPSIS'].apply(get_status)
    
    HasilAnalisis.query.delete()
    
    for _, row in df.iterrows():
        hasil = HasilAnalisis(
            perusahaan_id=row['id'],
            skor_ahp=row['Skor_AHP_final'],
            skor_topsis=row['Skor_TOPSIS'],
            rank_topsis=row['Rank_TOPSIS'],
            status=row['Status']
        )
        db.session.add(hasil)
    
    db.session.commit()
    
    return df, ahp_results


# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    total_perusahaan = Perusahaan.query.count()
    
    ahp_results = calculate_ahp_weights()
    cr_value = ahp_results['cr']
    
    hasil_count = HasilAnalisis.query.count()
    status_analisis = "Belum" if hasil_count == 0 else "Sudah"
    
    top_perusahaan = []
    if hasil_count > 0:
        hasil_list = db.session.query(HasilAnalisis, Perusahaan).join(
            Perusahaan, HasilAnalisis.perusahaan_id == Perusahaan.id
        ).order_by(HasilAnalisis.rank_topsis).limit(5).all()
        
        for hasil, perusahaan in hasil_list:
            top_perusahaan.append({
                'kode': perusahaan.kode,
                'nama': perusahaan.nama,
                'skor': hasil.skor_topsis,
                'rank': hasil.rank_topsis
            })
    
    return render_template('dashboard.html',
                         total_perusahaan=total_perusahaan,
                         total_kriteria=10,
                         status_analisis=status_analisis,
                         cr_value=cr_value,
                         top_perusahaan=top_perusahaan,
                         topsis_murni_available=TOPSIS_MURNI_AVAILABLE)


@app.route('/data-perusahaan')
def data_perusahaan():
    perusahaan_list = Perusahaan.query.all()
    return render_template('data_perusahaan.html', perusahaan_list=perusahaan_list)


@app.route('/data-perusahaan/tambah', methods=['GET', 'POST'])
def tambah_perusahaan():
    if request.method == 'POST':
        try:
            perusahaan = Perusahaan(
                kode=request.form['kode'],
                nama=request.form['nama'],
                roa=float(request.form['roa']),
                laba_operasional=float(request.form['laba_operasional']),
                rasio_lancar=float(request.form['rasio_lancar']),
                rasio_cepat=float(request.form['rasio_cepat']),
                utang_nilai_bersih=float(request.form['utang_nilai_bersih']),
                rasio_utang=float(request.form['rasio_utang']),
                nilai_bersih_aset=float(request.form['nilai_bersih_aset']),
                arus_kas=float(request.form['arus_kas']),
                arus_kas_liabilitas=float(request.form['arus_kas_liabilitas']),
                perputaran_aset=float(request.form['perputaran_aset'])
            )
            db.session.add(perusahaan)
            db.session.commit()
            flash('Data perusahaan berhasil ditambahkan!', 'success')
            return redirect(url_for('data_perusahaan'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan data: {str(e)}', 'danger')
    
    return render_template('tambah_perusahaan.html')


@app.route('/data-perusahaan/edit/<int:id>', methods=['GET', 'POST'])
def edit_perusahaan(id):
    perusahaan = Perusahaan.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            perusahaan.kode = request.form['kode']
            perusahaan.nama = request.form['nama']
            perusahaan.roa = float(request.form['roa'])
            perusahaan.laba_operasional = float(request.form['laba_operasional'])
            perusahaan.rasio_lancar = float(request.form['rasio_lancar'])
            perusahaan.rasio_cepat = float(request.form['rasio_cepat'])
            perusahaan.utang_nilai_bersih = float(request.form['utang_nilai_bersih'])
            perusahaan.rasio_utang = float(request.form['rasio_utang'])
            perusahaan.nilai_bersih_aset = float(request.form['nilai_bersih_aset'])
            perusahaan.arus_kas = float(request.form['arus_kas'])
            perusahaan.arus_kas_liabilitas = float(request.form['arus_kas_liabilitas'])
            perusahaan.perputaran_aset = float(request.form['perputaran_aset'])
            
            db.session.commit()
            flash('Data perusahaan berhasil diupdate!', 'success')
            return redirect(url_for('data_perusahaan'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal mengupdate data: {str(e)}', 'danger')
    
    return render_template('edit_perusahaan.html', perusahaan=perusahaan)


@app.route('/data-perusahaan/hapus/<int:id>')
def hapus_perusahaan(id):
    perusahaan = Perusahaan.query.get_or_404(id)
    try:
        HasilAnalisis.query.filter_by(perusahaan_id=id).delete()
        db.session.delete(perusahaan)
        db.session.commit()
        flash('Data perusahaan berhasil dihapus!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus data: {str(e)}', 'danger')
    
    return redirect(url_for('data_perusahaan'))


@app.route('/data-kriteria')
def data_kriteria():
    ahp_results = calculate_ahp_weights()
    matrices = get_ahp_matrices()
    
    return render_template('data_kriteria.html',
                         ahp_results=ahp_results,
                         matrices=matrices)


@app.route('/proses-ahp')
def proses_ahp():
    ahp_results = calculate_ahp_weights()
    matrices = get_ahp_matrices()
    
    return render_template('proses_ahp.html',
                         ahp_results=ahp_results,
                         matrices=matrices)


@app.route('/proses-topsis')
def proses_topsis():
    perusahaan_count = Perusahaan.query.count()
    ahp_results = calculate_ahp_weights()
    
    if perusahaan_count == 0:
        return render_template('proses_topsis.html',
                             hasil_list=[],
                             ahp_results=ahp_results,
                             pesan_kosong=True)
    
    try:
        df, ahp_results = calculate_topsis()
        hasil_list = df.to_dict('records')
        
        return render_template('proses_topsis.html',
                             hasil_list=hasil_list,
                             ahp_results=ahp_results,
                             pesan_kosong=False)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return render_template('proses_topsis.html',
                             hasil_list=[],
                             ahp_results=ahp_results,
                             pesan_kosong=True)


@app.route('/hasil-akhir')
def hasil_akhir():
    hasil_list = db.session.query(HasilAnalisis, Perusahaan).join(
        Perusahaan, HasilAnalisis.perusahaan_id == Perusahaan.id
    ).order_by(HasilAnalisis.rank_topsis).all()
    
    return render_template('hasil_akhir.html', 
                         hasil_list=hasil_list,
                         pesan_kosong=(len(hasil_list) == 0))


@app.route('/jalankan-topsis')
def jalankan_topsis():
    """Jalankan perhitungan TOPSIS secara manual"""
    perusahaan_count = Perusahaan.query.count()
    
    if perusahaan_count == 0:
        flash('Tidak ada data perusahaan! Silakan tambah data terlebih dahulu.', 'danger')
        return redirect(url_for('data_perusahaan'))
    
    try:
        df, ahp_results = calculate_topsis()
        flash(f'✅ Perhitungan TOPSIS berhasil! {perusahaan_count} perusahaan telah dianalisis.', 'success')
        return redirect(url_for('hasil_akhir'))
    except Exception as e:
        flash(f'❌ Error saat perhitungan: {str(e)}', 'danger')
        return redirect(url_for('data_perusahaan'))


# ============================================
# ROUTES TOPSIS MURNI (BARU!)
# ============================================

@app.route('/topsis-murni')
def topsis_murni():
    """Halaman TOPSIS Murni - tanpa konversi rating"""
    if not TOPSIS_MURNI_AVAILABLE:
        flash('Fitur TOPSIS Murni tidak tersedia. File topsis_murni.py tidak ditemukan.', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        perusahaan_list = Perusahaan.query.all()
        
        if not perusahaan_list:
            flash('Belum ada data perusahaan. Silakan input data terlebih dahulu.', 'warning')
            return redirect(url_for('data_perusahaan'))
        
        # Konversi ke DataFrame
        data = []
        for p in perusahaan_list:
            row = {
                'id': p.id,
                'kode': p.kode,
                'nama': p.nama,
                'ROA': p.roa,
                'Tingkat Laba Operasional': p.laba_operasional,
                'Rasio Lancar': p.rasio_lancar,
                'Rasio Cepat': p.rasio_cepat,
                'Total Utang/Total Nilai Bersih': p.utang_nilai_bersih,
                'Rasio Utang': p.rasio_utang,
                'Nilai Bersih/Aset': p.nilai_bersih_aset,
                'Tingkat Arus Kas': p.arus_kas,
                'Arus Kas terhadap Liabilitas': p.arus_kas_liabilitas,
                'Perputaran Total Aset': p.perputaran_aset
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Hitung TOPSIS Murni
        df_hasil = calculate_topsis_murni(df)
        
        # Dapatkan detail perhitungan
        detail = get_detail_perhitungan(df)
        
        # Dapatkan info AHP
        ahp_info = get_ahp_info_murni()
        
        # Sort berdasarkan ranking
        df_hasil = df_hasil.sort_values('Rank_TOPSIS_Murni')
        
        # Konversi ke list of dict untuk template
        hasil_list = df_hasil.to_dict('records')
        
        return render_template('topsis_murni.html',
                             hasil=hasil_list,
                             detail=detail,
                             ahp_info=ahp_info,
                             kriteria=expected_subs,
                             n_companies=len(df_hasil))
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/export-topsis-murni')
def export_topsis_murni():
    """Export hasil TOPSIS Murni ke Excel"""
    if not TOPSIS_MURNI_AVAILABLE:
        flash('Fitur TOPSIS Murni tidak tersedia.', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        perusahaan_list = Perusahaan.query.all()
        
        if not perusahaan_list:
            flash('Belum ada data untuk di-export', 'warning')
            return redirect(url_for('topsis_murni'))
        
        # Konversi ke DataFrame
        data = []
        for p in perusahaan_list:
            row = {
                'Kode': p.kode,
                'Nama Perusahaan': p.nama,
                'ROA': p.roa,
                'Tingkat Laba Operasional': p.laba_operasional,
                'Rasio Lancar': p.rasio_lancar,
                'Rasio Cepat': p.rasio_cepat,
                'Total Utang/Total Nilai Bersih': p.utang_nilai_bersih,
                'Rasio Utang': p.rasio_utang,
                'Nilai Bersih/Aset': p.nilai_bersih_aset,
                'Tingkat Arus Kas': p.arus_kas,
                'Arus Kas terhadap Liabilitas': p.arus_kas_liabilitas,
                'Perputaran Total Aset': p.perputaran_aset
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Rename untuk TOPSIS
        df_topsis = df.rename(columns={'Nama Perusahaan': 'nama'})
        
        # Hitung TOPSIS
        df_hasil = calculate_topsis_murni(df_topsis)
        
        # Pilih kolom untuk export
        kolom_export = ['Kode', 'nama'] + list(expected_subs) + ['Skor_TOPSIS_Murni', 'Rank_TOPSIS_Murni']
        df_export = df_hasil[kolom_export].copy()
        df_export = df_export.rename(columns={'nama': 'Nama Perusahaan'})
        
        # Sort berdasarkan ranking
        df_export = df_export.sort_values('Rank_TOPSIS_Murni')
        
        # Simpan ke file Excel
        output_filename = f'HASIL_TOPSIS_MURNI_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Pastikan folder upload ada
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        df_export.to_excel(output_path, index=False, sheet_name='Hasil TOPSIS Murni')
        
        # Download file
        return send_file(
            output_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=output_filename
        )
    
    except Exception as e:
        flash(f'Error saat export: {str(e)}', 'danger')
        return redirect(url_for('topsis_murni'))


@app.route('/perbandingan-metode')
def perbandingan_metode():
    """Halaman perbandingan TOPSIS Rating vs TOPSIS Murni"""
    if not TOPSIS_MURNI_AVAILABLE:
        flash('Fitur perbandingan tidak tersedia.', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        perusahaan_list = Perusahaan.query.all()
        
        if not perusahaan_list:
            flash('Belum ada data perusahaan', 'warning')
            return redirect(url_for('data_perusahaan'))
        
        # Konversi ke DataFrame
        data = []
        for p in perusahaan_list:
            row = {
                'id': p.id,
                'kode': p.kode,
                'nama': p.nama,
                'ROA': p.roa,
                'Tingkat Laba Operasional': p.laba_operasional,
                'Rasio Lancar' : p.rasio_lancar,
                'Rasio Cepat': p.rasio_cepat,
                'Total Utang/Total Nilai Bersih': p.utang_nilai_bersih,
                'Rasio Utang': p.rasio_utang,
                'Nilai Bersih/Aset': p.nilai_bersih_aset,
                'Tingkat Arus Kas': p.arus_kas,
                'Arus Kas terhadap Liabilitas': p.arus_kas_liabilitas,
                'Perputaran Total Aset': p.perputaran_aset
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Hitung TOPSIS Rating (menggunakan fungsi yang sudah ada)
        df_rating, _ = calculate_topsis()
        
        # Hitung TOPSIS Murni
        df_murni = calculate_topsis_murni(df)
        
        # Gabungkan hasil
        # Ambil kolom yang diperlukan dari masing-masing metode
        df_gabung = pd.DataFrame({
            'kode': df_murni['kode'],
            'nama': df_murni['nama'],
            'Skor_Rating': df_rating['Skor_TOPSIS'].values,
            'Rank_Rating': df_rating['Rank_TOPSIS'].values,
            'Skor_Murni': df_murni['Skor_TOPSIS_Murni'],
            'Rank_Murni': df_murni['Rank_TOPSIS_Murni'],
        })
        
        # Hitung selisih ranking
        df_gabung['Selisih_Rank'] = abs(df_gabung['Rank_Rating'] - df_gabung['Rank_Murni'])
        
        # Sort berdasarkan ranking TOPSIS Murni
        df_gabung = df_gabung.sort_values('Rank_Murni')
        
        # Konversi ke list of dict
        hasil_list = df_gabung.to_dict('records')
        
        # Hitung statistik
        korelasi = df_gabung['Skor_Rating'].corr(df_gabung['Skor_Murni'])
        rata_selisih = df_gabung['Selisih_Rank'].mean()
        max_selisih = df_gabung['Selisih_Rank'].max()
        
        stats = {
            'korelasi': round(korelasi, 4),
            'rata_selisih': round(rata_selisih, 2),
            'max_selisih': int(max_selisih),
            'total_perusahaan': len(df_gabung)
        }
        
        return render_template('perbandingan_metode.html',
                             hasil=hasil_list,
                             stats=stats)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/export-perbandingan')
def export_perbandingan():
    """Export perbandingan ke Excel"""
    if not TOPSIS_MURNI_AVAILABLE:
        flash('Fitur perbandingan tidak tersedia.', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        perusahaan_list = Perusahaan.query.all()
        
        if not perusahaan_list:
            flash('Belum ada data untuk di-export', 'warning')
            return redirect(url_for('perbandingan_metode'))
        
        # Konversi ke DataFrame
        data = []
        for p in perusahaan_list:
            row = {
                'id': p.id,
                'kode': p.kode,
                'nama': p.nama,
                'ROA': p.roa,
                'Tingkat Laba Operasional': p.laba_operasional,
                'Rasio Lancar': p.rasio_lancar,
                'Rasio Cepat': p.rasio_cepat,
                'Total Utang/Total Nilai Bersih': p.utang_nilai_bersih,
                'Rasio Utang': p.rasio_utang,
                'Nilai Bersih/Aset': p.nilai_bersih_aset,
                'Tingkat Arus Kas': p.arus_kas,
                'Arus Kas terhadap Liabilitas': p.arus_kas_liabilitas,
                'Perputaran Total Aset': p.perputaran_aset
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Hitung kedua metode
        df_rating, _ = calculate_topsis()
        df_murni = calculate_topsis_murni(df)
        
        # Gabungkan hasil
        df_gabung = pd.DataFrame({
            'Kode': df_murni['kode'],
            'Nama Perusahaan': df_murni['nama'],
            'Skor TOPSIS Rating': df_rating['Skor_TOPSIS'].values,
            'Rank Rating': df_rating['Rank_TOPSIS'].values,
            'Skor TOPSIS Murni': df_murni['Skor_TOPSIS_Murni'],
            'Rank Murni': df_murni['Rank_TOPSIS_Murni'],
            'Selisih Rank': abs(df_rating['Rank_TOPSIS'].values - df_murni['Rank_TOPSIS_Murni'])
        })
        
        # Sort berdasarkan ranking murni
        df_gabung = df_gabung.sort_values('Rank Murni')
        
        # Simpan ke Excel
        output_filename = f'PERBANDINGAN_METODE_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Buat Excel dengan multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Perbandingan
            df_gabung.to_excel(writer, sheet_name='Perbandingan', index=False)
            
            # Sheet 2: Detail Rating
            df_rating_detail = df_rating[['kode', 'nama', 'Skor_TOPSIS', 'Rank_TOPSIS', 'Status']].copy()
            df_rating_detail = df_rating_detail.rename(columns={
                'kode': 'Kode',
                'nama': 'Nama Perusahaan',
                'Skor_TOPSIS': 'Skor',
                'Rank_TOPSIS': 'Ranking'
            })
            df_rating_detail = df_rating_detail.sort_values('Ranking')
            df_rating_detail.to_excel(writer, sheet_name='TOPSIS Rating', index=False)
            
            # Sheet 3: Detail Murni
            df_murni_detail = df_murni[['kode', 'nama', 'Skor_TOPSIS_Murni', 'Rank_TOPSIS_Murni']].copy()
            df_murni_detail = df_murni_detail.rename(columns={
                'kode': 'Kode',
                'nama': 'Nama Perusahaan',
                'Skor_TOPSIS_Murni': 'Skor',
                'Rank_TOPSIS_Murni': 'Ranking'
            })
            df_murni_detail = df_murni_detail.sort_values('Ranking')
            df_murni_detail.to_excel(writer, sheet_name='TOPSIS Murni', index=False)
        
        return send_file(
            output_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=output_filename
        )
    
    except Exception as e:
        flash(f'Error saat export: {str(e)}', 'danger')
        return redirect(url_for('perbandingan_metode'))


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)