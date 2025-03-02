from bitcoin import Blockchain, Wallet

def print_wallet_info(name: str, wallet: Wallet) -> None:
    """Affiche les informations d'un portefeuille."""
    balance = wallet.get_balance()
    print(f"{name} - Adresse: {wallet.public_key[:10]}... | Solde: {balance:.2f} BTC")
    
    utxos = wallet.get_utxos()
    if utxos:
        print(f"  UTXOs de {name}:")
        for utxo in utxos:
            print(f"  - {utxo.amount:.2f} BTC (TX: {utxo.tx_hash[:8]}...:{utxo.output_index})")

def chain_print(blockchain: Blockchain) -> None:
    """Affiche la blockchain et le contenu des blocs."""
    print("\nBlocs dans la blockchain:")
    for block in blockchain.chain:
        print(f"Bloc #{block.index} | Hash: {block.hash[:10]}... | Transactions: {len(block.transactions)}")
        for tx in block.transactions:
            if not tx.inputs:
                print(f"  - Récompense de minage: {tx.outputs[0].amount} BTC pour {tx.outputs[0].recipient[:10]}...")
            else:
                sender = "???"
                total_input = 0
                for tx_input in tx.inputs:
                    input_id = f"{tx_input.tx_hash}:{tx_input.output_index}"
                    # Note: Dans un cas réel, nous devrions rechercher l'expéditeur
                total_output = sum(output.amount for output in tx.outputs)
                print(f"  - Transaction: {tx.tx_hash[:10]}... | Entrées: {len(tx.inputs)} | Sorties: {len(tx.outputs)} | Total: {total_output:.2f} BTC")

def run_simulation():
    print("Création d'une nouvelle blockchain...")
    bitcoin = Blockchain(difficulty=4)  # Difficulté réduite pour une simulation plus rapide
    
    print("\nCréation des portefeuilles...")
    # Associer les portefeuilles à la blockchain pour la gestion des soldes
    alice = Wallet(bitcoin)
    bob = Wallet(bitcoin)
    charlie = Wallet(bitcoin)
    
    print("\nÉtat initial des portefeuilles:")
    print_wallet_info("Alice", alice)
    print_wallet_info("Bob", bob)
    print_wallet_info("Charlie", charlie)
    
    print("\nAlice mine un bloc pour obtenir des bitcoins...")
    bitcoin.mine_pending_transactions(alice.public_key)
    
    print("\nBob mine un bloc pour obtenir des bitcoins...")
    bitcoin.mine_pending_transactions(bob.public_key)
    
    print("\nAlice envoie 10 BTC à Bob...")
    try:
        tx = alice.create_transaction(bob.public_key, 60)
        if bitcoin.add_transaction_to_mempool(tx):
            print("Transaction ajoutée au mempool avec succès.")
        else:
            print("Échec de l'ajout de la transaction au mempool.")
    except ValueError as e:
        print(f"Erreur: {e}")
    
    print("\nCharlie mine un bloc (incluant la transaction d'Alice à Bob)...")
    bitcoin.mine_pending_transactions(charlie.public_key)
    
    print("\nÉtat final des portefeuilles:")
    print_wallet_info("Alice", alice)
    print_wallet_info("Bob", bob)
    print_wallet_info("Charlie", charlie)
    
    print("\nVérification de la validité de la chaîne...")
    is_valid = bitcoin.is_chain_valid()
    print(f"La blockchain est {'valide' if is_valid else 'invalide'}")
    
    chain_print(bitcoin)

if __name__ == "__main__":
    run_simulation()
