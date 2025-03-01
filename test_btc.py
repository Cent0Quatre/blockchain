from bitcoin import Blockchain, Wallet

def chain_print(blockchain: Blockchain) -> None:
    """Affiche la bitcoin_bc et le contenu des blocs."""
    print("\nBlocs dans la bitcoin_bc:")
    for block in blockchain.chain:
        print(f"Bloc #{block.index} | Hash: {block.hash[:10]}... | Transactions: {len(block.transactions)}")
        for tx in block.transactions:
            if tx.sender == "Coinbase":
                print(f"  - Récompense de minage pour {tx.recipient[:10]}...: {tx.amount} BTC")
            else:
                print(f"  - {tx.sender[:10]}... envoie {tx.amount} BTC à {tx.recipient[:10]}...")

# Exemple d'utilisation
def run_simulation():
    bitcoin_bc = Blockchain(difficulty=4)
    
    # Créer quelques portefeuilles
    Yann = Wallet()
    Moustafa = Wallet()
    Bouldingue = Wallet()
    
    print(f"Yann: {Yann.public_key[:10]}...")
    print(f"Moustafa: {Moustafa.public_key[:10]}...")
    
    # Des transactions
    tx1 = Yann.create_transaction(Moustafa.public_key, 10)
    bitcoin_bc.add_transaction_to_mempool(tx1)

    tx2 = Moustafa.create_transaction(Yann.public_key, 1.5)
    bitcoin_bc.add_transaction_to_mempool(tx2)

    print("\nYann mine un bloc...")
    bitcoin_bc.mine_pending_transactions(Yann.public_key)

    tx3 = Moustafa.create_transaction(Bouldingue.public_key, 10000.0)
    bitcoin_bc.add_transaction_to_mempool(tx3)

    for _ in range(10):
        print("\nBouldingue mine un bloc...")
        bitcoin_bc.mine_pending_transactions(Bouldingue.public_key)
    
    # Vérifier la validité de la bitcoin_bc
    print(f"\nLa bitcoin_bc est-elle valide? {bitcoin_bc.is_chain_valid()}")

    chain_print(bitcoin_bc)

# Simulation
if __name__ == "__main__":
    run_simulation()
