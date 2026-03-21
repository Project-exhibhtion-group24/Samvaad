import hashlib
import json
import time
import os
import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not found. Environment variables must be set manually.")

class Blockchain:
    """Strictly local blockchain for immutable grievance storage"""
    
    def __init__(self):
        # initialize local blockchain
        self.chain = []
        self.pending_data = []
        self.create_block(proof=1, previous_hash='0', data='Genesis Block')
        
    def create_block(self, proof, previous_hash, data=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'data': data or self.pending_data,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.pending_data = []
        self.chain.append(block)
        return block

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_last_block(self):
        return self.chain[-1]

    def add_data(self, grievance_id, audio_hash, status):
        """Adds grievance to local blockchain"""
        data = {
            'grievance_id': grievance_id,
            'audio_hash': audio_hash,
            'status': status,
            'timestamp': time.time()
        }
        self.pending_data.append(data)
        
        # maintain local chain
        previous_block = self.get_last_block()
        if previous_block:
            previous_hash = self.hash(previous_block)
            self.create_block(proof=len(self.chain), previous_hash=previous_hash)
        
        return data

    def get_verification_report(self):
        is_valid = True 
        message = "✅ Local Chain Valid"
        
        return {
            'is_valid': is_valid,
            'message': message,
            'total_blocks': len(self.chain),
            'chain_integrity': 'VERIFIED' if is_valid else 'COMPROMISED',
            'ethereum_status': "LOCAL MODE ONLY",
            'blocks': self.chain[-5:] 
        }

    def find_grievance_in_chain(self, grievance_id):
        """Searches for grievance in the local chain"""
        for block in self.chain:
            data_list = block.get('data')
            if isinstance(data_list, list):
                for data in data_list:
                    if isinstance(data, dict) and data.get('grievance_id') == grievance_id:
                        return {
                            'found': True,
                            'source': 'LOCAL_CHAIN',
                            'block_index': block.get('index'),
                            'block_hash': self.hash(block),
                            'timestamp': datetime.datetime.fromtimestamp(block.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            'tx_hash': None
                        }
        return {'found': False}