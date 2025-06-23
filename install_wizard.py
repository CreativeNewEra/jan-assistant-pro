#!/usr/bin/env python3
"""
Jan Assistant Pro - Advanced Installer with Configuration Wizard
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Ensure setup/ is a package and import modules normally
try:
    from setup.system_check import SystemChecker
    from setup.dependency_manager import DependencyManager
    from setup.config_wizard import ConfigWizard
    from setup.api_providers import APIProviderManager
except ImportError as e:
    print(f"❌ Failed to import setup modules: {e}")
    print("Please ensure you're running this from the project root directory and that 'setup/' contains an __init__.py file.")
    sys.exit(1)

class JanAssistantInstaller:
    """Main installer for Jan Assistant Pro"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.backup_dir = self.project_root / '.installer_backup'
        
    def welcome_message(self):
        """Display welcome message and project info"""
        print("🚀 Jan Assistant Pro - Advanced Installer")
        print("=" * 50)
        print("A powerful, local-first AI assistant with enterprise features")
        print("Compatible with any OpenAI-compatible API")
        print("")
        print("This installer will:")
        print("  • Check system requirements")
        print("  • Install Python dependencies") 
        print("  • Configure API providers interactively")
        print("  • Set up security and preferences")
        print("  • Create optimized configuration files")
        print("")
    
    def check_existing_installation(self) -> bool:
        """Check if there's an existing installation"""
        config_file = self.project_root / 'config' / 'config.json'
        env_file = self.project_root / '.env'
        
        if config_file.exists() or env_file.exists():
            print("⚠️  Existing installation detected!")
            print(f"Found: {config_file if config_file.exists() else env_file}")
            
            choice = input("Continue and overwrite? (y/n): ").lower().strip()
            if choice != 'y':
                print("Installation cancelled.")
                return False
            
            # Create backup
            self._create_backup()
        
        return True
    
    def _create_backup(self):
        """Create backup of existing configuration"""
        import shutil
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_dir / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        files_to_backup = [
            'config/config.json',
            '.env',
            'data/memory.json',
            'data/memory.sqlite'
        ]
        
        backed_up = []
        for file_path in files_to_backup:
            source = self.project_root / file_path
            if source.exists():
                dest = backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                backed_up.append(file_path)
        
        if backed_up:
            print(f"📦 Backup created: {backup_dir}")
            print(f"   Backed up: {', '.join(backed_up)}")
    
    def run_system_checks(self) -> bool:
        """Run comprehensive system checks"""
        print("\n" + "="*50)
        print("🔍 SYSTEM REQUIREMENTS CHECK")
        print("="*50)
        
        checker = SystemChecker()
        results = checker.check_all()
        
        # Show system info
        print("\n🖥️  System Information:")
        info = checker.get_system_info()
        for key, value in info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Show summary
        success = checker.print_summary()
        
        if not success:
            # Try to install missing dependencies
            print("\n🔧 Attempting to install missing dependencies...")
            if checker.install_missing_dependencies():
                print("✅ Dependencies installed, re-checking...")
                # Re-run checks
                results = checker.check_all()
                success = checker.print_summary()
        
        if not success:
            choice = input("\n⚠️  Some checks failed. Continue anyway? (y/n): ")
            if choice.lower().strip() != 'y':
                return False
        
        return True
    
    def install_dependencies(self, dev: bool = False) -> bool:
        """Install Python dependencies"""
        print("\n" + "="*50)
        print("📦 DEPENDENCY INSTALLATION")
        print("="*50)
        
        manager = DependencyManager(self.project_root)
        
        # Show dependency info
        info = manager.get_dependency_info()
        print("Current environment:")
        for key, value in info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Install Poetry if needed and preferred
        if not info['poetry_available'] and info['pyproject_exists']:
            print("\n🎯 Poetry not found but pyproject.toml exists")
            choice = input("Install Poetry for better dependency management? (y/n): ")
            if choice.lower().strip() == 'y':
                if not manager.install_poetry():
                    print("⚠️  Failed to install Poetry, falling back to pip")
        
        # Install dependencies
        print("\n📦 Installing dependencies...")
        success = manager.install_dependencies(dev=dev)
        
        if not success:
            print("❌ Failed to install dependencies")
            choice = input("Continue anyway? (y/n): ")
            return choice.lower().strip() == 'y'
        
        return True
    
    def run_configuration_wizard(self, quick_mode: bool = False) -> bool:
        """Run the interactive configuration wizard"""
        print("\n" + "="*50)
        print("🧙‍♂️ CONFIGURATION WIZARD")
        print("="*50)
        
        wizard = ConfigWizard(self.project_root)
        
        try:
            config = wizard.run_wizard(quick_mode=quick_mode)
            
            # Save configuration
            config_path = wizard.save_config(config)
            env_path = wizard.create_env_file(config)
            
            print(f"\n✅ Configuration files created:")
            print(f"  • {config_path}")
            print(f"  • {env_path}")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  Configuration cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Configuration failed: {e}")
            return False
    
    def test_installation(self) -> bool:
        """Test the installation by importing core modules"""
        print("\n" + "="*50)
        print("🧪 INSTALLATION TEST")
        print("="*50)
        
        test_modules = [
            ('src.core.config', 'Configuration system'),
            ('src.core.api_client', 'API client'),
            ('src.gui.main_window', 'GUI system'),
            ('src.tools.tool_registry', 'Tool system')
        ]
        
        all_passed = True
        
        for module_name, description in test_modules:
            try:
                __import__(module_name)
                print(f"  ✅ {description}")
            except ImportError as e:
                print(f"  ❌ {description}: {e}")
                all_passed = False
        
        # Test configuration loading
        try:
            config_path = self.project_root / 'config' / 'config.json'
            if config_path.exists():
                import json
                with open(config_path) as f:
                    json.load(f)
                print("  ✅ Configuration file valid")
            else:
                print("  ⚠️  No configuration file found")
        except Exception as e:
            print(f"  ❌ Configuration file invalid: {e}")
            all_passed = False
        
        return all_passed
    
    def create_startup_script(self):
        """Create convenient startup script"""
        script_content = '''#!/bin/bash
# Jan Assistant Pro Startup Script

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -f "poetry.lock" ] && command -v poetry &> /dev/null; then
    echo "🚀 Starting Jan Assistant Pro with Poetry..."
    poetry run python main.py
elif [ -d ".venv" ]; then
    echo "🚀 Starting Jan Assistant Pro with venv..."
    source .venv/bin/activate
    python main.py
else
    echo "🚀 Starting Jan Assistant Pro..."
    python main.py
fi
'''
        
        script_path = self.project_root / 'start.sh'
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        print(f"✅ Startup script created: {script_path}")
        print("   You can now run: ./start.sh")
    
    def finalize_installation(self):
        """Finalize the installation"""
        print("\n" + "="*50)
        print("🎉 INSTALLATION COMPLETE!")
        print("="*50)
        
        print("Jan Assistant Pro has been successfully installed!")
        print("")
        print("📁 Project structure:")
        print("  • config/config.json - Main configuration")
        print("  • .env - Environment variables")
        print("  • data/ - Runtime data and cache")
        print("  • start.sh - Convenient startup script")
        print("")
        print("🚀 To start the application:")
        print("  1. Run: ./start.sh")
        print("  2. Or: python main.py")
        print("")
        print("📖 For help and documentation:")
        print("  • README.md - Project documentation")
        print("  • docs/ - Detailed documentation")
        print("  • https://github.com/CreativeNewEra/jan-assistant-pro")
        print("")
        print("💡 Tips:")
        print("  • Check config/config.json to customize settings")
        print("  • Use environment variables for sensitive data")
        print("  • Run 'make test' to verify installation")

def main():
    """Main installer entry point"""
    parser = argparse.ArgumentParser(
        description="Jan Assistant Pro Advanced Installer"
    )
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Quick setup with minimal interaction'
    )
    parser.add_argument(
        '--dev',
        action='store_true', 
        help='Install development dependencies'
    )
    parser.add_argument(
        '--provider',
        help='Pre-select API provider (openai, anthropic, jan, etc.)'
    )
    parser.add_argument(
        '--api-key',
        help='Pre-set API key for selected provider'
    )
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip system requirement checks (not recommended)'
    )
    
    args = parser.parse_args()
    
    # Initialize installer
    installer = JanAssistantInstaller()
    
    try:
        # Welcome message
        installer.welcome_message()
        
        # Check existing installation
        if not installer.check_existing_installation():
            sys.exit(1)
        
        # System checks
        if not args.skip_checks:
            if not installer.run_system_checks():
                print("❌ System checks failed")
                sys.exit(1)
        
        # Install dependencies
        if not installer.install_dependencies(dev=args.dev):
            print("❌ Dependency installation failed")
            sys.exit(1)
        
        # Configuration wizard
        if not installer.run_configuration_wizard(quick_mode=args.quick):
            print("❌ Configuration failed")
            sys.exit(1)
        
        # Test installation
        if not installer.test_installation():
            print("⚠️  Some installation tests failed")
            choice = input("Continue anyway? (y/n): ")
            if choice.lower().strip() != 'y':
                sys.exit(1)
        
        # Create startup script
        installer.create_startup_script()
        
        # Finalize
        installer.finalize_installation()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        print("Please check the error message and try again")
        sys.exit(1)

if __name__ == '__main__':
    main()
