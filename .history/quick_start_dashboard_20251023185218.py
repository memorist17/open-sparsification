#!/usr/bin/env python3
"""
Quick Start Dashboard - Simplified version with mock data if needed
"""

import sys
import subprocess
from pathlib import Path

def check_and_install_packages():
    """Check and install required packages."""
    required = {
        'numpy': 'numpy',
        'pandas': 'pandas',
        'dash': 'dash',
        'plotly': 'plotly'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (will install)")
            missing.append(package)
    
    if missing:
        print(f"\nInstalling {len(missing)} packages...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--quiet'
        ] + missing)
        print("✓ Installation complete")
    
    return True

def create_mock_data():
    """Create mock data for demo."""
    import numpy as np
    import pandas as pd
    import json
    
    output_dir = Path('demo_output')
    
    patterns = {
        'clustered': {'lac_mult': 2.5, 'rp': 150, 'delta_alpha': 0.45},
        'random': {'lac_mult': 1.1, 'rp': 80, 'delta_alpha': 0.15},
        'grid': {'lac_mult': 1.05, 'rp': 50, 'delta_alpha': 0.05}
    }
    
    for pattern, params in patterns.items():
        pattern_dir = output_dir / pattern
        pattern_dir.mkdir(parents=True, exist_ok=True)
        
        # Lacunarity
        scales = [10, 25, 50, 100, 200, 400, 600]
        lac_values = [params['lac_mult'] * (1 + 0.3 * np.log10(s/10)) for s in scales]
        lac_df = pd.DataFrame({
            'scale_pixels': [s//5 for s in scales],
            'scale_meters': scales,
            'lacunarity': lac_values,
            'scale_category': ['small']*2 + ['medium']*2 + ['large']*3
        })
        lac_df.to_csv(pattern_dir / f'{pattern}_lacunarity.csv', index=False)
        
        # Percolation
        thresholds = [10, 25, 50, 100, 200, 400, 800]
        rp = params['rp']
        s1_ratios = [min(1.0, (t/rp)**2) if t < rp else 1.0 for t in thresholds]
        perc_df = pd.DataFrame({
            'threshold': thresholds,
            'S1_ratio': s1_ratios,
            'n_components': [10-int(9*r) for r in s1_ratios],
            'avg_degree': [r * 15 for r in s1_ratios],
            'clustering': [0.3 + 0.4*r for r in s1_ratios],
            'avg_path_length': [50*(1-r) + 5 for r in s1_ratios]
        })
        perc_df.to_csv(pattern_dir / f'{pattern}_percolation.csv', index=False)
        
        # Multifractal
        q_vals = [-5, -3, -2, -1, 0, 0.5, 1, 1.5, 2, 3, 5]
        d0 = 1.8
        delta = params['delta_alpha']
        d_q = [d0 - delta * abs(q) * 0.1 for q in q_vals]
        alpha = [d0 - delta * q * 0.15 for q in q_vals]
        f_alpha = [d0 - 0.5 * ((a - d0) / delta)**2 if delta > 0 else d0 for a in alpha]
        
        mf_df = pd.DataFrame({
            'q': q_vals,
            'tau_q': [d * (q-1) for d, q in zip(d_q, q_vals)],
            'D_q': d_q,
            'alpha': alpha,
            'f_alpha': f_alpha
        })
        mf_df.to_csv(pattern_dir / f'{pattern}_multifractal.csv', index=False)
        
        # Summary
        summary = {
            'n_points': 500,
            'lacunarity_small': float(lac_values[0]),
            'lacunarity_medium': float(lac_values[3]),
            'lacunarity_large': float(lac_values[5]),
            'percolation_r_p': rp,
            'percolation_max_S1_ratio': 1.0,
            'percolation_critical_degree': s1_ratios[3] * 15,
            'multifractal_D0': d0,
            'multifractal_D1': d_q[6],
            'multifractal_D2': d_q[8],
            'multifractal_Delta_alpha': delta,
            'multifractal_alpha_min': min(alpha),
            'multifractal_alpha_max': max(alpha)
        }
        
        with open(pattern_dir / f'{pattern}_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
    
    print(f"✓ Mock data created in {output_dir}/")
    return output_dir

def main():
    print("="*60)
    print("🚀 OpenSparsity Dashboard Quick Start")
    print("="*60)
    print()
    
    # Check packages
    print("1. Checking dependencies...")
    if not check_and_install_packages():
        print("Failed to install dependencies")
        return
    print()
    
    # Create data if needed
    print("2. Preparing data...")
    data_dir = Path('demo_output')
    if not data_dir.exists() or not list(data_dir.iterdir()):
        print("Creating mock demo data...")
        create_mock_data()
    else:
        print(f"✓ Data found in {data_dir}/")
    print()
    
    # Import and run dashboard
    print("3. Starting dashboard...")
    print("="*60)
    print()
    
    try:
        # Import here after packages are installed
        import dashboard
        app = dashboard.create_app(str(data_dir))
        
        if app:
            print("🌐 Dashboard running at: http://127.0.0.1:8050")
            print()
            print("Press Ctrl+C to stop")
            print("="*60)
            print()
            
            app.run_server(debug=False, host='127.0.0.1', port=8050)
        else:
            print("Failed to create dashboard")
    
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

