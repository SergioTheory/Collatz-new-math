import numpy as np
import time

def diagnose_noise():
    M = 22
    B = 22
    mod_B = 1 << B
    
    from e24_spectral_extended import get_hist
    t0 = time.time()
    hist = get_hist(M, B)
    t1 = time.time()
    print(f"DFS completed in {t1-t0:.2f}s")
    
    hist_unrestricted = hist.sum(axis=0)
    fft_un = np.fft.fft(hist_unrestricted)
    fft_un[0] = 0
    mags = np.abs(fft_un)
    
    mags_odd = mags[1::2]
    
    # 1. Total energy (Parseval)
    # Energy = sum(|I(h)|^2)
    # Actually, var = sum(|I(h)|^2) / (mod_B^2) 
    # But let's just look at sum of squared magnitudes for odd h
    total_energy_odd = np.sum(mags_odd ** 2)
    
    # 2. Structural peaks (low frequencies and their aliases)
    # h in [1, 3, 5, 7, 9, 11] and mod_B - h
    structural_h = []
    for h in range(1, 20, 2):
        structural_h.append(h)
        structural_h.append(mod_B - h)
        structural_h.append(mod_B // 2 - h)
        structural_h.append(mod_B // 2 + h)
        
    structural_h = [h for h in structural_h if h > 0 and h < mod_B and h % 2 == 1]
    structural_h = list(set(structural_h))
    
    structural_energy = 0
    for h in structural_h:
        structural_energy += mags[h] ** 2
        
    # 3. Noise tail energy
    noise_energy = total_energy_odd - structural_energy
    
    print(f"Total Odd Energy: {total_energy_odd:.2e}")
    print(f"Structural Energy (h~O(1)): {structural_energy:.2e} ({structural_energy/total_energy_odd*100:.2f}%)")
    print(f"Noise Tail Energy: {noise_energy:.2e} ({noise_energy/total_energy_odd*100:.2f}%)")
    
    # Analyze decay of noise
    # Exclude structural
    mags_noise = np.array([mags[h] for h in range(1, mod_B, 2) if h not in structural_h])
    
    max_noise = np.max(mags_noise)
    mean_noise = np.mean(mags_noise)
    
    total_words = hist.sum()
    print(f"\nMax Noise Magnitude: {max_noise:.2f} (Normalized: {max_noise/total_words:.6f})")
    print(f"Mean Noise Magnitude: {mean_noise:.2f} (Normalized: {mean_noise/total_words:.6f})")
    
    # Theoretical decay
    print(f"Theoretical decay expectation 2^{{-B/2}} = {2**(-B/2):.6f}")
    print(f"Ratio of Max Noise to Theoretical: {(max_noise/total_words) / (2**(-B/2)):.2f}")

if __name__ == "__main__":
    diagnose_noise()
