import hashlib
import json
import time
import os
from datetime import datetime

class Block:
    """
    A block in the blockchain, containing information about a file
    """
    def __init__(self, index, timestamp, file_id, file_hash, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.file_id = file_id
        self.file_hash = file_hash
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate the hash of the block"""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "file_id": self.file_id,
            "file_hash": self.file_hash,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty=2):
        """Mine a block to meet the difficulty requirement"""
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
        return self.hash
    
    def to_dict(self):
        """Convert block to dictionary for JSON serialization"""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "file_id": self.file_id,
            "file_hash": self.file_hash,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Blockchain:
    """
    A blockchain for tracking file integrity
    """
    def __init__(self, blockchain_file="blockchain.json", difficulty=2):
        self.chain = []
        self.blockchain_file = blockchain_file
        self.difficulty = difficulty
        self.file_histories = {}
        
        # Load existing blockchain or create genesis block
        self.load_chain()
        if len(self.chain) == 0:
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        genesis_block = Block(0, str(datetime.now()), "genesis", "genesis_hash", "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_chain()
        
    def get_latest_block(self):
        """Get the most recent block in the chain"""
        return self.chain[-1]
    
    def create_block(self, file_id, file_hash):
        """Add a new block to the blockchain for a file"""
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        new_timestamp = str(datetime.now())
        previous_hash = previous_block.hash
        
        new_block = Block(new_index, new_timestamp, file_id, file_hash, previous_hash)
        new_block.mine_block(self.difficulty)
        
        # Add to chain
        self.chain.append(new_block)
        
        # Update file history
        if file_id not in self.file_histories:
            self.file_histories[file_id] = []
        
        self.file_histories[file_id].append({
            "timestamp": new_timestamp,
            "file_hash": file_hash,
            "block_index": new_index,
            "block_hash": new_block.hash
        })
        
        # Save the updated chain
        self.save_chain()
        
        return new_block
    
    def verify_chain_integrity(self):
        """Verify the integrity of the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if the hash of the current block is valid
            if current_block.hash != current_block.calculate_hash():
                return False
                
            # Check if the previous hash reference is correct
            if current_block.previous_hash != previous_block.hash:
                return False
                
        return True
    
    def verify_file_integrity(self, file_id, current_hash):
        """
        Verify the integrity of a file by comparing its current hash
        with the hash stored in the blockchain
        """
        if file_id not in self.file_histories:
            return False
            
        # Get the most recent hash for this file
        latest_entry = self.file_histories[file_id][-1]
        stored_hash = latest_entry["file_hash"]
        
        return stored_hash == current_hash
    
    def get_file_history(self, file_id):
        """Get the history of a file from the blockchain"""
        if file_id not in self.file_histories:
            return []
            
        return self.file_histories[file_id]
    
    def load_chain(self):
        """Load blockchain from file"""
        try:
            with open(self.blockchain_file, 'r') as f:
                data = json.load(f)
                
                self.chain = []
                self.file_histories = data.get("file_histories", {})
                
                for block_data in data.get("chain", []):
                    block = Block(
                        block_data["index"],
                        block_data["timestamp"],
                        block_data["file_id"],
                        block_data["file_hash"],
                        block_data["previous_hash"]
                    )
                    block.nonce = block_data["nonce"]
                    block.hash = block_data["hash"]
                    self.chain.append(block)
                    
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, start with empty chain
            self.chain = []
            self.file_histories = {}
    
    def save_chain(self):
        """Save blockchain to file"""
        data = {
            "chain": [block.to_dict() for block in self.chain],
            "file_histories": self.file_histories
        }
        
        with open(self.blockchain_file, 'w') as f:
            json.dump(data, f, indent=4)

# Legacy functions for backward compatibility
def add_file_to_blockchain(file_id, file_hash):
    """Add a file to the blockchain (legacy function)"""
    blockchain = Blockchain()
    return blockchain.create_block(file_id, file_hash)

def verify_file_in_blockchain(file_id, file_hash):
    """Verify a file in the blockchain (legacy function)"""
    blockchain = Blockchain()
    return blockchain.verify_file_integrity(file_id, file_hash)

def create_genesis_block():
    """Create the first block in the chain (genesis block)"""
    return Block(0, datetime.now(), "genesis", "genesis_hash", "0")

def get_latest_block():
    """Get the latest block"""
    blockchain = Blockchain()
    return blockchain.get_latest_block()

def verify_blockchain():
    """Verify the integrity of the entire blockchain"""
    blockchain = Blockchain()
    return blockchain.verify_chain_integrity()

# Static methods for the main application to use
@staticmethod
def create_block(file_id, file_hash):
    """Create a new block in the blockchain"""
    blockchain = Blockchain()
    return blockchain.create_block(file_id, file_hash)

@staticmethod
def verify_file_integrity(file_id, file_hash):
    """Verify the integrity of a file"""
    blockchain = Blockchain()
    return blockchain.verify_file_integrity(file_id, file_hash)

@staticmethod
def verify_chain_integrity():
    """Verify the integrity of the entire blockchain"""
    blockchain = Blockchain()
    return blockchain.verify_chain_integrity()

@staticmethod
def get_file_history(file_id):
    """Get the history of a file"""
    blockchain = Blockchain()
    return blockchain.get_file_history(file_id) 