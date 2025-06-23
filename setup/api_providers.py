"""
API provider configurations for Jan Assistant Pro
"""

import json
import socket
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class APIProvider:
    """Configuration for an API provider"""
    name: str
    display_name: str
    base_url: str
    models: List[str]
    auth_type: str = "bearer"  # bearer, none, custom
    requires_key: bool = True
    auto_detect: bool = False
    default_model: Optional[str] = None
    description: str = ""


class APIProviderManager:
    """Manages API provider configurations and detection"""
    
    def __init__(self):
        self.providers = self._load_default_providers()
        self.detected_services = {}
    
    def _load_default_providers(self) -> Dict[str, APIProvider]:
        """Load predefined API provider configurations"""
        providers = {
            'openai': APIProvider(
                name='openai',
                display_name='OpenAI',
                base_url='https://api.openai.com/v1',
                models=[
                    'gpt-4', 'gpt-4-turbo', 'gpt-4-turbo-preview',
                    'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'
                ],
                default_model='gpt-4',
                description='Official OpenAI API service'
            ),
            
            'anthropic': APIProvider(
                name='anthropic',
                display_name='Anthropic Claude',
                base_url='https://api.anthropic.com/v1',
                models=[
                    'claude-3-opus-20240229',
                    'claude-3-sonnet-20240229',
                    'claude-3-haiku-20240307'
                ],
                default_model='claude-3-sonnet-20240229',
                description='Anthropic Claude API service'
            ),
            
            'jan': APIProvider(
                name='jan',
                display_name='Jan.ai (Local)',
                base_url='http://127.0.0.1:1337/v1',
                models=[],  # Will be detected
                auto_detect=True,
                requires_key=False,
                description='Local Jan.ai instance'
            ),
            
            'ollama': APIProvider(
                name='ollama',
                display_name='Ollama (Local)',
                base_url='http://127.0.0.1:11434/v1',
                models=[],  # Will be detected
                auto_detect=True,
                requires_key=False,
                description='Local Ollama instance'
            ),
            
            'lmstudio': APIProvider(
                name='lmstudio',
                display_name='LM Studio (Local)',
                base_url='http://127.0.0.1:1234/v1',
                models=[],  # Will be detected
                auto_detect=True,
                requires_key=False,
                description='Local LM Studio instance'
            ),
            
            'textgen': APIProvider(
                name='textgen',
                display_name='Text Generation WebUI',
                base_url='http://127.0.0.1:5000/v1',
                models=[],  # Will be detected
                auto_detect=True,
                requires_key=False,
                description='Text Generation WebUI (oobabooga)'
            ),
        }
        
        return providers
    
    def detect_local_services(self) -> Dict[str, bool]:
        """Auto-detect local API services"""
        print("🔍 Detecting local API services...")
        
        results = {}
        
        for name, provider in self.providers.items():
            if provider.auto_detect:
                detected = self._check_service_availability(provider)
                results[name] = detected
                
                status = "✅ Found" if detected else "❌ Not found"
                print(f"  {status}: {provider.display_name}")
                
                if detected:
                    # Try to get available models
                    models = self._get_available_models(provider)
                    if models:
                        provider.models = models
                        print(f"    Models: {', '.join(models[:3])}" + 
                              (f" (+{len(models)-3} more)" if len(models) > 3 else ""))
        
        self.detected_services = results
        return results
    
    def _check_service_availability(self, provider: APIProvider) -> bool:
        """Check if a service is available at the given endpoint"""
        try:
            # Parse URL to get host and port
            from urllib.parse import urlparse
            parsed = urlparse(provider.base_url)
            host = parsed.hostname or 'localhost'
            port = parsed.port
            
            if not port:
                port = 443 if parsed.scheme == 'https' else 80
            
            # Try to connect to the service
            with socket.create_connection((host, port), timeout=2):
                pass
            
            # Try to make a simple API call
            try:
                health_url = f"{provider.base_url.rstrip('/')}/models"
                req = urllib.request.Request(health_url)
                req.add_header('User-Agent', 'Jan-Assistant-Pro-Installer/1.0')
                
                with urllib.request.urlopen(req, timeout=3) as response:
                    if response.status == 200:
                        return True
            except Exception:
                # Some services might not have /models endpoint
                # but still be available
                return True
                
        except Exception:
            pass
        
        return False
    
    def _get_available_models(self, provider: APIProvider) -> List[str]:
        """Get list of available models from a provider"""
        try:
            models_url = f"{provider.base_url.rstrip('/')}/models"
            req = urllib.request.Request(models_url)
            req.add_header('User-Agent', 'Jan-Assistant-Pro-Installer/1.0')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    
                    # Handle different response formats
                    if 'data' in data:
                        # OpenAI format
                        return [model['id'] for model in data['data']]
                    elif 'models' in data:
                        # Alternative format
                        return data['models']
                    elif isinstance(data, list):
                        # Simple list format
                        return [item['id'] if isinstance(item, dict) else str(item) 
                               for item in data]
                        
        except Exception as e:
            print(f"    Could not fetch models: {e}")
        
        return []
    
    def test_provider_connection(
        self, provider: APIProvider, api_key: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Test connection to a specific provider"""
        try:
            # Prepare request
            test_url = f"{provider.base_url.rstrip('/')}/models"
            req = urllib.request.Request(test_url)
            req.add_header('User-Agent', 'Jan-Assistant-Pro-Installer/1.0')
            
            if provider.requires_key and api_key:
                if provider.auth_type == "bearer":
                    req.add_header('Authorization', f'Bearer {api_key}')
            
            # Make request
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, "Connection successful"
                else:
                    return False, f"HTTP {response.status}"
                    
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Invalid API key"
            elif e.code == 403:
                return False, "Access forbidden"
            else:
                return False, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, str(e)
    
    def get_provider_choices(self) -> List[Tuple[str, str]]:
        """Get list of providers for interactive selection"""
        choices = []
        
        # Add detected local services first
        for name, provider in self.providers.items():
            if provider.auto_detect and self.detected_services.get(name, False):
                status = "🟢 Available"
                choices.append((name, f"{provider.display_name} - {status}"))
        
        # Add cloud providers
        for name, provider in self.providers.items():
            if not provider.auto_detect:
                choices.append((name, f"{provider.display_name} - Cloud API"))
        
        # Add custom option
        choices.append(('custom', 'Custom OpenAI-compatible API'))
        choices.append(('skip', 'Skip (configure manually later)'))
        
        return choices
    
    def create_custom_provider(
        self, name: str, base_url: str, models: List[str] = None,
        requires_key: bool = True
    ) -> APIProvider:
        """Create a custom provider configuration"""
        provider = APIProvider(
            name=name,
            display_name=name.title(),
            base_url=base_url,
            models=models or [],
            requires_key=requires_key,
            description="Custom OpenAI-compatible API"
        )
        
        self.providers[name] = provider
        return provider
    
    def generate_config(
        self, provider_name: str, api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """Generate configuration for selected provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        config = {
            "api": {
                "base_url": provider.base_url,
                "model": model or provider.default_model or (
                    provider.models[0] if provider.models else "gpt-3.5-turbo"
                ),
                "timeout": 30
            }
        }
        
        if provider.requires_key and api_key:
            config["api"]["api_key"] = api_key
        
        return config
    
    def save_provider_configs(self, filepath: str):
        """Save provider configurations to file"""
        data = {
            name: asdict(provider) 
            for name, provider in self.providers.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def print_provider_summary(self):
        """Print summary of available providers"""
        print("\n" + "="*50)
        print("🌐 API PROVIDER SUMMARY")
        print("="*50)
        
        local_count = sum(1 for p in self.providers.values() if p.auto_detect)
        cloud_count = sum(1 for p in self.providers.values() if not p.auto_detect)
        detected_count = sum(1 for detected in self.detected_services.values() 
                           if detected)
        
        print(f"Local Services: {detected_count}/{local_count} detected")
        print(f"Cloud Services: {cloud_count} available")
        
        if detected_count > 0:
            print("\n✅ Available local services:")
            for name, detected in self.detected_services.items():
                if detected:
                    provider = self.providers[name]
                    model_info = f" ({len(provider.models)} models)" if provider.models else ""
                    print(f"  • {provider.display_name}{model_info}")


def main():
    """Run API provider detection as standalone script"""
    manager = APIProviderManager()
    manager.detect_local_services()
    manager.print_provider_summary()
    
    # Save detected configurations
    manager.save_provider_configs('detected_providers.json')
    print("\n💾 Provider configurations saved to detected_providers.json")


if __name__ == '__main__':
    main()
