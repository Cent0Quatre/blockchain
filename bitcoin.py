import hashlib, time, json, binascii, ecdsa
from typing import List, Dict, Any, Set, Tuple

class UTXO:
    """Représente une sortie de transaction non dépensée (Unspent Transaction Output)."""
    def __init__(self, tx_hash: str, output_index: int, amount: float, recipient: str):
        self.tx_hash = tx_hash  # Hash de la transaction d'origine
        self.output_index = output_index  # Index de sortie dans la transaction
        self.amount = amount  # Montant
        self.recipient = recipient  # Clé publique du destinataire
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tx_hash': self.tx_hash,
            'output_index': self.output_index,
            'amount': self.amount,
            'recipient': self.recipient
        }
    
    def get_id(self) -> str:
        """Retourne un identifiant unique pour cet UTXO."""
        return f"{self.tx_hash}:{self.output_index}"


class TransactionInput:
    """Représente une entrée de transaction qui fait référence à un UTXO."""
    def __init__(self, tx_hash: str, output_index: int):
        self.tx_hash = tx_hash  # Hash de la transaction contenant l'UTXO
        self.output_index = output_index  # Index de l'UTXO dans la transaction
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tx_hash': self.tx_hash,
            'output_index': self.output_index
        }
    
    def get_id(self) -> str:
        """Retourne un identifiant unique pour cette entrée."""
        return f"{self.tx_hash}:{self.output_index}"


class TransactionOutput:
    """Représente une sortie de transaction qui crée un nouveau UTXO."""
    def __init__(self, amount: float, recipient: str):
        self.amount = amount  # Montant
        self.recipient = recipient  # Clé publique du destinataire
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'amount': self.amount,
            'recipient': self.recipient
        }


class Transaction:
    def __init__(self):
        self.inputs: List[TransactionInput] = []
        self.outputs: List[TransactionOutput] = []
        self.timestamp = time.time()
        self.signature = None
        self.tx_hash = None
        
    def add_input(self, tx_hash: str, output_index: int) -> None:
        """Ajoute une entrée à la transaction."""
        self.inputs.append(TransactionInput(tx_hash, output_index))
        
    def add_output(self, amount: float, recipient: str) -> None:
        """Ajoute une sortie à la transaction."""
        self.outputs.append(TransactionOutput(amount, recipient))
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'inputs': [inp.to_dict() for inp in self.inputs],
            'outputs': [out.to_dict() for out in self.outputs],
            'timestamp': self.timestamp,
            'signature': self.signature,
            'tx_hash': self.tx_hash
        }
    
    def calculate_hash(self) -> str:
        """Calcule le hachage de la transaction sans inclure la signature."""
        tx_dict = {
            'inputs': [inp.to_dict() for inp in self.inputs],
            'outputs': [out.to_dict() for out in self.outputs],
            'timestamp': self.timestamp
        }
        tx_string = json.dumps(tx_dict, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def sign_transaction(self, private_key: str) -> None:
        """Signe la transaction avec la clé privée."""
        if not self.tx_hash:
            self.tx_hash = self.calculate_hash()
        
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
        signature = sk.sign(self.tx_hash.encode())
        self.signature = binascii.hexlify(signature).decode('ascii')
        
    def verify_signature(self, public_key: str) -> bool:
        """Vérifie la signature de la transaction."""
        if self.signature is None or self.tx_hash is None:
            return False
        
        try:
            vk = ecdsa.VerifyingKey.from_string(binascii.unhexlify(public_key), curve=ecdsa.SECP256k1)
            return vk.verify(binascii.unhexlify(self.signature), self.tx_hash.encode())
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
        
        transaction_hashes = [tx.tx_hash for tx in self.transactions]
        
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
    
    def add_transaction(self, transaction: Transaction, blockchain) -> bool:
        """Ajoute une transaction au bloc si elle est valide."""
        # Ne pas vérifier les transactions coinbase (récompenses de minage)
        if not transaction.inputs:
            self.transactions.append(transaction)
            self.hash = self.calculate_hash()
            return True
            
        # Vérifier si la transaction est valide
        if not blockchain.is_transaction_valid(transaction):
            return False
        
        self.transactions.append(transaction)
        self.hash = self.calculate_hash()
        return True
        
    def mine_block(self, difficulty: int) -> None:
        """Mine le bloc avec une difficulté donnée (preuve de travail)."""
        target = "0" * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
        print(f"Bloc miné! Nonce: {self.nonce}, Hash: {self.hash[:10]}...")


class Wallet:
    def __init__(self, blockchain=None):
        # Génère une nouvelle paire de clés ECDSA
        self.private_key = self._generate_private_key()
        self.public_key = self._derive_public_key(self.private_key)
        self.blockchain = blockchain
        
    def _generate_private_key(self) -> str:
        """Génère une clé privée aléatoire."""
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        return binascii.hexlify(private_key.to_string()).decode('ascii')
    
    def _derive_public_key(self, private_key: str) -> str:
        """Dérive la clé publique à partir de la clé privée."""
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        return binascii.hexlify(vk.to_string()).decode('ascii')
    
    def get_balance(self) -> float:
        """Calcule le solde du portefeuille en consultant les UTXO."""
        if self.blockchain is None:
            return 0
            
        return sum(utxo.amount for utxo in self.blockchain.get_utxos_for_address(self.public_key))
    
    def get_utxos(self) -> List[UTXO]:
        """Obtient tous les UTXO appartenant à ce portefeuille."""
        if self.blockchain is None:
            return []
            
        return self.blockchain.get_utxos_for_address(self.public_key)
        
    def create_transaction(self, recipient_address: str, amount: float) -> Transaction:
        """Crée et signe une transaction pour envoyer des coins."""
        if self.blockchain is None:
            raise ValueError("Wallet not connected to blockchain")
            
        # Vérifier si le portefeuille a suffisamment de fonds
        balance = self.get_balance()
        if balance < amount:
            raise ValueError(f"Solde insuffisant: {balance} BTC, tentative d'envoi de {amount} BTC")
            
        # Créer une nouvelle transaction
        transaction = Transaction()
        
        # Collecter les UTXO pour couvrir le montant
        utxos_to_spend = []
        total_input = 0
        
        for utxo in self.get_utxos():
            utxos_to_spend.append(utxo)
            total_input += utxo.amount
            
            # Ajouter l'entrée correspondante à la transaction
            transaction.add_input(utxo.tx_hash, utxo.output_index)
            
            if total_input >= amount:
                break
                
        # Ajouter la sortie pour le destinataire
        transaction.add_output(amount, recipient_address)
        
        # Créer une sortie pour la monnaie à rendre si nécessaire
        change = total_input - amount
        if change > 0:
            transaction.add_output(change, self.public_key)
            
        # Calculer le hash de la transaction
        transaction.tx_hash = transaction.calculate_hash()
        
        # Signer la transaction
        transaction.sign_transaction(self.private_key)
        
        return transaction


class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        self.difficulty = difficulty
        self.mining_reward = 50.0
        self.halving_interval = 10  # Blocs entre chaque division par deux de la récompense
        self.utxo_set: Dict[str, UTXO] = {}  # Ensemble des UTXO actuels
        self.spent_outputs: Set[str] = set()  # Ensemble des sorties déjà dépensées
        
        # Créer le bloc de genèse
        self._create_genesis_block()
        
    def _create_genesis_block(self) -> None:
        """Crée le bloc de genèse."""
        genesis_block = Block(0, "0" * 64, time.time(), 0)
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        
    def get_latest_block(self) -> Block:
        """Retourne le dernier bloc de la chaîne."""
        return self.chain[-1]
    
    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Ajoute une transaction au mempool si elle est valide."""
        # Check if the transaction is valid
        if not self.is_transaction_valid(transaction):
            return False
            
        # Check for double-spending within the mempool
        # Track which UTXOs are already referenced by transactions in the mempool
        mempool_inputs = set()
        for tx in self.mempool:
            for tx_input in tx.inputs:
                mempool_inputs.add(f"{tx_input.tx_hash}:{tx_input.output_index}")
        
        # Verify the transaction doesn't try to spend UTXOs already referenced in the mempool
        for tx_input in transaction.inputs:
            input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
            if input_id in mempool_inputs:
                return False  # Double-spend attempt detected in mempool
        
        # If we get here, the transaction is valid
        self.mempool.append(transaction)
        return True
    
    def is_transaction_valid(self, transaction: Transaction) -> bool:
        """Vérifie si une transaction est valide."""
        # Vérifier si la transaction a au moins une entrée (sauf pour les transactions coinbase)
        if not transaction.inputs and not transaction.outputs:
            return False
            
        # Les transactions sans entrées sont des transactions coinbase (récompenses de minage)
        if not transaction.inputs:
            return True
            
        # Récupérer la clé publique du premier UTXO référencé
        first_input = transaction.inputs[0]
        input_id = f"{first_input.tx_hash}:{first_input.output_index}"
        
        if input_id not in self.utxo_set:
            return False
            
        sender_public_key = self.utxo_set[input_id].recipient
        
        # Vérifier la signature
        if not transaction.verify_signature(sender_public_key):
            return False
            
        # Vérifier que les entrées ne sont pas déjà dépensées
        for tx_input in transaction.inputs:
            input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
            
            # Vérifier si l'UTXO existe
            if input_id not in self.utxo_set:
                return False
                
            # Vérifier si l'UTXO appartient à l'émetteur
            if self.utxo_set[input_id].recipient != sender_public_key:
                return False
                
            # Vérifier si l'UTXO n'est pas déjà dépensé (double dépense)
            if input_id in self.spent_outputs:
                return False
                
        # Calculer le total des entrées et des sorties
        total_input = sum(self.utxo_set[f"{tx_in.tx_hash}:{tx_in.output_index}"].amount for tx_in in transaction.inputs)
        total_output = sum(output.amount for output in transaction.outputs)
        
        # Vérifier que le total des sorties ne dépasse pas le total des entrées
        if total_output > total_input:
            return False
            
        return True
    
    def process_block_transactions(self, block: Block) -> None:
        """Met à jour l'ensemble des UTXO après l'ajout d'un bloc."""
        for tx in block.transactions:
            # Marquer les entrées comme dépensées et les retirer de l'ensemble UTXO
            for tx_input in tx.inputs:
                input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
                self.spent_outputs.add(input_id)
                if input_id in self.utxo_set:
                    del self.utxo_set[input_id]
            
            # Ajouter les nouvelles sorties à l'ensemble UTXO
            for i, tx_output in enumerate(tx.outputs):
                utxo = UTXO(tx.tx_hash, i, tx_output.amount, tx_output.recipient)
                self.utxo_set[utxo.get_id()] = utxo
    
    def get_utxos_for_address(self, address: str) -> List[UTXO]:
        """Retourne tous les UTXO appartenant à une adresse."""
        return [utxo for utxo in self.utxo_set.values() if utxo.recipient == address]
    
    def create_coinbase_transaction(self, miner_address: str) -> Transaction:
        """Crée une transaction coinbase (récompense de minage)."""
        coinbase_tx = Transaction()
        
        # Pas d'entrées pour une transaction coinbase
        
        # Ajouter la sortie avec la récompense
        reward = self._calculate_mining_reward()
        coinbase_tx.add_output(reward, miner_address)
        
        # Calculer le hash de la transaction
        coinbase_tx.tx_hash = coinbase_tx.calculate_hash()
        
        return coinbase_tx
    
    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Mine un nouveau bloc avec les transactions en attente."""
        # Créer un nouveau bloc
        block = Block(len(self.chain), self.get_latest_block().hash)
        
        # Créer une transaction de récompense pour le mineur
        coinbase_tx = self.create_coinbase_transaction(miner_address)
        block.transactions.append(coinbase_tx)
        
        # Ajouter des transactions du mempool
        max_transactions = 10  # Simplifié, Bitcoin utilise une limite de taille en octets
        
        # Copier pour itérer et modifier
        remaining_transactions = []
        
        # Limiter le nombre de transactions à traiter
        transactions_to_try = self.mempool[:max_transactions]
        
        for tx in transactions_to_try:
            if block.add_transaction(tx, self):
                # Marquer temporairement les entrées comme dépensées pour éviter la double dépense
                # dans le même bloc
                for tx_input in tx.inputs:
                    input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
                    self.spent_outputs.add(input_id)
            else:
                remaining_transactions.append(tx)
        
        # Mettre à jour le mempool
        self.mempool = remaining_transactions + self.mempool[max_transactions:]
        
        # Miner le bloc
        block.mine_block(self.difficulty)
        
        # Mettre à jour l'ensemble UTXO
        self.process_block_transactions(block)
        
        # Ajouter le bloc à la chaîne
        self.chain.append(block)
        
        return block
    
    def _calculate_mining_reward(self) -> float:
        """Calcule la récompense de minage basée sur le halving."""
        halvings = len(self.chain) // self.halving_interval
        return self.mining_reward / (2 ** halvings)
    
    def is_chain_valid(self) -> bool:
        """Vérifie si la blockchain est valide."""
        # Recréer l'état UTXO pour vérification
        temp_utxo_set = {}
        temp_spent_outputs = set()
        
        for i in range(len(self.chain)):
            current_block = self.chain[i]
            
            # Vérifier le hash du bloc
            if current_block.hash != current_block.calculate_hash():
                print(f"Hash invalide pour le bloc {i}")
                return False
                
            # Vérifier le chaînage avec le bloc précédent (sauf pour le bloc de genèse)
            if i > 0 and current_block.previous_hash != self.chain[i-1].hash:
                print(f"Chaînage invalide pour le bloc {i}")
                return False
                
            # Vérifier la preuve de travail
            if current_block.hash[:self.difficulty] != "0" * self.difficulty:
                print(f"Preuve de travail invalide pour le bloc {i}")
                return False
                
            # Vérifier chaque transaction
            for tx in current_block.transactions:
                # Vérifier les transactions normales (non-coinbase)
                if tx.inputs:
                    # Vérifier la signature
                    first_input = tx.inputs[0]
                    input_id = f"{first_input.tx_hash}:{first_input.output_index}"
                    
                    if input_id not in temp_utxo_set:
                        print(f"UTXO référencé introuvable: {input_id}")
                        return False
                        
                    sender_public_key = temp_utxo_set[input_id].recipient
                    
                    if not tx.verify_signature(sender_public_key):
                        print(f"Signature invalide dans le bloc {i}")
                        return False
                        
                    # Vérifier que les entrées ne sont pas déjà dépensées
                    total_input = 0
                    for tx_input in tx.inputs:
                        input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
                        
                        if input_id not in temp_utxo_set:
                            print(f"UTXO référencé introuvable: {input_id}")
                            return False
                            
                        if input_id in temp_spent_outputs:
                            print(f"Double dépense détectée: {input_id}")
                            return False
                            
                        # Vérifier que l'expéditeur possède l'UTXO
                        if temp_utxo_set[input_id].recipient != sender_public_key:
                            print(f"Tentative de dépenser un UTXO d'un autre utilisateur")
                            return False
                            
                        total_input += temp_utxo_set[input_id].amount
                        temp_spent_outputs.add(input_id)
                        
                    # Vérifier le total des entrées et sorties
                    total_output = sum(output.amount for output in tx.outputs)
                    
                    if total_output > total_input:
                        print(f"Sortie supérieure à l'entrée dans la transaction")
                        return False
                
                # Mettre à jour l'état UTXO temporaire
                # Supprimer les entrées dépensées
                for tx_input in tx.inputs:
                    input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
                    if input_id in temp_utxo_set:
                        del temp_utxo_set[input_id]
                
                # Ajouter les nouvelles sorties
                for j, tx_output in enumerate(tx.outputs):
                    utxo = UTXO(tx.tx_hash, j, tx_output.amount, tx_output.recipient)
                    temp_utxo_set[utxo.get_id()] = utxo
                    
        return True
    
    def get_balance(self, address: str) -> float:
        """Calcule le solde d'une adresse."""
        return sum(utxo.amount for utxo in self.get_utxos_for_address(address))
