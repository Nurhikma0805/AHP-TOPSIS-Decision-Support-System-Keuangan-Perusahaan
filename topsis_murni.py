import numpy as np
import pandas as pd

# ============================================
# 1. FUNGSI PERHITUNGAN AHP
# ============================================

def ahp_weights(matrix):
    """Menghitung bobot AHP dari matriks perbandingan berpasangan"""
    matrix = np.array(matrix, dtype=float)
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights


# ============================================
# 2. MATRIKS PERBANDINGAN KRITERIA
# ============================================

M_kriteria = [
    [1,   3,   4,   5],
    [1/3, 1,   3,   4],
    [1/4, 1/3, 1,   3],
    [1/5, 1/4, 1/3, 1],
]

kriteria = ["Profitabilitas", "Likuiditas", "Solvabilitas", "Efisiensi"]
w_kriteria = ahp_weights(M_kriteria)


# ============================================
# 3. MATRIKS SUB-KRITERIA
# ============================================

M_profit = [[1, 2],
            [0.5, 1]]
sub_profit = ["ROA", "Tingkat Laba Operasional"]

M_likuid = [[1, 0.5],
            [2, 1]]
sub_likuid = ["Rasio Lancar", "Rasio Cepat"]

M_solv = [[1, 2, 3],
          [0.5, 1, 2],
          [0.333, 0.5, 1]]
sub_solv = ["Total Utang/Total Nilai Bersih", "Rasio Utang", "Nilai Bersih/Aset"]

M_efisiensi = [[1, 2, 3],
               [0.5, 1, 2],
               [0.333, 0.5, 1]]
sub_efisiensi = ["Tingkat Arus Kas", "Arus Kas terhadap Liabilitas", "Perputaran Total Aset"]

w_profit = ahp_weights(M_profit)
w_likuid = ahp_weights(M_likuid)
w_solv = ahp_weights(M_solv)
w_efisiensi = ahp_weights(M_efisiensi)


# ============================================
# 4. HITUNG BOBOT GLOBAL: Kriteria × Sub
# ============================================

bobot_global_sub = {}

for sub, w in zip(sub_profit, w_profit):
    bobot_global_sub[sub] = w * w_kriteria[0]

for sub, w in zip(sub_likuid, w_likuid):
    bobot_global_sub[sub] = w * w_kriteria[1]

for sub, w in zip(sub_solv, w_solv):
    bobot_global_sub[sub] = w * w_kriteria[2]

for sub, w in zip(sub_efisiensi, w_efisiensi):
    bobot_global_sub[sub] = w * w_kriteria[3]


# ============================================
# 5. DAFTAR SUB-KRITERIA
# ============================================

expected_subs = sub_profit + sub_likuid + sub_solv + sub_efisiensi


# ============================================
# 6. IDENTIFIKASI BENEFIT / COST
# ============================================

benefit_criteria = [
    "ROA",
    "Tingkat Laba Operasional",
    "Rasio Lancar",
    "Rasio Cepat",
    "Nilai Bersih/Aset",
    "Tingkat Arus Kas",
    "Arus Kas terhadap Liabilitas",
    "Perputaran Total Aset"
]

cost_criteria = [
    "Total Utang/Total Nilai Bersih",
    "Rasio Utang"
]


# ============================================
# 7. FUNGSI TOPSIS MURNI (TANPA RATING)
# ============================================

def calculate_topsis_murni(df):
    """
    Menghitung TOPSIS langsung dari nilai asli (tanpa konversi BS/B/C/K)
    
    Args:
        df: DataFrame dengan kolom sub-kriteria
        
    Returns:
        DataFrame dengan tambahan kolom Skor_TOPSIS dan Rank_TOPSIS
    """
    # Pastikan semua kolom ada
    missing_cols = [col for col in expected_subs if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom tidak ditemukan: {missing_cols}")
    
    # 7.1. Matriks Keputusan
    X = df[expected_subs].values.astype(float)
    
    # 7.2. Normalisasi Vektor
    X_squared_sum = np.sqrt((X ** 2).sum(axis=0))
    # Hindari pembagian dengan nol
    X_squared_sum[X_squared_sum == 0] = 1.0
    R = X / X_squared_sum
    
    # 7.3. Bobot AHP (Global)
    weights = np.array([bobot_global_sub[col] for col in expected_subs])
    
    # 7.4. Matriks Normalisasi Terbobot
    V = R * weights
    
    # 7.5. Solusi Ideal Positif dan Negatif
    A_plus = np.zeros(len(expected_subs))
    A_minus = np.zeros(len(expected_subs))
    
    for i, col in enumerate(expected_subs):
        if col in benefit_criteria:
            A_plus[i] = V[:, i].max()
            A_minus[i] = V[:, i].min()
        else:  # COST
            A_plus[i] = V[:, i].min()
            A_minus[i] = V[:, i].max()
    
    # 7.6. Jarak ke solusi ideal
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    
    # 7.7. Skor TOPSIS
    denominator = D_plus + D_minus
    denominator[denominator == 0] = 1.0  # Hindari pembagian dengan nol
    C = D_minus / denominator
    
    # 7.8. Tambahkan ke DataFrame
    df_result = df.copy()
    df_result['Skor_TOPSIS_Murni'] = C
    df_result['Rank_TOPSIS_Murni'] = df_result['Skor_TOPSIS_Murni'].rank(ascending=False, method='min').astype(int)
    
    return df_result


def get_detail_perhitungan(df):
    """
    Mendapatkan detail perhitungan untuk ditampilkan
    
    Returns:
        dict dengan detail matriks dan hasil
    """
    X = df[expected_subs].values.astype(float)
    
    # Normalisasi
    X_squared_sum = np.sqrt((X ** 2).sum(axis=0))
    X_squared_sum[X_squared_sum == 0] = 1.0
    R = X / X_squared_sum
    
    # Weighted
    weights = np.array([bobot_global_sub[col] for col in expected_subs])
    V = R * weights
    
    # Ideal Solutions
    A_plus = np.zeros(len(expected_subs))
    A_minus = np.zeros(len(expected_subs))
    
    for i, col in enumerate(expected_subs):
        if col in benefit_criteria:
            A_plus[i] = V[:, i].max()
            A_minus[i] = V[:, i].min()
        else:
            A_plus[i] = V[:, i].min()
            A_minus[i] = V[:, i].max()
    
    # Distances
    D_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    D_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))
    
    return {
        'matriks_keputusan': X,
        'matriks_normalisasi': R,
        'matriks_terbobot': V,
        'bobot': weights,
        'ideal_positif': A_plus,
        'ideal_negatif': A_minus,
        'jarak_positif': D_plus,
        'jarak_negatif': D_minus,
        'kriteria': expected_subs,
        'bobot_global': bobot_global_sub
    }


# ============================================
# 8. FUNGSI UNTUK MENDAPATKAN INFO AHP
# ============================================

def get_ahp_info():
    """
    Mendapatkan informasi lengkap perhitungan AHP
    
    Returns:
        dict dengan info bobot kriteria dan sub-kriteria
    """
    return {
        'kriteria': {
            'nama': kriteria,
            'bobot': w_kriteria.tolist(),
            'matriks': M_kriteria
        },
        'profitabilitas': {
            'nama': sub_profit,
            'bobot_lokal': w_profit.tolist(),
            'bobot_global': [bobot_global_sub[s] for s in sub_profit],
            'matriks': M_profit
        },
        'likuiditas': {
            'nama': sub_likuid,
            'bobot_lokal': w_likuid.tolist(),
            'bobot_global': [bobot_global_sub[s] for s in sub_likuid],
            'matriks': M_likuid
        },
        'solvabilitas': {
            'nama': sub_solv,
            'bobot_lokal': w_solv.tolist(),
            'bobot_global': [bobot_global_sub[s] for s in sub_solv],
            'matriks': M_solv
        },
        'efisiensi': {
            'nama': sub_efisiensi,
            'bobot_lokal': w_efisiensi.tolist(),
            'bobot_global': [bobot_global_sub[s] for s in sub_efisiensi],
            'matriks': M_efisiensi
        }
    }