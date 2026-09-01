"""
Launch CAMATIS Metrics Dashboard
Quick launcher for the comprehensive metrics visualization
"""

import subprocess
import sys

print("="*70)
print("LAUNCHING CAMATIS METRICS DASHBOARD")
print("="*70)
print("\n📊 Starting Streamlit dashboard...")
print("🌐 Dashboard will open in your browser automatically")
print("\n💡 To stop the dashboard, press Ctrl+C in this terminal\n")
print("="*70)

try:
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "camatis/metrics_dashboard.py",
        "--server.port=8501",
        "--server.headless=false"
    ])
except KeyboardInterrupt:
    print("\n\n✅ Dashboard stopped successfully")
except Exception as e:
    print(f"\n❌ Error launching dashboard: {e}")
    print("\n💡 Try running manually:")
    print("   streamlit run camatis/metrics_dashboard.py")
