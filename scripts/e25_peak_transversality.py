import numpy as np
import time

def check_peaks():
    # We will just run DFS to collect hist
    M = 22
    B = 22
    mod_B = 1 << B
    
    from e24_spectral_extended import get_hist
    hist = get_hist(M, B)
    
    # 1. Unrestricted
    hist_unrestricted = hist.sum(axis=0)
    fft_un = np.fft.fft(hist_unrestricted)
    fft_un[0] = 0
    mags_un = np.abs(fft_un)
    # Only odd
    mags_un_odd = mags_un[1::2]
    
    # 2. Restricted d=11
    hist_res = hist[11]
    fft_res = np.fft.fft(hist_res)
    fft_res[0] = 0
    mags_res = np.abs(fft_res)
    mags_res_odd = mags_res[1::2]
    
    # Top 10 unrestricted peaks
    top_un_idx = np.argsort(mags_un_odd)[-10:][::-1]
    top_un_h = 2 * top_un_idx + 1
    
    # Top 10 restricted peaks
    top_res_idx = np.argsort(mags_res_odd)[-10:][::-1]
    top_res_h = 2 * top_res_idx + 1
    
    print("=== Top 10 Unrestricted Peaks ===")
    for h in top_un_h:
        print(f"h = {h}, |I(h)| = {mags_un[h]:.2f}")
        
    print("\n=== Top 10 Restricted (d=11) Peaks ===")
    for h in top_res_h:
        print(f"h = {h}, |I_11(h)| = {mags_res[h]:.2f}")
        
    # Check overlap
    overlap = set(top_un_h).intersection(set(top_res_h))
    print(f"\nOverlap between Top 10: {len(overlap)}")
    
    # Check value of unrestricted peaks in restricted spectrum
    print("\n=== Unrestricted Peaks in Restricted Spectrum ===")
    for h in top_un_h:
        print(f"h = {h}, |I_11(h)| = {mags_res[h]:.2f} (Rank: {np.sum(mags_res_odd > mags_res[h])})")
        
    # Check value of restricted peaks in unrestricted spectrum
    print("\n=== Restricted Peaks in Unrestricted Spectrum ===")
    for h in top_res_h:
        print(f"h = {h}, |I(h)| = {mags_un[h]:.2f} (Rank: {np.sum(mags_un_odd > mags_un[h])})")

if __name__ == "__main__":
    check_peaks()
