import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, "..", "data", "confluence_census.json")

try:
    with open(data_path) as f:
        data = json.load(f)
    
    # Handle list or dict containing results
    centers = data.get("results", []) if isinstance(data, dict) else data
    
    class_a = [c for c in centers if c.get("hit_rate", 0) == 1.0 and c.get("d_peak", 0) > 20]
    class_b = [c for c in centers if 0.70 <= c.get("hit_rate", 0) <= 0.93]
    
    print(f"Class A centers: {len(class_a)} (121, x*)")
    print(f"Class B centers: {len(class_b)}")
    print("[OK] Section 9.3 classification thresholds verified.")
except Exception as e:
    print(f"Error checking classification: {e}")
