"""
Dependency management for Jan Assistant Pro installer
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List


class DependencyManager:
    """Manages Python dependencies installation"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.pyproject_path = self.project_root / 'pyproject.toml'
        self.poetry_lock_path = self.project_root / 'poetry.lock'
        self.requirements_path = self.project_root / 'requirements.txt'
        
    def detect_package_manager(self) -> str:
        """Detect the best available package manager"""
        if shutil.which('poetry') and self.pyproject_path.exists():
            return 'poetry'
        elif shutil.which('pip') or shutil.which('pip3'):
            return 'pip'
        else:
            raise RuntimeError(
                "No suitable package manager found (Poetry or pip required)"
            )
    
    def install_poetry(self) -> bool:
        """Install Poetry if not present"""
        if shutil.which('poetry'):
            print("📦 Poetry already installed")
            return True
        
        print("📦 Installing Poetry...")
        try:
            # Use the official Poetry installer
            import urllib.request
            
            with tempfile.NamedTemporaryFile(
                mode='w+b', suffix='.py', delete=False
            ) as f:
                urllib.request.urlretrieve(
                    'https://install.python-poetry.org',
                    f.name
                )
                
                # Run the installer
                result = subprocess.run(
                    [sys.executable, f.name],
                    capture_output=True,
                    text=True
                )
                
                os.unlink(f.name)
                
                if result.returncode == 0:
                    print("  ✅ Poetry installed successfully")
                    # Add to PATH for current session
                    poetry_bin = Path.home() / '.local' / 'bin'
                    if poetry_bin.exists():
                        os.environ['PATH'] = (
                            f"{poetry_bin}:{os.environ['PATH']}"
                        )
                    return True
                else:
                    print(f"  ❌ Failed to install Poetry: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Failed to install Poetry: {e}")
            return False
    
    def install_dependencies(
        self, dev: bool = False, extras: List[str] = None
    ) -> bool:
        """Install project dependencies using the best available method"""
        manager = self.detect_package_manager()
        
        if manager == 'poetry':
            return self._install_with_poetry(dev, extras)
        else:
            return self._install_with_pip(dev, extras)
    
    def _install_with_poetry(
        self, dev: bool = False, extras: List[str] = None
    ) -> bool:
        """Install dependencies using Poetry"""
        print("📦 Installing dependencies with Poetry...")
        
        try:
            # Build the command
            cmd = ['poetry', 'install']
            
            if dev:
                cmd.append('--with=dev')
            
            if extras:
                for extra in extras:
                    cmd.extend(['--extras', extra])
            
            # Run installation with progress
            print(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                text=True,
                capture_output=False  # Show real-time output
            )
            
            if result.returncode == 0:
                print("  ✅ Dependencies installed successfully")
                return True
            else:
                print(
                    f"  ❌ Failed to install dependencies "
                    f"(exit code: {result.returncode})"
                )
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to install with Poetry: {e}")
            return False
    
    def _install_with_pip(
        self, dev: bool = False, extras: List[str] = None
    ) -> bool:
        """Install dependencies using pip"""
        print("📦 Installing dependencies with pip...")
        
        try:
            # Generate requirements.txt from pyproject.toml if it doesn't exist
            if not self.requirements_path.exists():
                if not self._generate_requirements_txt():
                    return False
            
            pip_cmd = 'pip3' if shutil.which('pip3') else 'pip'
            
            # Install main dependencies
            cmd = [pip_cmd, 'install', '-r', str(self.requirements_path)]
            
            print(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root)
            
            if result.returncode != 0:
                print(
                    f"  ❌ Failed to install dependencies "
                    f"(exit code: {result.returncode})"
                )
                return False
            
            # Install development dependencies if requested
            if dev:
                dev_requirements = self.project_root / 'requirements-dev.txt'
                if dev_requirements.exists():
                    cmd = [pip_cmd, 'install', '-r', str(dev_requirements)]
                    print(f"  Running: {' '.join(cmd)}")
                    result = subprocess.run(cmd, cwd=self.project_root)
                    
                    if result.returncode != 0:
                        print("  ⚠️  Failed to install dev dependencies")
            
            print("  ✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to install with pip: {e}")
            return False
    
    def _generate_requirements_txt(self) -> bool:
        """Generate requirements.txt from pyproject.toml"""
        try:
            if not self.pyproject_path.exists():
                print("  ❌ No pyproject.toml found")
                return False
            
            # Try to use poetry export if available
            if shutil.which('poetry'):
                cmd = [
                    'poetry', 'export', '--format', 'requirements.txt', 
                    '--output', str(self.requirements_path)
                ]
                result = subprocess.run(
                    cmd, cwd=self.project_root, capture_output=True
                )
                
                if result.returncode == 0:
                    print("  ✅ Generated requirements.txt from pyproject.toml")
                    return True
            
            # Fallback: extract basic requirements from pyproject.toml
            print("  ⚠️  Generating basic requirements.txt")
            requirements = [
                "requests>=2.31.0",
                "python-dotenv>=1.0.0", 
                "keyring>=24.0",
                "aiohttp>=3.9",
                "prometheus-client>=0.22",
                "cachetools>=5.3"
            ]
            
            self.requirements_path.write_text('\n'.join(requirements))
            print("  ✅ Generated basic requirements.txt")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to generate requirements.txt: {e}")
            return False
    
    def check_virtual_environment(self) -> bool:
        """Check if we're in a virtual environment"""
        return (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
    
    def get_dependency_info(self) -> dict:
        """Get information about current dependencies"""
        info = {
            'virtual_env': self.check_virtual_environment(),
            'package_manager': None,
            'poetry_available': bool(shutil.which('poetry')),
            'pip_available': bool(shutil.which('pip') or shutil.which('pip3')),
            'pyproject_exists': self.pyproject_path.exists(),
            'poetry_lock_exists': self.poetry_lock_path.exists(),
            'requirements_exists': self.requirements_path.exists(),
        }
        
        try:
            info['package_manager'] = self.detect_package_manager()
        except RuntimeError:
            info['package_manager'] = None
            
        return info


def main():
    """Run dependency manager as standalone script"""
    manager = DependencyManager()
    info = manager.get_dependency_info()
    
    print("📦 Dependency Information:")
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if info['package_manager']:
        print(f"\n🔧 Installing dependencies with {info['package_manager']}...")
        success = manager.install_dependencies(dev=True)
        if success:
            print("🎉 All dependencies installed successfully!")
        else:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    else:
        print("❌ No package manager available")
        sys.exit(1)


if __name__ == '__main__':
    main()
