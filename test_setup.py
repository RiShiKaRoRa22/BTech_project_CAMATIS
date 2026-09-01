"""
Test CAMATIS Setup
Verify all dependencies and data files
"""

import sys
import os
from camatis.config import TRAIN_FILE, TEST_FILE

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    
    packages = [
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('sklearn', 'Scikit-learn'),
        ('torch', 'PyTorch'),
        ('lightgbm', 'LightGBM'),
        ('catboost', 'CatBoost'),
        ('xgboost', 'XGBoost'),
        ('networkx', 'NetworkX'),
        ('simpy', 'SimPy'),
        ('streamlit', 'Streamlit'),
        ('plotly', 'Plotly'),
        ('matplotlib', 'Matplotlib'),
        ('seaborn', 'Seaborn')
    ]
    
    failed = []
    for package, name in packages:
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Install with: pip install -r camatis_requirements.txt")
        return False
    else:
        print("\n✅ All packages installed!")
        return True

def test_data_files():
    """Test if data files exist"""
    print("\nTesting data files...")
    
    files = [
        TRAIN_FILE,
        TEST_FILE
    ]
    
    failed = []
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024 * 1024)  # MB
            print(f"  ✓ {file} ({size:.2f} MB)")
        else:
            print(f"  ✗ {file} - NOT FOUND")
            failed.append(file)
    
    if failed:
        print(f"\n❌ Missing data files: {', '.join(failed)}")
        return False
    else:
        print("\n✅ All data files present!")
        return True

def test_data_loading():
    """Test if data can be loaded"""
    print("\nTesting data loading...")
    
    try:
        import pandas as pd
        
        train_df = pd.read_csv(TRAIN_FILE)
        test_df = pd.read_csv(TEST_FILE)
        
        print(f"  ✓ Train data: {train_df.shape}")
        print(f"  ✓ Test data: {test_df.shape}")
        
        required_cols = ['passenger_demand', 'load_factor', 'utilization_encoded']
        missing = [col for col in required_cols if col not in train_df.columns]
        
        if missing:
            print(f"  ✗ Missing columns: {missing}")
            return False
        
        print("\n✅ Data loaded successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Data loading failed: {str(e)}")
        return False

def test_directories():
    """Test if required directories exist or can be created"""
    print("\nTesting directories...")
    
    dirs = [
        'camatis',
        'camatis/models_saved',
        'camatis/results',
        'camatis/logs'
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"  ✓ Created {dir_path}")
            except Exception as e:
                print(f"  ✗ Failed to create {dir_path}: {e}")
                return False
        else:
            print(f"  ✓ {dir_path} exists")
    
    print("\n✅ All directories ready!")
    return True

def test_pytorch():
    """Test PyTorch functionality"""
    print("\nTesting PyTorch...")
    
    try:
        import torch
        
        # Check CUDA availability
        if torch.cuda.is_available():
            print(f"  ✓ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("  ℹ CUDA not available (will use CPU)")
        
        # Test tensor creation
        x = torch.randn(10, 5)
        print(f"  ✓ Tensor creation works: {x.shape}")
        
        print("\n✅ PyTorch working!")
        return True
        
    except Exception as e:
        print(f"\n❌ PyTorch test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("CAMATIS Setup Verification")
    print("="*70)
    
    tests = [
        ("Package Imports", test_imports),
        ("Data Files", test_data_files),
        ("Data Loading", test_data_loading),
        ("Directories", test_directories),
        ("PyTorch", test_pytorch)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {str(e)}")
            results.append((name, False))
        print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED! Ready to run CAMATIS!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Run pipeline: python run_camatis.py")
        print("  2. Launch dashboard: streamlit run camatis/dashboard.py")
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️  SOME TESTS FAILED - Please fix issues above")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
