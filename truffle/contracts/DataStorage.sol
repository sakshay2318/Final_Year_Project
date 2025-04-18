// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DataStorage {
    struct Data {
        uint256 id;
        string ipfsHash;
        uint256 timestamp;
        uint256 securityLevel;  // Add security level to the struct
    }

    Data[] public dataStorage;

    event DataAdded(uint256 id, string ipfsHash, uint256 timestamp, uint256 securityLevel);

    function addData(string memory ipfsHash, uint256 securityLevel) public {
        uint256 id = dataStorage.length;
        uint256 timestamp = block.timestamp;

        dataStorage.push(Data(id, ipfsHash, timestamp, securityLevel));
        emit DataAdded(id, ipfsHash, timestamp, securityLevel);
    }

    function getData(uint256 id) public view returns (uint256, string memory, uint256, uint256) {
        require(id < dataStorage.length, "Data ID does not exist");
        Data memory data = dataStorage[id];
        return (data.id, data.ipfsHash, data.timestamp, data.securityLevel);  // Return the security level
    }
}
