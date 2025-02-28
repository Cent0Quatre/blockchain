from bitcoin import Blockchain, Wallet

# Exemple d'utilisation
def run_simulation():
    blockchain = Blockchain(difficulty=4)
    
    # Créer quelques portefeuilles
    alice = Wallet()
    bob = Wallet()
    charlie = Wallet()
    
    print(f"Alice: {alice.public_key[:10]}...")
    print(f"Bob: {bob.public_key[:10]}...")
    print(f"Charlie: {charlie.public_key[:10]}...")
    
    # Des transactions
    tx1 = alice.create_transaction(bob.public_key, 1.0)
    blockchain.add_transaction_to_mempool(tx1)

    tx2 = bob.create_transaction(alice.public_key, 0.5)
    blockchain.add_transaction_to_mempool(tx2)

    # Charlie mine un bloc
    print("\nCharlie mine un bloc...")
    blockchain.mine_pending_transactions(charlie.public_key)

    print(len(blockchain.chain[1].transactions))
    
    # Vérifier la validité de la blockchain
    print(f"\nLa blockchain est-elle valide? {blockchain.is_chain_valid()}")
    
    # Afficher les blocs
    print("\nBlocs dans la blockchain:")
    for block in blockchain.chain:
        print(f"Bloc #{block.index} | Hash: {block.hash[:10]}... | Transactions: {len(block.transactions)}")
        for tx in block.transactions:
            if tx.sender == "Coinbase":
                print(f"  - Récompense de minage pour {tx.recipient[:10]}...: {tx.amount} BTC")
            else:
                print(f"  - {tx.sender[:10]}... envoie {tx.amount} BTC à {tx.recipient[:10]}...")

# Simulation
if __name__ == "__main__":
    run_simulation()
