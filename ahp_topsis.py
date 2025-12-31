import numpy as np
from numpy.linalg import eig

class AHPCalculator:
    """
    AHP (Analytical Hierarchy Process) Calculator
    Menghitung bobot kriteria berdasarkan matriks perbandingan berpasangan
    """
    
    # Random Index untuk consistency check
    RI = {
        1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
        11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
    }
    
    def __init__(self, pairwise_matrix):
        """
        Initialize AHP Calculator
        
        Args:
            pairwise_matrix: numpy array berisi matriks perbandingan berpasangan
        """
        self.matrix = np.array(pairwise_matrix, dtype=float)
        self.n = len(self.matrix)
        self.weights = None
        self.cr = None
        self.lambda_max = None
    
    def calculate_weights(self):
        """
        Menghitung bobot kriteria menggunakan metode eigenvalue
        
        Returns:
            tuple: (weights, consistency_ratio)
        """
        # Hitung eigenvalues dan eigenvectors
        eigenvalues, eigenvectors = eig(self.matrix)
        
        # Ambil eigenvalue terbesar dan eigenvector-nya
        max_index = np.argmax(eigenvalues.real)
        self.lambda_max = eigenvalues[max_index].real
        principal_eigenvector = eigenvectors[:, max_index].real
        
        # Normalisasi eigenvector untuk mendapatkan bobot
        self.weights = principal_eigenvector / principal_eigenvector.sum()
        
        # Hitung Consistency Ratio
        self.cr = self.calculate_consistency_ratio()
        
        return self.weights, self.cr
    
    def calculate_consistency_ratio(self):
        """
        Menghitung Consistency Ratio (CR)
        CR < 0.1 menunjukkan konsistensi yang baik
        
        Returns:
            float: Consistency Ratio
        """
        if self.n < 2:
            return 0.0
        
        # Consistency Index (CI)
        ci = (self.lambda_max - self.n) / (self.n - 1)
        
        # Consistency Ratio (CR)
        ri = self.RI.get(self.n, 1.49)
        cr = ci / ri if ri > 0 else 0.0
        
        return cr
    
    def is_consistent(self, threshold=0.1):
        """
        Cek apakah matriks konsisten
        
        Args:
            threshold: batas CR (default 0.1)
            
        Returns:
            bool: True jika konsisten
        """
        return self.cr is not None and self.cr < threshold
    
    @staticmethod
    def create_pairwise_matrix(comparisons, n_criteria):
        """
        Membuat matriks perbandingan berpasangan dari dictionary comparisons
        
        Args:
            comparisons: dict dengan key (i,j) dan value = nilai perbandingan
            n_criteria: jumlah kriteria
            
        Returns:
            numpy array: matriks perbandingan berpasangan
        """
        matrix = np.ones((n_criteria, n_criteria))
        
        for (i, j), value in comparisons.items():
            matrix[i][j] = value
            matrix[j][i] = 1.0 / value if value != 0 else 1.0
        
        return matrix


class TOPSISCalculator:
    """
    TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) Calculator
    Menghitung ranking alternatif berdasarkan kedekatan dengan solusi ideal
    """
    
    def __init__(self, decision_matrix, weights, criteria_types):
        """
        Initialize TOPSIS Calculator
        
        Args:
            decision_matrix: numpy array (n_alternatives x n_criteria)
            weights: list bobot kriteria (hasil AHP)
            criteria_types: list tipe kriteria ('benefit' atau 'cost')
        """
        self.matrix = np.array(decision_matrix, dtype=float)
        self.weights = np.array(weights, dtype=float)
        self.criteria_types = criteria_types
        self.n_alternatives, self.n_criteria = self.matrix.shape
        
        self.normalized_matrix = None
        self.weighted_matrix = None
        self.ideal_positive = None
        self.ideal_negative = None
        self.distances_positive = None
        self.distances_negative = None
        self.preference_values = None
        self.rankings = None
    
    def calculate(self):
        """
        Menjalankan perhitungan TOPSIS lengkap
        
        Returns:
            tuple: (preference_values, rankings)
        """
        self.normalize_matrix()
        self.apply_weights()
        self.determine_ideal_solutions()
        self.calculate_distances()
        self.calculate_preference_values()
        self.calculate_rankings()
        
        return self.preference_values, self.rankings
    
    def normalize_matrix(self):
        """
        Normalisasi matriks keputusan menggunakan metode vector normalization
        """
        # Hitung akar kuadrat dari jumlah kuadrat setiap kolom
        column_sums = np.sqrt((self.matrix ** 2).sum(axis=0))
        
        # Hindari pembagian dengan nol
        column_sums[column_sums == 0] = 1.0
        
        # Normalisasi
        self.normalized_matrix = self.matrix / column_sums
    
    def apply_weights(self):
        """
        Kalikan matriks ternormalisasi dengan bobot kriteria
        """
        self.weighted_matrix = self.normalized_matrix * self.weights
    
    def determine_ideal_solutions(self):
        """
        Tentukan solusi ideal positif (A+) dan negatif (A-)
        """
        self.ideal_positive = np.zeros(self.n_criteria)
        self.ideal_negative = np.zeros(self.n_criteria)
        
        for j in range(self.n_criteria):
            if self.criteria_types[j] == 'benefit':
                # Untuk benefit: max adalah ideal positif, min adalah ideal negatif
                self.ideal_positive[j] = self.weighted_matrix[:, j].max()
                self.ideal_negative[j] = self.weighted_matrix[:, j].min()
            else:  # cost
                # Untuk cost: min adalah ideal positif, max adalah ideal negatif
                self.ideal_positive[j] = self.weighted_matrix[:, j].min()
                self.ideal_negative[j] = self.weighted_matrix[:, j].max()
    
    def calculate_distances(self):
        """
        Hitung jarak Euclidean dari setiap alternatif ke solusi ideal
        """
        self.distances_positive = np.sqrt(
            ((self.weighted_matrix - self.ideal_positive) ** 2).sum(axis=1)
        )
        
        self.distances_negative = np.sqrt(
            ((self.weighted_matrix - self.ideal_negative) ** 2).sum(axis=1)
        )
    
    def calculate_preference_values(self):
        """
        Hitung nilai preferensi (V) untuk setiap alternatif
        V = D- / (D+ + D-)
        """
        denominator = self.distances_positive + self.distances_negative
        
        # Hindari pembagian dengan nol
        denominator[denominator == 0] = 1.0
        
        self.preference_values = self.distances_negative / denominator
    
    def calculate_rankings(self):
        """
        Tentukan ranking berdasarkan nilai preferensi (descending)
        """
        # argsort mengurutkan dari kecil ke besar, jadi kita balik
        sorted_indices = np.argsort(-self.preference_values)
        
        # Buat array ranking
        self.rankings = np.empty(self.n_alternatives, dtype=int)
        self.rankings[sorted_indices] = np.arange(1, self.n_alternatives + 1)
    
    def get_results(self):
        """
        Dapatkan hasil lengkap perhitungan TOPSIS
        
        Returns:
            dict: hasil perhitungan
        """
        results = []
        for i in range(self.n_alternatives):
            results.append({
                'index': i,
                'D+': self.distances_positive[i],
                'D-': self.distances_negative[i],
                'V': self.preference_values[i],
                'ranking': self.rankings[i]
            })
        
        # Sort by ranking
        results.sort(key=lambda x: x['ranking'])
        
        return results


# Utility Functions
def validate_pairwise_matrix(matrix):
    """
    Validasi matriks perbandingan berpasangan
    
    Args:
        matrix: numpy array
        
    Returns:
        tuple: (is_valid, error_message)
    """
    n = len(matrix)
    
    # Check if square
    if matrix.shape[0] != matrix.shape[1]:
        return False, "Matriks harus berbentuk persegi"
    
    # Check diagonal = 1
    if not np.allclose(np.diag(matrix), 1.0):
        return False, "Diagonal matriks harus bernilai 1"
    
    # Check reciprocal property
    for i in range(n):
        for j in range(i+1, n):
            if matrix[i][j] > 0:
                expected = 1.0 / matrix[i][j]
                if not np.isclose(matrix[j][i], expected, rtol=0.01):
                    return False, f"Nilai reciprocal tidak konsisten di posisi ({i},{j})"
    
    return True, "Matriks valid"


def print_matrix(matrix, title="Matrix"):
    """Helper function untuk print matrix dengan format rapi"""
    print(f"\n{title}:")
    print("-" * 50)
    for row in matrix:
        print(" ".join([f"{val:8.4f}" for val in row]))
    print("-" * 50)