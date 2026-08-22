import json
import os
import sys

def main():
    print("--- Verifying Confluence Archipelago ---")
    data_path = os.path.join("data", "confluence_census.json")
    if not os.path.exists(data_path):
        print(f"[FAIL] Missing {data_path}")
        return
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    
    centers = []
    for info in results:
        if info.get('status') in ('CONFIRMED', 'CANDIDATE'):
            centers.append({
                'peak': int(info['peak']),
                'center': int(info['center']) if info.get('center') else None
            })
            
    targeted_path = os.path.join("data", "targeted_31_50.json")
    if os.path.exists(targeted_path):
        with open(targeted_path, 'r') as f:
            t_data = json.load(f)
            for item in t_data.get('results', []):
                if item.get('center'):
                    centers.append({
                        'peak': int(item['peak']),
                        'center': int(item['center'])
                    })
                    
    targeted_path2 = os.path.join("data", "targeted_41_50.json")
    if os.path.exists(targeted_path2):
        with open(targeted_path2, 'r') as f:
            t_data = json.load(f)
            for item in t_data.get('results', []):
                if item.get('center'):
                    centers.append({
                        'peak': int(item['peak']),
                        'center': int(item['center'])
                    })

    # Keep unique peaks
    unique_centers = {c['peak']: c for c in centers if c['center'] is not None}
    
    print(f"[OK] Loaded {len(unique_centers)} valid confluence centers (Class A/B).")
    
    mod3_count = 0
    errors = []
    
    for peak, c_data in unique_centers.items():
        c = c_data['center']
        bits = c.bit_length()
        
        # Formula check
        expected_bits = 0.498 * peak + 6.29
        diff = abs(bits - expected_bits)
        errors.append(diff)
        
        if c % 3 == 2:
            mod3_count += 1
            
    if len(errors) == 0:
        print("[FAIL] No valid centers found!")
        return

    avg_error = sum(errors) / len(errors)
    assert avg_error < 2.0, f"Average error for formula is too high: {avg_error}"
    print(f"[OK] Formula center_bits ~ 0.498 * peak + 6.29 validated (avg error {avg_error:.2f} bits).")
    
    mod3_pct = mod3_count / len(unique_centers)
    assert mod3_pct >= 0.85, f"Modulo 3 filter failed, only {mod3_pct:.1%} match"
    print(f"[OK] Modulo filter c = 2 (mod 3) validated for {mod3_pct:.1%} of centers.")

if __name__ == '__main__':
    main()
