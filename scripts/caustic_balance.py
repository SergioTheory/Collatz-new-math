import json
import numpy as np
from scipy.stats import linregress
import os

def main():
    census_path = r"C:\Users\Admin\Documents\Collatz\data\confluence_census.json"
    algebra_path = r"C:\Users\Admin\Documents\Collatz\data\algebra_centers.json"
    catalog_path = r"C:\Users\Admin\Documents\Collatz\confluence_catalog.json"
    
    unique_centers = {}

    # 1. Load algebra centers (most complete for 14-50)
    if os.path.exists(algebra_path):
        with open(algebra_path, 'r') as f:
            algebra = json.load(f)
            if 'factorization' in algebra:
                for peak_str, data in algebra['factorization'].items():
                    peak = int(peak_str)
                    c_val = int(data['center'])
                    bits = c_val.bit_length()
                    unique_centers[peak] = {
                        'peak': peak,
                        'center': c_val,
                        'bits': bits,
                        'status': 'CONFIRMED',
                        'source': 'Algebra'
                    }

    # 2. Load census
    if os.path.exists(census_path):
        with open(census_path, 'r') as f:
            census = json.load(f)
            
        for item in census.get('results', []):
            if item.get('status') in ['CONFIRMED', 'CANDIDATE']:
                c_val = int(item['center'])
                bits = c_val.bit_length()
                peak = item['peak']
                status = item['status']
                
                notes = item.get('notes', '')
                if 'known:' in notes:
                    try:
                        known_str = notes.split('known:')[1].split(')')[0].strip()
                        c_val = int(known_str)
                        bits = c_val.bit_length()
                        status = 'CONFIRMED'
                    except:
                        pass
                
                if peak not in unique_centers or unique_centers[peak]['status'] != 'CONFIRMED':
                    unique_centers[peak] = {
                        'peak': peak,
                        'center': c_val,
                        'bits': bits,
                        'status': status,
                        'source': 'Census'
                    }
                
    # 3. Add Zone 2 manually and Barina
    if os.path.exists(catalog_path):
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
            for item in catalog:
                if item.get('class_id') == 1:
                    c_val = int(item['canonical_center'])
                    unique_centers[item['peak']] = {
                        'peak': item['peak'],
                        'center': c_val,
                        'bits': c_val.bit_length(),
                        'status': 'CONFIRMED',
                        'source': 'Zone 2'
                    }
                elif item.get('class_id') == 2:
                    c_val = int(item['n'])
                    unique_centers[item['peak']] = { # wait, barina has peak 140 too
                        'peak': item['peak'],
                        'center': c_val,
                        'bits': c_val.bit_length(),
                        'status': 'ISOLATED',
                        'source': 'Barina'
                    }

    final_centers = sorted([c for c in unique_centers.values() if c['source'] != 'Barina'], key=lambda x: x['peak'])
    
    print(f"Total unique centers loaded: {len(final_centers)}")
    
    peaks = []
    bits = []
    alpha_effs = []
    
    print(f"\n{'Peak':<6} | {'Bits':<6} | {'Alpha_eff':<10} | {'Status':<12} | {'Source'}")
    print("-" * 60)
    
    for c in final_centers:
        a_eff = c['bits'] / c['peak']
        peaks.append(c['peak'])
        bits.append(c['bits'])
        alpha_effs.append(a_eff)
        print(f"{c['peak']:<6} | {c['bits']:<6} | {a_eff:<10.4f} | {c['status']:<12} | {c['source']}")
        
    slope, intercept, r_value, p_value, std_err = linregress(peaks, bits)
    
    print("\n--- Caustic Balance Equation ---")
    print(f"Regression: bits(c) = {slope:.4f} * peak + {intercept:.4f}")
    print(f"R-squared: {r_value**2:.4f}")
    
    conf_alpha = [c['bits']/c['peak'] for c in final_centers if c['status'] == 'CONFIRMED']
    cand_alpha = [c['bits']/c['peak'] for c in final_centers if c['status'] == 'CANDIDATE']
    
    print("\n--- Alpha_eff Distribution ---")
    if conf_alpha:
        print(f"Class B (CONFIRMED)   : Mean = {np.mean(conf_alpha):.4f}, Std = {np.std(conf_alpha):.4f}, Min = {np.min(conf_alpha):.4f}, Max = {np.max(conf_alpha):.4f}")
    if cand_alpha:
        print(f"Transitional (CANDID) : Mean = {np.mean(cand_alpha):.4f}, Std = {np.std(cand_alpha):.4f}, Min = {np.min(cand_alpha):.4f}, Max = {np.max(cand_alpha):.4f}")

if __name__ == '__main__':
    main()
