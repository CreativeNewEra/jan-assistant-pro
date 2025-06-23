"""
System requirements validation for Jan Assistant Pro
"""

import os
import sys
import shutil
import subprocess
import platform
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class SystemChecker:
    """Validates system requirements and dependencies"""
    
    def __init__(self):
        self.requirements = {
            'python_version': (3, 8),
            'required_modules': ['tkinter', 'sqlite3'],
            'optional_modules': ['keyring'],
            'system_commands': ['git'],
        }
        self.results = {}
    
    def check_all(self) -> Dict[str, bool]:
        """Run all system checks and return results"""
        print("🔍 Checking system requirements...")
        
        checks = [
            ('python_version', self.check_python_version),
            ('package_manager', self.check_package_manager),
            ('required_modules', self.check_required_modules),
            ('tkinter', self.check_tkinter),
            ('network', self.check_network),
            ('permissions', self.check_permissions),
        ]
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                self.results[check_name] = result
                status = "✅" if result else "❌"
                print(f"  {status} {check_name.replace('_', ' ').title()}")
            except Exception as e:
                self.results[check_name] = False
                print(f"  ❌ {check_name.replace('_', ' ').title()}: {e}")
        
        return self.results
    
    def check_python_version(self) -> bool:
        """Check if Python version meets requirements"""
        current = sys.version_info[:2]
        required = self.requirements['python_version']
        
        if current >= required:
            print(f"    Python {'.'.join(map(str, current))} ≥ {'.'.join(map(str, required))}")
            return True
        else:
            print(f"    Python {'.'.join(map(str, current))} < {'.'.join(map(str, required))} (required)")
            return False
    
    def check_package_manager(self) -> bool:
        """Check for Poetry or pip availability"""
        managers = []
        
        # Check for Poetry
        if shutil.which('poetry'):
            try:
                result = subprocess.run(['poetry', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    managers.append(f"Poetry {result.stdout.strip().split()[-1]}")
            except Exception:
                pass
        
        # Check for pip
        if shutil.which('pip') or shutil.which('pip3'):
            try:
                pip_cmd = 'pip3' if shutil.which('pip3') else 'pip'
                result = subprocess.run([pip_cmd, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version = result.stdout.strip().split()[1]
                    managers.append(f"pip {version}")
            except Exception:
                pass
        
        if managers:
            print(f"    Found: {', '.join(managers)}")
            return True
        else:
            print("    No package manager found (Poetry or pip required)")
            return False
    
    def check_required_modules(self) -> bool:
        """Check if required Python modules are available"""
        missing = []
        
        for module in self.requirements['required_modules']:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            print(f"    Missing modules: {', '.join(missing)}")
            return False
        else:
            print(f"    All required modules available")
            return True
    
    def check_tkinter(self) -> bool:
        """Special check for tkinter GUI support"""
        try:
            import tkinter
            # Try to create a root window (but don't show it)
            root = tkinter.Tk()
            root.withdraw()
            root.destroy()
            print("    GUI support available")
            return True
        except Exception as e:
            print(f"    GUI support unavailable: {e}")
            if platform.system() == 'Linux':
                print("    Try: sudo apt-get install python3-tk")
            return False
    
    def check_network(self) -> bool:
        """Check basic network connectivity"""
        try:
            import urllib.request
            urllib.request.urlopen('https://httpbin.org/status/200', timeout=5)
            print("    Internet connectivity available")
            return True
        except Exception:
            print("    Limited or no internet connectivity")
            return False
    
    def check_permissions(self) -> bool:
        """Check write permissions in current directory"""
        try:
            test_file = Path('.') / '.test_permissions'
            test_file.write_text('test')
            test_file.unlink()
            
            # Check if we can create subdirectories
            test_dir = Path('.') / '.test_dir'
            test_dir.mkdir(exist_ok=True)
            test_dir.rmdir()
            
            print("    Write permissions available")
            return True
        except Exception as e:
            print(f"    Insufficient permissions: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, str]:
        """Get detailed system information"""
        return {
            'platform': platform.platform(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'architecture': platform.architecture()[0],
            'processor': platform.processor() or platform.machine(),
            'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            'home_dir': str(Path.home()),
            'current_dir': str(Path.cwd()),
        }
    
    def install_missing_dependencies(self) -> bool:
        """Attempt to install missing system dependencies"""
        system = platform.system().lower()
        
        if system == 'linux':
            return self._install_linux_dependencies()
        elif system == 'darwin':  # macOS
            return self._install_macos_dependencies()
        else:
            print("⚠️  Manual dependency installation may be required on Windows")
            return True
    
    def _install_linux_dependencies(self) -> bool:
        """Install dependencies on Linux systems"""
        if not self.results.get('tkinter', True):
            print("🔧 Installing tkinter...")
            try:
                # Try common package managers
                for cmd in [
                    ['sudo', 'apt-get', 'install', '-y', 'python3-tk'],
                    ['sudo', 'yum', 'install', '-y', 'tkinter'],
                    ['sudo', 'pacman', '-S', '--noconfirm', 'tk'],
                ]:
                    if shutil.which(cmd[1]):
                        result = subprocess.run(cmd, capture_output=True)
                        if result.returncode == 0:
                            print("  ✅ tkinter installed successfully")
                            return True
                        break
                
                print("  ⚠️  Could not install tkinter automatically")
                print("     Please install manually: sudo apt-get install python3-tk")
                return False
            except Exception as e:
                print(f"  ❌ Failed to install tkinter: {e}")
                return False
        
        return True
    
    def _install_macos_dependencies(self) -> bool:
        """Install dependencies on macOS"""
        # tkinter should be included with Python on macOS
        if not self.results.get('tkinter', True):
            print("⚠️  tkinter should be included with Python on macOS")
            print("   Try reinstalling Python from python.org or using Homebrew")
        
        return True
    
    def print_summary(self):
        """Print a summary of all checks"""
        print("\n" + "="*50)
        print("📋 SYSTEM CHECK SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)
        
        for check, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check.replace('_', ' ').title():20} {status}")
        
        print(f"\nResults: {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 All system requirements met!")
            return True
        else:
            print("⚠️  Some requirements not met. Installation may fail.")
            return False

def main():
    """Run system check as standalone script"""
    checker = SystemChecker()
    results = checker.check_all()
    
    print("\n🖥️  System Information:")
    info = checker.get_system_info()
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    checker.print_summary()
    
    if not all(results.values()):
        sys.exit(1)

if __name__ == '__main__':
    main()
