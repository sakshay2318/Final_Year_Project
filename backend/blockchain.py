from web3 import Web3
import json
from config import GANACHE_URL, CONTRACT_ADDRESS, CONTRACT_ABI

# Connect to Ganache
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(CONTRACT_ABI))
account = web3.eth.accounts[0]  # Use the first Ganache account

def store_to_blockchain(ipfs_hash, security_level):
    """Store IPFS hash and security level in the blockchain."""
    try:
        tx = contract.functions.addData(ipfs_hash, security_level).transact({
            'from': account,
            'gas': 500000  # You can adjust the gas limit if needed
        })
        receipt = web3.eth.wait_for_transaction_receipt(tx)
        if receipt['status'] == 1:
            print("Transaction successful")
        else:
            print("Transaction failed")
        return receipt
    except Exception as e:
        print(f"Error during blockchain transaction: {e}")
        raise e

def get_data_from_blockchain(record_id):
    """Retrieve data from the blockchain by ID."""
    try:
        # Fetch the record from blockchain using the record ID
        record = contract.functions.getData(record_id).call()
        ipfs_hash = record[0]
        security_level = int(record[1])  # Make sure it's an integer
        return ipfs_hash, security_level
    except Exception as e:
        print(f"Error fetching data from blockchain: {e}")
        raise e
