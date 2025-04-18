from cryptography.fernet import Fernet

IPFS_API_URL = "http://127.0.0.1:5001/api/v0"
GANACHE_URL = "http://127.0.0.1:7545"
IPFS_RETRIEVE_URL = 'https://ipfs.io/ipfs'
CONTRACT_ADDRESS = "0x3ef1f263f23651906a6BC69B1924b030ded1eD4a"
SECURITY_KEYS = [
    Fernet.generate_key().decode('utf-8'),  # Level 1
    Fernet.generate_key().decode('utf-8'),  # Level 2
    Fernet.generate_key().decode('utf-8'),  # Level 3
    Fernet.generate_key().decode('utf-8'),  # Level 4
    Fernet.generate_key().decode('utf-8'),  # Level 5
    Fernet.generate_key().decode('utf-8'),  # Level 6
]
CONTRACT_ABI = """
[
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "ipfsHash",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "securityLevel",
                "type": "uint256"
            }
        ],
        "name": "addData",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "id",
                "type": "uint256"
            }
        ],
        "name": "getData",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
"""
