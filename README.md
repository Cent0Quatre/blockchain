# Simulation Bitcoin - Implémentation Éducative d'une Blockchain

## Vue d'ensemble

Ce projet implémente une simulation complète d'un réseau Bitcoin simplifié à des fins éducatives. Il démontre les concepts fondamentaux de la technologie blockchain, incluant la cryptographie asymétrique, la preuve de travail (Proof of Work), la gestion des transactions et le modèle UTXO (Unspent Transaction Output).

### Contexte académique

Cette implémentation permet d'étudier concrètement les mécanismes décrits dans le livre blanc de Satoshi Nakamoto "Bitcoin: A Peer-to-Peer Electronic Cash System" (2008). Elle offre une base pratique pour comprendre les défis de la décentralisation, de la sécurité cryptographique et du consensus distribué.

## Objectifs pédagogiques

### Objectifs primaires
- **Compréhension des structures de données blockchain** : Implémentation complète des blocs, transactions et chaînes
- **Maîtrise des algorithmes cryptographiques** : Utilisation d'ECDSA pour les signatures numériques et SHA-256 pour le hachage
- **Apprentissage du modèle UTXO** : Gestion des entrées et sorties de transactions non dépensées
- **Étude des mécanismes de consensus** : Implémentation de la preuve de travail avec ajustement de difficulté

### Objectifs secondaires
- **Simulation de réseau décentralisé** : Modélisation du comportement de multiples acteurs
- **Analyse de performance** : Mesure des temps de bloc et de la congestion du mempool
- **Sécurité cryptographique** : Prévention des doubles dépenses et validation des signatures

## Architecture du système

### Diagramme conceptuel
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Wallet       │◄──►│   Blockchain    │◄──►│  Simulation     │
│  - Clés ECDSA   │    │  - Chaîne       │    │  - Utilisateurs │
│  - Transactions │    │  - UTXO Set     │    │  - Threading    │
│  - Soldes       │    │  - Mempool      │    │  - Métriques    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Composants principaux

#### 1. Classes fondamentales
- **`UTXO`** : Représente une sortie de transaction non dépensée
- **`Transaction`** : Encapsule les transferts de valeur avec signatures cryptographiques
- **`Block`** : Conteneur de transactions avec preuve de travail
- **`Blockchain`** : Gestionnaire de la chaîne et du consensus
- **`Wallet`** : Interface utilisateur pour les opérations cryptographiques

#### 2. Modules de simulation
- **`SimulationUser`** : Modélise le comportement d'un utilisateur du réseau
- **`BitcoinSimulation`** : Orchestrateur de la simulation multi-thread

## Concepts théoriques implémentés

### 1. Cryptographie asymétrique (ECDSA)
```python
# Génération de clés sur la courbe secp256k1
private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
public_key = private_key.get_verifying_key()

# Signature des transactions
signature = private_key.sign(transaction_hash.encode())
```

**Justification théorique** : L'utilisation d'ECDSA sur secp256k1 garantit l'authenticité et la non-répudiation des transactions tout en maintenant l'anonymat des utilisateurs.

### 2. Modèle UTXO (Unspent Transaction Output)
```python
class UTXO:
    def __init__(self, tx_hash: str, output_index: int, amount: float, recipient: str):
        self.tx_hash = tx_hash
        self.output_index = output_index
        self.amount = amount
        self.recipient = recipient
```

**Avantages du modèle UTXO** :
- Parallélisation des validations de transactions
- Prévention naturelle des doubles dépenses
- Traçabilité complète des fonds
- Simplification de la vérification de l'historique

### 3. Arbre de Merkle
```python
def calculate_merkle_root(self) -> str:
    transaction_hashes = [tx.tx_hash for tx in self.transactions]
    while len(transaction_hashes) > 1:
        # Combinaison par paires et hachage
        # Permet la vérification efficace des transactions
```

**Propriétés cryptographiques** : L'arbre de Merkle permet une vérification O(log n) de l'inclusion d'une transaction sans télécharger l'intégralité du bloc.

### 4. Preuve de travail (Proof of Work)
```python
def mine_block(self, difficulty: int) -> None:
    target = "0" * difficulty
    while self.hash[:difficulty] != target:
        self.nonce += 1
        self.hash = self.calculate_hash()
```

**Mécanisme de consensus** : La preuve de travail garantit que la modification de l'historique nécessite une puissance de calcul supérieure à celle du réseau honnête.

### 5. Mécanisme de halving
```python
def _calculate_mining_reward(self) -> float:
    halvings = len(self.chain) // self.halving_interval
    return self.mining_reward / (2 ** halvings)
```

**Politique monétaire** : Le halving contrôle l'inflation en réduisant périodiquement la récompense de minage, créant une rareté programmée.

## Installation et prérequis

### Dépendances système
```bash
# Python 3.8 ou supérieur requis
python --version

# Installation des dépendances
pip install ecdsa pynput
```

### Dépendances Python
- **`ecdsa`** : Cryptographie à courbes elliptiques pour les signatures
- **`pynput`** : Gestion des événements clavier pour l'interface interactive
- **`hashlib`** : Fonctions de hachage cryptographique (intégré)
- **`threading`** : Parallélisation pour la simulation multi-utilisateurs

## Guide d'utilisation

### 1. Test basique des fonctionnalités
```bash
python test_btc.py
```

**Sortie attendue** :
- Création de portefeuilles avec génération de clés
- Minage initial pour distribution de bitcoins
- Exécution de transactions avec validation
- Vérification de l'intégrité de la blockchain

### 2. Simulation interactive complète
```bash
python simulation.py
```

**Contrôles interactifs** :
- `Espace` : Pause/Reprise de la simulation
- `Échap` : Arrêt propre avec rapport final

### 3. Tests unitaires et validation
```bash
python -c "
from bitcoin import Blockchain, Wallet
bc = Blockchain()
print('Blockchain valide:', bc.is_chain_valid())
"
```

## Analyse technique

### Performance et complexité

#### Complexité algorithmique
- **Validation de transaction** : O(n) où n est le nombre d'entrées
- **Calcul de l'arbre de Merkle** : O(m) où m est le nombre de transactions
- **Preuve de travail** : O(2^d) où d est la difficulté
- **Recherche UTXO** : O(1) grâce au dictionnaire indexé

#### Métriques de performance observées
```
Difficulté 2 : ~1-3 secondes par bloc
Difficulté 4 : ~15-60 secondes par bloc
Mémoire : ~50MB pour 1000 blocs avec 10 transactions chacun
```

### Sécurité cryptographique

#### Propriétés de sécurité garanties
1. **Intégrité** : Modification détectable via les hachages chaînés
2. **Authenticité** : Signatures ECDSA non falsifiables
3. **Non-répudiation** : Traçabilité complète des transactions
4. **Prévention double-dépense** : Vérification UTXO stricte

### Architecture multi-thread

```python
# Threads de simulation
├── mining_thread()      # Minage des blocs
├── transaction_thread() # Génération de transactions
├── user_management()    # Gestion dynamique des utilisateurs
├── report_thread()      # Affichage des métriques
└── keyboard_listener()  # Interface utilisateur
```

**Synchronisation** : Utilisation de `threading.Condition` pour la gestion des pauses et `threading.Lock` pour la protection des données partagées.

## Limitations et simplifications

### Simplifications par rapport à Bitcoin

1. **Réseau** : Simulation single-node sans protocole P2P
2. **Sérialisation** : JSON au lieu du format binaire Bitcoin
3. **Scripts** : Absence de Bitcoin Script pour les conditions de déverrouillage
4. **Taille des blocs** : Limite arbitraire sur le nombre de transactions
5. **Ajustement de difficulté** : Difficulté fixe au lieu d'ajustement automatique

### Limitations techniques

1. **Persistance** : Pas de sauvegarde sur disque (données en mémoire)
2. **Validation** : Simplifiée par rapport aux règles complètes de Bitcoin
3. **Types de transactions** : Seules les transactions P2PK sont supportées
4. **Frais de transaction** : Non implémentés

## Validation et tests

### Tests unitaires suggérés
```python
def test_transaction_validation():
    # Test de validation des signatures
    # Test de prévention double-dépense
    # Test de conservation de la valeur

def test_blockchain_integrity():
    # Test de chaînage des blocs
    # Test de calcul Merkle
    # Test de preuve de travail
```

### Scénarios de test
1. **Test de charge** : 1000 utilisateurs, 10000 transactions
2. **Test de sécurité** : Tentatives de double-dépense
3. **Test de performance** : Mesure des temps de validation
4. **Test de consensus** : Résolution de forks simulés
