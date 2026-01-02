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
- Visualisasi hasil analisis dalam bentuk tabel dan grafik

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
- Analisis hasil pemeringkatan dengan visualisasi interaktif dan ekspor data

---

## 📂 Struktur Folder

```
ahp-topsis-system/
├── contoh/              # File contoh data Excel
├── statis/              # File CSS, JS, images
├── templat/             # File HTML templates
├── ahp_topsis.py        # Logic AHP-TOPSIS
├── aplikasi.py          # Flask application
├── models.py            # Database models
├── requirements.txt     # Python dependencies
└── topsis_murni.py      # TOPSIS calculation
```

---

## 📌 Skala Perbandingan AHP

- **1** = Kedua kriteria sama penting
- **3** = Sedikit lebih penting
- **5** = Lebih penting
- **7** = Sangat lebih penting
- **9** = Mutlak lebih penting

---

## 📄 Catatan

**Pastikan file Excel Anda memiliki:**
- Kolom **PERUSAHAAN** dan semua kolom sub-kriteria sesuai dengan format yang ditentukan
- Data harus lengkap untuk semua sub-kriteria

**Contoh format Excel:**

| PERUSAHAAN | Profitabilitas | Likuiditas | Solvabilitas | Efisiensi | ... |
|------------|----------------|------------|--------------|-----------|-----|
| PT ABC     | 15.2           | 2.3        | 1.5          | 85.5      | ... |
| PT XYZ     | 12.8           | 1.9        | 1.8          | 78.2      | ... |

---

## 👨‍💻 Developer

Dikembangkan oleh: **[Nama Kamu]**  
Program PKL - PT Pos Indonesia  
Tahun: 2026

---

## 📜 Lisensi

MIT License
