"""
Memory management system for Jan Assistant Pro
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import threading


class MemoryManager:
    """Manages persistent memory for the assistant.

    The class uses :class:`threading.RLock`, a reentrant lock, so that
    methods such as ``remember`` or ``recall`` can call ``save_memory``
    while already holding the lock without causing a deadlock.
    """
    
    def __init__(self, memory_file: str, max_entries: int = 1000, auto_save: bool = True):
        self.memory_file = memory_file
        self.max_entries = max_entries
        self.auto_save = auto_save
        self.memory_data = {}
        self._lock = threading.RLock()
        
        # Ensure directory exists
        self._ensure_memory_dir()
        
        # Load existing memory
        self.load_memory()
    
    def _ensure_memory_dir(self):
        """Ensure the memory directory exists"""
        memory_dir = os.path.dirname(self.memory_file)
        if memory_dir and not os.path.exists(memory_dir):
            os.makedirs(memory_dir, exist_ok=True)
    
    def load_memory(self) -> bool:
        """
        Load memory from file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        with self._lock:
            try:
                if os.path.exists(self.memory_file):
                    with open(self.memory_file, 'r', encoding='utf-8') as f:
                        self.memory_data = json.load(f)
                    return True
                else:
                    self.memory_data = {}
                    return True
            except Exception as e:
                print(f"Error loading memory: {e}")
                self.memory_data = {}
                return False
    
    def save_memory(self) -> bool:
        """
        Save memory to file
        
        Returns:
            True if saved successfully, False otherwise
        """
        with self._lock:
            try:
                # Clean up old entries if we exceed max_entries
                if len(self.memory_data) > self.max_entries:
                    self._cleanup_old_entries()
                
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(self.memory_data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"Error saving memory: {e}")
                return False
    
    def _cleanup_old_entries(self):
        """Remove oldest entries to stay within max_entries limit"""
        if len(self.memory_data) <= self.max_entries:
            return
        
        # Sort by timestamp and keep only the most recent entries
        sorted_items = sorted(
            self.memory_data.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        # Keep only the most recent max_entries
        self.memory_data = dict(sorted_items[:self.max_entries])
    
    def remember(self, key: str, value: str, category: str = "general") -> bool:
        """
        Store a memory entry
        
        Args:
            key: The key to store the memory under
            value: The value to remember
            category: Optional category for organization
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            try:
                self.memory_data[key] = {
                    'value': value,
                    'category': category,
                    'timestamp': datetime.now().isoformat(),
                    'access_count': 0
                }
                
                if self.auto_save:
                    self.save_memory()
                
                return True
            except Exception as e:
                print(f"Error storing memory: {e}")
                return False
    
    def recall(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory entry
        
        Args:
            key: The key to recall
            
        Returns:
            Memory entry dictionary or None if not found
        """
        with self._lock:
            if key in self.memory_data:
                # Update access count
                self.memory_data[key]['access_count'] += 1
                self.memory_data[key]['last_accessed'] = datetime.now().isoformat()
                
                if self.auto_save:
                    self.save_memory()
                
                return self.memory_data[key].copy()
            
            return None
    
    def fuzzy_recall(self, search_term: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Search for memories using fuzzy matching
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of (key, memory) tuples that match
        """
        search_term = search_term.lower().strip()
        matches = []
        
        with self._lock:
            for key, memory in self.memory_data.items():
                key_lower = key.lower()
                value_lower = memory['value'].lower()
                
                # Exact key match gets highest priority
                if search_term == key_lower:
                    matches.insert(0, (key, memory.copy()))
                # Partial key match
                elif search_term in key_lower or key_lower in search_term:
                    matches.append((key, memory.copy()))
                # Value contains search term
                elif search_term in value_lower:
                    matches.append((key, memory.copy()))
        
        return matches
    
    def forget(self, key: str) -> bool:
        """
        Remove a memory entry
        
        Args:
            key: The key to forget
            
        Returns:
            True if removed successfully
        """
        with self._lock:
            if key in self.memory_data:
                del self.memory_data[key]
                
                if self.auto_save:
                    self.save_memory()
                
                return True
            return False
    
    def list_memories(self, category: str = None, limit: int = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        List all memories, optionally filtered by category
        
        Args:
            category: Optional category filter
            limit: Optional limit on number of results
            
        Returns:
            List of (key, memory) tuples
        """
        with self._lock:
            memories = []
            
            for key, memory in self.memory_data.items():
                if category is None or memory.get('category') == category:
                    memories.append((key, memory.copy()))
            
            # Sort by timestamp (most recent first)
            memories.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
            
            if limit:
                memories = memories[:limit]
            
            return memories
    
    def get_categories(self) -> List[str]:
        """
        Get all unique categories
        
        Returns:
            List of category names
        """
        with self._lock:
            categories = set()
            for memory in self.memory_data.values():
                categories.add(memory.get('category', 'general'))
            return sorted(list(categories))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics
        
        Returns:
            Dictionary with memory statistics
        """
        with self._lock:
            if not self.memory_data:
                return {
                    'total_entries': 0,
                    'categories': [],
                    'oldest_entry': None,
                    'newest_entry': None,
                    'most_accessed': None
                }
            
            timestamps = [m.get('timestamp', '') for m in self.memory_data.values()]
            access_counts = [(k, m.get('access_count', 0)) for k, m in self.memory_data.items()]
            
            most_accessed = max(access_counts, key=lambda x: x[1]) if access_counts else None
            
            return {
                'total_entries': len(self.memory_data),
                'categories': self.get_categories(),
                'oldest_entry': min(timestamps) if timestamps else None,
                'newest_entry': max(timestamps) if timestamps else None,
                'most_accessed': most_accessed[0] if most_accessed and most_accessed[1] > 0 else None
            }
    
    def clear_all(self) -> bool:
        """
        Clear all memories
        
        Returns:
            True if cleared successfully
        """
        with self._lock:
            try:
                self.memory_data = {}
                if self.auto_save:
                    self.save_memory()
                return True
            except Exception as e:
                print(f"Error clearing memory: {e}")
                return False
    
    def export_memories(self, file_path: str) -> bool:
        """
        Export memories to a file
        
        Args:
            file_path: Path to export to
            
        Returns:
            True if exported successfully
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting memories: {e}")
            return False
    
    def import_memories(self, file_path: str, merge: bool = True) -> bool:
        """
        Import memories from a file
        
        Args:
            file_path: Path to import from
            merge: If True, merge with existing memories. If False, replace all.
            
        Returns:
            True if imported successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            with self._lock:
                if merge:
                    self.memory_data.update(imported_data)
                else:
                    self.memory_data = imported_data
                
                if self.auto_save:
                    self.save_memory()
            
            return True
        except Exception as e:
            print(f"Error importing memories: {e}")
            return False
