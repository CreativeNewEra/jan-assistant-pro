"""
Interactive configuration wizard for Jan Assistant Pro
"""

import json
import getpass
from pathlib import Path
from typing import Dict, Optional, List, Any

from .api_providers import APIProviderManager, APIProvider

class ConfigWizard:
    """Interactive configuration wizard"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / 'config'
        self.data_dir = project_root / 'data'
        self.provider_manager = APIProviderManager()
        self.config = {}
        
    def run_wizard(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run the full configuration wizard"""
        print("🧙‍♂️ Jan Assistant Pro Configuration Wizard")
        print("=" * 50)
        
        # Create directories
        self._create_directories()
        
        if quick_mode:
            return self._quick_setup()
        else:
            return self._interactive_setup()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.config_dir,
            self.data_dir,
            self.data_dir / 'cache',
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")
    
    def _quick_setup(self) -> Dict[str, Any]:
        """Quick setup with minimal interaction"""
        print("\n⚡ Quick Setup Mode")
        print("Using default configuration with local service detection...")
        
        # Detect local services
        self.provider_manager.detect_local_services()
        
        # Find first available local service
        local_provider = None
        for name, detected in self.provider_manager.detected_services.items():
            if detected:
                local_provider = self.provider_manager.providers[name]
                break
        
        if local_provider:
            print(f"✅ Using {local_provider.display_name}")
            config = self.provider_manager.generate_config(local_provider.name)
        else:
            print("⚠️  No local services detected, using OpenAI defaults")
            config = self._get_default_config()
        
        # Add default settings
        config.update(self._get_default_settings())
        
        return config
    
    def _interactive_setup(self) -> Dict[str, Any]:
        """Full interactive setup"""
        print("\n🔧 Interactive Setup")
        
        # Step 1: API Provider Selection
        api_config = self._configure_api_provider()
        
        # Step 2: Security Settings
        security_config = self._configure_security()
        
        # Step 3: UI Preferences
        ui_config = self._configure_ui()
        
        # Step 4: Advanced Features
        features_config = self._configure_features()
        
        # Combine all configurations
        config = {
            **api_config,
            "security": security_config,
            "ui": ui_config,
            "tools": features_config,
            **self._get_default_settings()
        }
        
        return config
    
    def _configure_api_provider(self) -> Dict[str, Any]:
        """Configure API provider interactively"""
        print("\n🌐 API Provider Configuration")
        print("-" * 30)
        
        # Detect local services first
        self.provider_manager.detect_local_services()
        
        # Get provider choices
        choices = self.provider_manager.get_provider_choices()
        
        print("\nAvailable API providers:")
        for i, (key, display) in enumerate(choices, 1):
            print(f"  {i}. {display}")
        
        # Get user selection
        while True:
            try:
                choice = input(f"\nSelect provider (1-{len(choices)}): ").strip()
                if not choice:
                    continue
                    
                idx = int(choice) - 1
                if 0 <= idx < len(choices):
                    provider_key, _ = choices[idx]
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        # Handle different provider types
        if provider_key == 'skip':
            print("⏭️  Skipping API configuration")
            return self._get_default_config()
        elif provider_key == 'custom':
            return self._configure_custom_provider()
        else:
            return self._configure_known_provider(provider_key)
    
    def _configure_known_provider(self, provider_key: str) -> Dict[str, Any]:
        """Configure a known provider"""
        provider = self.provider_manager.providers[provider_key]
        
        print(f"\n🔧 Configuring {provider.display_name}")
        print(f"Description: {provider.description}")
        
        api_key = None
        
        # Get API key if required
        if provider.requires_key:
            while True:
                api_key = getpass.getpass(
                    f"Enter API key for {provider.display_name}: "
                ).strip()
                
                if not api_key:
                    print("API key is required for this provider.")
                    continue
                
                # Test the connection
                print("🧪 Testing connection...")
                success, message = self.provider_manager.test_provider_connection(
                    provider, api_key
                )
                
                if success:
                    print("✅ Connection successful!")
                    break
                else:
                    print(f"❌ Connection failed: {message}")
                    retry = input("Try again? (y/n): ").lower().strip()
                    if retry != 'y':
                        break
        
        # Select model
        model = self._select_model(provider)
        
        # Generate configuration
        config = self.provider_manager.generate_config(
            provider_key, api_key, model
        )
        
        return config
    
    def _configure_custom_provider(self) -> Dict[str, Any]:
        """Configure a custom OpenAI-compatible provider"""
        print("\n🛠️  Custom Provider Configuration")
        
        while True:
            name = input("Provider name: ").strip()
            if name:
                break
            print("Provider name is required.")
        
        while True:
            base_url = input("Base URL (e.g., http://localhost:8080/v1): ").strip()
            if base_url:
                break
            print("Base URL is required.")
        
        requires_key = input("Requires API key? (y/n): ").lower().strip() == 'y'
        
        api_key = None
        if requires_key:
            api_key = getpass.getpass("API key (optional): ").strip() or None
        
        # Create custom provider
        provider = self.provider_manager.create_custom_provider(
            name, base_url, requires_key=requires_key
        )
        
        # Test connection if possible
        if api_key or not requires_key:
            print("🧪 Testing connection...")
            success, message = self.provider_manager.test_provider_connection(
                provider, api_key
            )
            
            if success:
                print("✅ Connection successful!")
                # Try to get models
                models = self.provider_manager._get_available_models(provider)
                if models:
                    provider.models = models
            else:
                print(f"⚠️  Connection test failed: {message}")
        
        # Select model
        model = self._select_model(provider)
        
        return self.provider_manager.generate_config(name, api_key, model)
    
    def _select_model(self, provider: APIProvider) -> Optional[str]:
        """Interactive model selection"""
        if not provider.models:
            model = input(f"Model name (default: {provider.default_model or 'gpt-3.5-turbo'}): ").strip()
            return model or provider.default_model or 'gpt-3.5-turbo'
        
        print(f"\nAvailable models for {provider.display_name}:")
        for i, model in enumerate(provider.models, 1):
            default_marker = " (default)" if model == provider.default_model else ""
            print(f"  {i}. {model}{default_marker}")
        
        while True:
            choice = input(f"Select model (1-{len(provider.models)}) or press Enter for default: ").strip()
            
            if not choice:
                return provider.default_model or provider.models[0]
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(provider.models):
                    return provider.models[idx]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number or press Enter for default.")
    
    def _configure_security(self) -> Dict[str, Any]:
        """Configure security settings"""
        print("\n🔒 Security Configuration")
        print("-" * 25)
        
        security_levels = [
            ("strict", "Strict - Minimal permissions, restricted commands"),
            ("moderate", "Moderate - Balanced security and functionality"),
            ("permissive", "Permissive - Maximum functionality, less restrictions")
        ]
        
        print("Security levels:")
        for i, (level, description) in enumerate(security_levels, 1):
            print(f"  {i}. {description}")
        
        while True:
            choice = input("Select security level (1-3, default: 2): ").strip() or "2"
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(security_levels):
                    level = security_levels[idx][0]
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        return self._get_security_config(level)
    
    def _configure_ui(self) -> Dict[str, Any]:
        """Configure UI preferences"""
        print("\n🎨 UI Configuration")
        print("-" * 18)
        
        theme = input("Theme (dark/light, default: dark): ").strip() or "dark"
        window_size = input("Window size (default: 800x600): ").strip() or "800x600"
        
        return {
            "theme": theme,
            "window_size": window_size,
            "font_family": "Consolas",
            "font_size": 10
        }
    
    def _configure_features(self) -> Dict[str, Any]:
        """Configure feature toggles"""
        print("\n⚙️  Feature Configuration")
        print("-" * 22)
        
        features = [
            ("file_operations", "File operations (read, write, list files)"),
            ("system_commands", "System commands (execute terminal commands)"),
            ("memory_operations", "Memory operations (persistent memory)"),
            ("web_search", "Web search capabilities (if available)")
        ]
        
        config = {}
        
        for key, description in features:
            default = "y" if key != "web_search" else "n"
            choice = input(f"Enable {description}? (y/n, default: {default}): ").strip() or default
            config[key] = choice.lower() == 'y'
        
        return config
    
    def _get_security_config(self, level: str) -> Dict[str, Any]:
        """Get security configuration for the specified level"""
        base_config = {
            "allowed_commands": ["ls", "pwd", "date", "whoami", "echo"],
            "blocked_commands": ["rm", "shutdown", "reboot"],
            "restricted_paths": ["/etc", "/sys", "/proc"],
            "command_timeout": 30,
            "max_command_output": "20KB",
            "sandbox_dir": "sandbox",
            "max_file_size": "10MB"
        }
        
        if level == "strict":
            base_config["allowed_commands"] = ["ls", "pwd", "date", "whoami"]
            base_config["restricted_paths"].extend(["/home", "/root"])
            base_config["max_file_size"] = "1MB"
        elif level == "permissive":
            base_config["allowed_commands"].extend([
                "cat", "head", "tail", "grep", "find", "python3", "pip"
            ])
            base_config["max_file_size"] = "100MB"
        
        return base_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default API configuration"""
        return {
            "api": {
                "base_url": "http://127.0.0.1:1337/v1",
                "api_key": "your-api-key",
                "model": "gpt-3.5-turbo",
                "timeout": 30
            }
        }
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default non-API settings"""
        return {
            "memory": {
                "file": "data/memory.json",
                "db": "data/memory.sqlite",
                "max_entries": 1000,
                "auto_save": True
            },
            "cache": {
                "config": {"ttl": 300, "size": 4}
            }
        }
    
    def save_config(self, config: Dict[str, Any]) -> Path:
        """Save configuration to file"""
        config_path = self.config_dir / 'config.json'
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"💾 Configuration saved to {config_path}")
        return config_path
    
    def create_env_file(self, config: Dict[str, Any]) -> Path:
        """Create .env file from configuration"""
        env_path = self.project_root / '.env'
        
        env_content = [
            "# Jan Assistant Pro Environment Configuration",
            "# Generated by configuration wizard",
            "",
        ]
        
        # Extract API settings
        api_config = config.get('api', {})
        if 'base_url' in api_config:
            env_content.append(f"JAN_ASSISTANT_API_BASE_URL={api_config['base_url']}")
        if 'api_key' in api_config:
            env_content.append(f"JAN_ASSISTANT_API_KEY={api_config['api_key']}")
        if 'model' in api_config:
            env_content.append(f"JAN_ASSISTANT_API_MODEL={api_config['model']}")
        
        env_content.extend([
            "",
            "# Security Settings",
            "JAN_ASSISTANT_DEBUG=false",
            "JAN_ASSISTANT_LOG_LEVEL=INFO",
            "",
            "# Memory Configuration", 
            "JAN_ASSISTANT_MEMORY_MAX_ENTRIES=1000"
        ])
        
        with open(env_path, 'w') as f:
            f.write('\n'.join(env_content))
        
        print(f"🔧 Environment file created: {env_path}")
        return env_path

def main():
    """Run configuration wizard as standalone script"""
    wizard = ConfigWizard(Path.cwd())
    config = wizard.run_wizard()
    wizard.save_config(config)
    wizard.create_env_file(config)
    
    print("\n🎉 Configuration complete!")
    print("You can now run: python main.py")

if __name__ == '__main__':
    main()
