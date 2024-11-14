import os
import hashlib
import logging
from typing import Dict, Optional

class SecurityManager:
    def __init__(self, config_paths: Dict[str, str]):
        self.logger = logging.getLogger('RootBot.security')
        self.config_paths = config_paths
        self.file_hashes = {}
        self._initialize_file_hashes()

    def _initialize_file_hashes(self):
        """Initialize hash values for critical files"""
        for file_type, path in self.config_paths.items():
            if os.path.exists(path):
                self.file_hashes[file_type] = self._calculate_file_hash(path)
                self.logger.info(f"Initialized hash for {file_type}: {self.file_hashes[file_type]}")

    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def verify_file_integrity(self, file_type: str) -> bool:
        """Verify integrity of a critical file"""
        if file_type not in self.config_paths:
            self.logger.error(f"Unknown file type: {file_type}")
            return False

        filepath = self.config_paths[file_type]
        if not os.path.exists(filepath):
            self.logger.error(f"File not found: {filepath}")
            return False

        current_hash = self._calculate_file_hash(filepath)
        expected_hash = self.file_hashes.get(file_type)

        if current_hash != expected_hash:
            self.logger.critical(
                f"File integrity check failed for {file_type}. "
                f"Expected: {expected_hash}, Got: {current_hash}"
            )
            return False

        self.logger.debug(f"File integrity verified for {file_type}")
        return True

    def update_file_hash(self, file_type: str) -> Optional[str]:
        """Update stored hash for a file after legitimate changes"""
        if file_type not in self.config_paths:
            self.logger.error(f"Unknown file type: {file_type}")
            return None

        filepath = self.config_paths[file_type]
        if not os.path.exists(filepath):
            self.logger.error(f"File not found: {filepath}")
            return None

        new_hash = self._calculate_file_hash(filepath)
        self.file_hashes[file_type] = new_hash
        self.logger.info(f"Updated hash for {file_type}: {new_hash}")
        return new_hash
