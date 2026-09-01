#!/usr/bin/env python3
"""
CAMATIS Execution Script
Run the complete pipeline
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camatis.main_pipeline import main

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   CAMATIS - Causal-Adaptive Multi-Agent Transport Intelligence   ║
    ║                                                                   ║
    ║   A Novel ML/DL Pipeline for Intelligent Transport Systems       ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        pipeline, results = main()
        
        print("\n" + "="*70)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*70)
        print("\n✅ All stages completed successfully!")
        print("\nKey Results:")
        print(f"  - Demand RMSE: {results['evaluation']['passenger_demand']['rmse']:.4f}")
        print(f"  - Load Factor RMSE: {results['evaluation']['load_factor']['rmse']:.4f}")
        print(f"  - Utilization Accuracy: {results['evaluation']['utilization_status']['accuracy']:.4f}")
        
        print("\n📊 Outputs:")
        print(f"  - Models: camatis/models_saved/")
        print(f"  - Results: camatis/results/")
        print(f"  - Logs: camatis/logs/")
        
        print("\n🚀 Next Steps:")
        print("  1. Review results in camatis/results/")
        print("  2. Launch dashboard: streamlit run camatis/dashboard.py")
        print("  3. Analyze uncertainty and anomaly reports")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
