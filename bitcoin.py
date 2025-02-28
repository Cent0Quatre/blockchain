import hashlib
import time
import json
from typing import List, Dict, Any
import binascii
import ecdsa

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = time.time()
        self.signature = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': self.signature
        }
    
    def calculate_hash(self) -> str:
        """Calcule le hachage de la transaction."""
        transaction_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(transaction_string.encode()).hexdigest()
    
    def sign_transaction(self, private_key):
        """Signe la transaction avec la clé privée."""
        transaction_hash = self.calculate_hash()
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
        signature = sk.sign(transaction_hash.encode())
        self.signature = binascii.hexlify(signature).decode('ascii')
        
    def verify_signature(self, public_key) -> bool:
        """Vérifie la signature de la transaction."""
        if self.signature is None:
            return False
        
        transaction_hash = self.calculate_hash()
        try:
            vk = ecdsa.VerifyingKey.from_string(binascii.unhexlify(public_key), curve=ecdsa.SECP256k1)
            return vk.verify(binascii.unhexlify(self.signature), transaction_hash.encode())
        except:
            return False


class Block:
    def __init__(self, index: int, previous_hash: str, timestamp=None, nonce: int = 0):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions: List[Transaction] = []
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.merkle_root = ""
        self.hash = self.calculate_hash()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root,
            'hash': self.hash
        }
        
    def calculate_merkle_root(self) -> str:
        """Calcule la racine de Merkle des transactions."""
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        transaction_hashes = [tx.calculate_hash() for tx in self.transactions]
        
        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 != 0:
                transaction_hashes.append(transaction_hashes[-1])
                
            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                combined = transaction_hashes[i] + transaction_hashes[i+1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
                
            transaction_hashes = new_hashes
            
        return transaction_hashes[0]
    
    def calculate_hash(self) -> str:
        """Calcule le hachage du bloc."""
        self.merkle_root = self.calculate_merkle_root()
        block_string = f"{self.index}{self.timestamp}{self.merkle_root}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def add_transaction(self, transaction: Transaction, mempool: List[Transaction]) -> bool:
        """Ajoute une transaction au bloc si elle est valide."""
        # Vérifications de base
        if not transaction.verify_signature(transaction.sender):
            return False
        
        # Dans un système réel, vérifier les UTXO, les doubles dépenses, etc.
        
        self.transactions.append(transaction)
        mempool.remove(transaction)
        self.hash = self.calculate_hash()
        return True
        
    def mine_block(self, difficulty: int) -> None:
        """Mine le bloc avec une difficulté donnée (preuve de travail)."""
        target = "0" * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
        print(f"Bloc miné! Nonce: {self.nonce}, Hash: {self.hash}")


class Wallet:
    def __init__(self):
        # Génère une nouvelle paire de clés ECDSA
        self.private_key = self._generate_private_key()
        self.public_key = self._derive_public_key(self.private_key)
        
    def _generate_private_key(self) -> str:
        """Génère une clé privée aléatoire."""
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        return binascii.hexlify(private_key.to_string()).decode('ascii')
    
    def _derive_public_key(self, private_key: str) -> str:
        """Dérive la clé publique à partir de la clé privée."""
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        return binascii.hexlify(vk.to_string()).decode('ascii')
    
    def create_transaction(self, recipient: str, amount: float) -> Transaction:
        """Crée et signe une nouvelle transaction."""
        transaction = Transaction(self.public_key, recipient, amount)
        transaction.sign_transaction(self.private_key)
        return transaction


class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        self.difficulty = difficulty
        self.mining_reward = 50.0
        self.halving_interval = 210000  # Blocs entre chaque division par deux de la récompense
        
        # Créer le bloc de genèse
        self._create_genesis_block()
        
    def _create_genesis_block(self) -> None:
        """Crée le bloc de genèse."""
        genesis_block = Block(0, "0" * 64, time.time(), 0)
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        
    def get_latest_block(self) -> Block:
        """Retourne le dernier bloc de la chaîne."""
        return self.chain[-1]
    
    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Ajoute une transaction au mempool."""
        # Dans une implémentation réelle, vérifier UTXO, balance, etc.
        if transaction.verify_signature(transaction.sender):
            self.mempool.append(transaction)
            return True
        return False
    
    def mine_pending_transactions(self, miner_reward_address: str) -> Block:
        """Mine un nouveau bloc avec les transactions en attente."""
        # Créer une récompense pour le mineur
        reward = self._calculate_mining_reward()
        reward_tx = Transaction("Coinbase", miner_reward_address, reward)
        
        # Créer un nouveau bloc
        block = Block(len(self.chain), self.get_latest_block().hash)
        
        # Ajouter la transaction de récompense
        block.transactions.append(reward_tx)
        
        # Ajouter des transactions de la mempool (limite de taille de bloc)
        max_transactions = 10  # Simplifié, Bitcoin utilise une limite de taille en octets
        for _ in range(min(max_transactions, len(self.mempool))):
            if self.mempool:
                tx = self.mempool.pop(0)
                block.add_transaction(tx, self.mempool)
        
        # Miner le bloc
        block.mine_block(self.difficulty)
        
        # Ajouter le bloc à la chaîne
        self.chain.append(block)
        
        return block
    
    def _calculate_mining_reward(self) -> float:
        """Calcule la récompense de minage basée sur le halving."""
        halvings = len(self.chain) // self.halving_interval
        return self.mining_reward / (2 ** halvings)
    
    def is_chain_valid(self) -> bool:
        """Vérifie si la blockchain est valide."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Vérifier si le hachage du bloc est correct
            if current_block.hash != current_block.calculate_hash():
                print("Hachage de bloc invalide")
                return False
                
            # Vérifier si le bloc pointe vers le précédent
            if current_block.previous_hash != previous_block.hash:
                print("Chaînage des blocs invalide")
                return False
                
            # Vérifier la preuve de travail
            if current_block.hash[:self.difficulty] != "0" * self.difficulty:
                print("Preuve de travail invalide")
                return False
                
            # Vérifier chaque transaction
            for tx in current_block.transactions:
                if tx.sender != "Coinbase" and not tx.verify_signature(tx.sender):
                    print("Signature de transaction invalide")
                    return False
                    
        return True
