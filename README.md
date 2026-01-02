# Sistem AHP-TOPSIS untuk Penilaian Kinerja Keuangan

Sistem pengambilan keputusan berbasis web yang menggunakan metode AHP dan TOPSIS untuk menilai dan merangking kinerja keuangan perusahaan manufaktur.

---

## 📖 Tentang Project

Project ini dikembangkan sebagai bagian dari program PKL di PT Pos Indonesia. Sistem ini membantu manajemen dalam menilai kinerja keuangan perusahaan secara objektif menggunakan metode Decision Support System.

---

## ✨ Fitur Utama

- Input dan perhitungan bobot kriteria dengan metode AHP
- Pemeringkatan perusahaan menggunakan metode TOPSIS  
- Upload data perusahaan melalui file Excel
- 
---

## 📊 Kriteria Penilaian

### 1. Profitabilitas
- ROA
- Tingkat Laba Operasional

### 2. Likuiditas
- Rasio Lancar
- Rasio Cepat

### 3. Solvabilitas
- Total Utang/Nilai Bersih
- Rasio Utang

### 4. Efisiensi
- Tingkat Aset
- Perputaran Aset

**Total Sub-Kriteria:** 10

---

## 💻 Teknologi

- **Backend:** Python 3.8+, Flask
- **Library:** NumPy, Pandas, Matplotlib
- **Frontend:** HTML, CSS, JavaScript

---

## 🚀 Instalasi

### 1. Kloning repositori
```bash
git clone https://github.com/Nurhikma0805/ahp-topsis-system.git
cd ahp-topsis-system
```

### 2. Instal dependensi
```bash
pip install -r requirements.txt
```

### 3. Jalankan aplikasi
```bash
python aplikasi.py
```

### 4. Akses aplikasi
Buka browser dan akses: `http://localhost:5000`

---

## 📝 Cara Penggunaan

### Tahapan Proses:

**1. AHP Kriteria Utama**
- Bandingkan 4 kriteria utama (Profitabilitas, Likuiditas, Solvabilitas, Efisiensi) menggunakan skala 1-9

**2. AHP Sub-Kriteria**
- Bandingkan sub-kriteria dalam setiap kriteria utama untuk mendapatkan bobot lokal

**3. Input Data Perusahaan**
- Upload file Excel yang berisi data kinerja keuangan perusahaan untuk semua sub-kriteria

**4. Hasil TOPSIS**
- Analisis hasil pemeringkatan 

---

## 📌 Skala Perbandingan AHP

- **1** = Kedua kriteria sama penting
- **3** = Sedikit lebih penting
- **5** = Lebih penting
- **7** = Sangat lebih penting
- **9** = Mutlak lebih penting

---

