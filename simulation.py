import time
import random
import threading
from bitcoin import Blockchain, Wallet, Transaction
from typing import List, Dict, Tuple
import signal
import sys
from pynput import keyboard

class SimulationUser:
    """Représente un utilisateur de la simulation avec son portefeuille et son comportement."""
    def __init__(self, name: str, blockchain: Blockchain):
        self.name = name
        self.wallet = Wallet(blockchain)
        self.blockchain = blockchain
        self.transactions_sent = 0
        self.blocks_mined = 0
        self.total_mined = 0.0
        self.last_action_time = time.time()
        
    def __str__(self) -> str:
        return f"{self.name} (Adresse: {self.wallet.public_key[:8]}...)"
        
    def get_balance(self) -> float:
        return self.wallet.get_balance()
    
    def send_transaction(self, recipient_wallet: Wallet, amount: float) -> bool:
        """Tente d'envoyer une transaction à un autre utilisateur."""
        try:
            if self.get_balance() < amount:
                print(f"⚠️ {self.name} a un solde insuffisant pour envoyer {amount:.2f} BTC")
                return False
                
            tx = self.wallet.create_transaction(recipient_wallet.public_key, amount)
            success = self.blockchain.add_transaction_to_mempool(tx)
            
            if success:
                self.transactions_sent += 1
                self.last_action_time = time.time()
                print(f"💸 {self.name} a envoyé {amount:.2f} BTC à {recipient_wallet.public_key[:8]}...")
            else:
                print(f"❌ Échec de la transaction de {self.name}")
                
            return success
        except ValueError as e:
            print(f"❌ Erreur lors de la transaction de {self.name}: {e}")
            return False
            
    def mine_block(self) -> bool:
        """Tente de miner un bloc."""
        try:
            # Vérifier s'il y a des transactions en attente (sauf pour les premiers blocs)
            if len(self.blockchain.mempool) == 0 and len(self.blockchain.chain) > 3:
                print(f"⏳ {self.name} attend des transactions pour miner un bloc...")
                return False
                
            print(f"⛏️ {self.name} commence à miner un bloc...")
            start_time = time.time()
            block = self.blockchain.mine_pending_transactions(self.wallet.public_key)
            mining_time = time.time() - start_time
            
            # Obtenir la récompense du bloc
            reward = 0
            for tx in block.transactions:
                if not tx.inputs and tx.outputs[0].recipient == self.wallet.public_key:
                    reward = tx.outputs[0].amount
                    
            self.blocks_mined += 1
            self.total_mined += reward
            self.last_action_time = time.time()
            
            print(f"✅ {self.name} a miné le bloc #{block.index} en {mining_time:.2f}s et reçu {reward:.2f} BTC")
            return True
        except Exception as e:
            print(f"❌ Erreur pendant le minage de {self.name}: {e}")
            return False


class BitcoinSimulation:
    """Simule un écosystème Bitcoin en temps réel."""
    def __init__(self, difficulty: int = 3, user_count: int = 5):
        self.blockchain = Blockchain(difficulty=difficulty)  # Difficulté réduite pour la simulation
        self.users: List[SimulationUser] = []
        self.mempool_stats = []
        self.block_times = []
        self.running = True
        self.paused = False
        self.pause_condition = threading.Condition()  # Pour synchroniser les threads pendant la pause
        self.stats_lock = threading.Lock()
        self.last_block_time = time.time()
        
        # Créer les utilisateurs initiaux
        names = ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
        for i in range(min(user_count, len(names))):
            self.add_user(names[i])
            
    def add_user(self, name: str) -> SimulationUser:
        """Ajoute un nouvel utilisateur à la simulation."""
        user = SimulationUser(name, self.blockchain)
        self.users.append(user)
        print(f"👤 Nouvel utilisateur créé: {user}")
        return user
        
    def random_user(self, exclude=None) -> SimulationUser:
        """Retourne un utilisateur aléatoire, différent de exclude."""
        if exclude:
            choices = [u for u in self.users if u != exclude]
        else:
            choices = self.users
            
        if not choices:
            return None
            
        return random.choice(choices)
    
    def check_pause(self):
        """Vérifie si la simulation est en pause et attend si c'est le cas."""
        with self.pause_condition:
            while self.paused and self.running:
                self.pause_condition.wait()
        
    def toggle_pause(self):
        """Bascule l'état de pause de la simulation."""
        with self.pause_condition:
            self.paused = not self.paused
            if not self.paused:
                print("▶️ Simulation reprise")
                self.pause_condition.notify_all()
            else:
                print("⏸️ Simulation en pause (appuyez sur la barre d'espace pour reprendre)")
        
    def print_network_status(self) -> None:
        """Affiche l'état actuel du réseau Bitcoin."""
        print("\n" + "="*80)
        print(f"ÉTAT DU RÉSEAU BITCOIN (Blocs: {len(self.blockchain.chain)}, Mempool: {len(self.blockchain.mempool)})")
        print("="*80)
        
        # Info des blocs récents
        print("\n--- BLOCS RÉCENTS ---")
        for block in self.blockchain.chain[-3:]:
            print(f"Bloc #{block.index} | Hash: {block.hash[:10]}... | Transactions: {len(block.transactions)}")
            
        # Info du mempool
        print(f"\n--- MEMPOOL ({len(self.blockchain.mempool)} transactions) ---")
        for i, tx in enumerate(self.blockchain.mempool[:5]):
            input_sum = sum(self.blockchain.utxo_set.get(f"{inp.tx_hash}:{inp.output_index}", 0).amount 
                           for inp in tx.inputs) if tx.inputs else 0
            output_sum = sum(out.amount for out in tx.outputs)
            print(f"TX {i+1}: {tx.tx_hash[:8]}... | Entrées: {len(tx.inputs)} | Sorties: {len(tx.outputs)} | Total: {output_sum:.2f} BTC")
            
        if len(self.blockchain.mempool) > 5:
            print(f"... et {len(self.blockchain.mempool) - 5} autres transactions")
            
        # Info des utilisateurs
        print("\n--- UTILISATEURS ---")
        for user in sorted(self.users, key=lambda u: u.get_balance(), reverse=True):
            print(f"{user.name}: {user.get_balance():.2f} BTC | Miné: {user.blocks_mined} blocs ({user.total_mined:.2f} BTC) | Envoyé: {user.transactions_sent} TX")
            
        print("\n" + "="*80)
        
    def mining_thread(self) -> None:
        """Thread dédié au minage par les utilisateurs."""
        while self.running:
            self.check_pause()  # Vérifier si on est en pause
            
            # Sélectionner un mineur au hasard
            miner = self.random_user()
            if miner:
                miner.mine_block()
                with self.stats_lock:
                    current_time = time.time()
                    self.block_times.append(current_time - self.last_block_time)
                    self.last_block_time = current_time
                    self.mempool_stats.append(len(self.blockchain.mempool))
            
            # Pause variable entre les tentatives de minage
            sleep_time = random.uniform(3, 8)
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_time and self.running:
                self.check_pause()
                time.sleep(0.1)
            
    def transaction_thread(self) -> None:
        """Thread dédié aux transactions entre utilisateurs."""
        while self.running:
            self.check_pause()  # Vérifier si on est en pause
            
            # S'assurer qu'il y a au moins deux utilisateurs
            if len(self.users) < 2:
                time.sleep(2)
                continue
                
            # Créer une nouvelle transaction aléatoire
            sender = self.random_user()
            receiver = self.random_user(exclude=sender)
            
            # Déterminer un montant aléatoire basé sur le solde de l'expéditeur
            balance = sender.get_balance()
            if balance > 0:
                # Montant aléatoire entre 1% et 20% du solde
                amount = random.uniform(0.01 * balance, 0.2 * balance)
                sender.send_transaction(receiver.wallet, amount)
            
            # Pause variable entre les transactions
            sleep_time = random.uniform(1, 5)
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_time and self.running:
                self.check_pause()
                time.sleep(0.1)
            
    def user_management_thread(self) -> None:
        """Thread dédié à la gestion des utilisateurs (ajout/suppression)."""
        user_names = ["Michael", "Nina", "Oscar", "Patricia", "Quinn", "Robert", "Sarah", 
                      "Thomas", "Uma", "Vincent", "Wendy", "Xander", "Yvonne", "Zach"]
        name_index = 0
        
        while self.running:
            self.check_pause()  # Vérifier si on est en pause
            
            # Occasionnellement ajouter un nouvel utilisateur
            if random.random() < 0.2 and len(self.users) < 15:  # 20% de chance, max 15 utilisateurs
                if name_index < len(user_names):
                    self.add_user(user_names[name_index])
                    name_index += 1
                else:
                    # Si on manque de noms prédéfinis
                    self.add_user(f"User{random.randint(1000, 9999)}")
            
            # Pause entre les actions de gestion des utilisateurs
            sleep_time = random.uniform(15, 30)
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_time and self.running:
                self.check_pause()
                time.sleep(0.5)
            
    def report_thread(self) -> None:
        """Thread dédié à la génération de rapports périodiques."""
        while self.running:
            self.check_pause()  # Vérifier si on est en pause
            
            if not self.paused:
                self.print_network_status()
                
                # Vérifier la validité de la chaîne
                is_valid = self.blockchain.is_chain_valid()
                if not is_valid:
                    print("⚠️ ALERTE: LA BLOCKCHAIN EST INVALIDE!")
            
            # Rapport toutes les 10 secondes
            sleep_time = 10
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_time and self.running:
                self.check_pause()
                time.sleep(0.5)
            
    def keyboard_listener(self):
        """Fonction pour gérer les entrées clavier."""
        def on_press(key):
            try:
                if key == keyboard.Key.space:
                    self.toggle_pause()
                elif key == keyboard.Key.esc:
                    print("\n👋 Arrêt de la simulation...")
                    self.running = False
                    return False  # Arrête le listener
            except Exception as e:
                print(f"Erreur lors de la gestion des touches: {e}")
                
        # Démarrer le listener
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
            
    def start(self) -> None:
        """Démarre la simulation avec plusieurs threads."""
        print("🚀 Démarrage de la simulation Bitcoin...")
        print("📋 Instructions:")
        print("   - Appuyez sur la barre d'espace pour mettre en pause/reprendre la simulation")
        print("   - Appuyez sur Échap pour terminer la simulation")
        
        # Créer les différents threads
        threads = [
            threading.Thread(target=self.mining_thread),
            threading.Thread(target=self.transaction_thread),
            threading.Thread(target=self.user_management_thread),
            threading.Thread(target=self.report_thread),
            threading.Thread(target=self.keyboard_listener)
        ]
        
        # Configurer comme daemon pour qu'ils s'arrêtent avec le thread principal
        for thread in threads:
            thread.daemon = True
            thread.start()
            
        # Capturer Ctrl+C pour arrêter proprement
        def signal_handler(sig, frame):
            print("\n👋 Arrêt de la simulation...")
            self.running = False
            time.sleep(1)  # Attendre que les threads se terminent
            self.print_final_report()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Garder le thread principal en vie
            while self.running:
                time.sleep(0.1)
            
            # Afficher le rapport final à la sortie
            self.print_final_report()
        except KeyboardInterrupt:
            signal_handler(None, None)
            
    def print_final_report(self) -> None:
        """Affiche un rapport final de la simulation."""
        print("\n" + "="*80)
        print("RAPPORT FINAL DE LA SIMULATION")
        print("="*80)
        
        # Statistiques générales
        blocks_count = len(self.blockchain.chain)
        tx_count = sum(len(block.transactions) for block in self.blockchain.chain)
        avg_block_time = sum(self.block_times) / len(self.block_times) if self.block_times else 0
        
        print(f"\nDurée de la simulation: {time.time() - self.blockchain.chain[0].timestamp:.0f} secondes")
        print(f"Nombre de blocs minés: {blocks_count}")
        print(f"Nombre total de transactions: {tx_count}")
        print(f"Temps moyen entre les blocs: {avg_block_time:.2f} secondes")
        
        # Top des utilisateurs
        print("\nClassement des utilisateurs:")
        for i, user in enumerate(sorted(self.users, key=lambda u: u.get_balance(), reverse=True)):
            print(f"{i+1}. {user.name}: {user.get_balance():.2f} BTC | {user.blocks_mined} blocs minés | {user.transactions_sent} transactions")
            
        print("\n" + "="*80)


if __name__ == "__main__":
    # Vérifier si pynput est installé
    try:
        import pynput
    except ImportError:
        print("La bibliothèque 'pynput' est requise pour cette simulation.")
        print("Veuillez l'installer avec la commande: pip install pynput")
        sys.exit(1)
        
    # Démarrer la simulation avec une difficulté réduite pour une expérience plus rapide
    simulation = BitcoinSimulation(difficulty=2, user_count=5)
    simulation.start()                        
