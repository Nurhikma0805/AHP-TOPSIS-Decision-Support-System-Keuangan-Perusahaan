from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Perusahaan(db.Model):
    __tablename__ = 'perusahaan'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False)
    
    # 10 Kriteria Keuangan
    roa = db.Column(db.Float, default=0.0)  # C1 - Return on Assets
    tingkat_laba = db.Column(db.Float, default=0.0)  # C2 - Tingkat Laba
    rasio_lancar = db.Column(db.Float, default=0.0)  # C3 - Rasio Lancar
    rasio_cepat = db.Column(db.Float, default=0.0)  # C4 - Rasio Cepat
    total_utang = db.Column(db.Float, default=0.0)  # C5 - Total Utang terhadap Aset
    rasio_utang = db.Column(db.Float, default=0.0)  # C6 - Rasio Utang terhadap Ekuitas
    nilai_bersih = db.Column(db.Float, default=0.0)  # C7 - Nilai Bersih
    tingkat_arus_kas = db.Column(db.Float, default=0.0)  # C8 - Tingkat Arus Kas Operasi
    arus_kas_liabilitas = db.Column(db.Float, default=0.0)  # C9 - Arus Kas terhadap Total Liabilitas
    perputaran_aset = db.Column(db.Float, default=0.0)  # C10 - Perputaran Aset
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    hasil_topsis = db.relationship('HasilTOPSIS', backref='perusahaan', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Perusahaan {self.nama}>'
    
    def get_nilai_kriteria(self):
        """Return list of all criteria values"""
        return [
            self.roa,
            self.tingkat_laba,
            self.rasio_lancar,
            self.rasio_cepat,
            self.total_utang,
            self.rasio_utang,
            self.nilai_bersih,
            self.tingkat_arus_kas,
            self.arus_kas_liabilitas,
            self.perputaran_aset
        ]


class Kriteria(db.Model):
    __tablename__ = 'kriteria'
    
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(10), unique=True, nullable=False)  # C1, C2, etc.
    nama = db.Column(db.String(200), nullable=False)
    tipe = db.Column(db.String(10), nullable=False)  # 'benefit' or 'cost'
    bobot = db.Column(db.Float, default=0.0)  # Bobot dari AHP
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    hasil_ahp = db.relationship('HasilAHP', backref='kriteria', lazy=True, cascade='all, delete-orphan')
    pairwise_a = db.relationship('PairwiseComparison', foreign_keys='PairwiseComparison.kriteria_a_id', 
                                 backref='kriteria_a', lazy=True, cascade='all, delete-orphan')
    pairwise_b = db.relationship('PairwiseComparison', foreign_keys='PairwiseComparison.kriteria_b_id',
                                 backref='kriteria_b', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Kriteria {self.kode} - {self.nama}>'


class PairwiseComparison(db.Model):
    __tablename__ = 'pairwise_comparison'
    
    id = db.Column(db.Integer, primary_key=True)
    kriteria_a_id = db.Column(db.Integer, db.ForeignKey('kriteria.id'), nullable=False)
    kriteria_b_id = db.Column(db.Integer, db.ForeignKey('kriteria.id'), nullable=False)
    nilai = db.Column(db.Float, nullable=False)  # Nilai perbandingan (1-9)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PairwiseComparison {self.kriteria_a_id} vs {self.kriteria_b_id}: {self.nilai}>'


class HasilAHP(db.Model):
    __tablename__ = 'hasil_ahp'
    
    id = db.Column(db.Integer, primary_key=True)
    kriteria_id = db.Column(db.Integer, db.ForeignKey('kriteria.id'), nullable=False)
    bobot = db.Column(db.Float, nullable=False)
    consistency_ratio = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HasilAHP Kriteria {self.kriteria_id}: {self.bobot}>'


class HasilTOPSIS(db.Model):
    __tablename__ = 'hasil_topsis'
    
    id = db.Column(db.Integer, primary_key=True)
    perusahaan_id = db.Column(db.Integer, db.ForeignKey('perusahaan.id'), nullable=False)
    nilai_preferensi = db.Column(db.Float, nullable=False)  # Nilai V
    jarak_ideal_positif = db.Column(db.Float, default=0.0)  # D+
    jarak_ideal_negatif = db.Column(db.Float, default=0.0)  # D-
    ranking = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HasilTOPSIS {self.perusahaan_id}: Rank {self.ranking}>'