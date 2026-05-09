// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/Ownable.sol";

contract ENSRegistryContract is AccessControl, Ownable {
    mapping(address => Domain) public domains;

    struct Domain {
        string name;
        address owner;
        bool registered;
    }

    event DomainRegistered(string domainId, string name, address owner);
    event DomainOwnershipTransferred(string domainId, address from, address to);

    // Constructor
    constructor() {
        // Initialize the contract owner
        Ownable(msg.sender);
    }

    // Register a new ENS domain
    function registerDomain(string memory _name) public {
        require(bytes(_name).length > 0, "Domain name cannot be empty");
        require(!domains[msg.address].registered, "Domain already registered");
        require(domains[_name].registered == false, "Domain already exists");

        domains[_name] = Domain({
            name: _name,
            owner: msg.address,
            registered: true
        });

        emit DomainRegistered(_name, _name, msg.address);
    }

    // Update the owner of an existing ENS domain
    function updateDomainOwner(string memory _domainId, address _newOwner) public {
        require(bytes(_domainId).length > 0, "Domain ID cannot be empty");
        require(domains[_domainId].owner == msg.address, "Only owner can update");
        require(domains[_domainId].registered, "Domain not registered");

        domains[_domainId].owner = _newOwner;

        emit DomainOwnershipTransferred(_domainId, msg.address, _newOwner);
    }

    // Query the status of an ENS domain
    function queryDomainStatus(string memory _domainId) public view returns (bool) {
        require(bytes(_domainId).length > 0, "Domain ID cannot be empty");
        return domains[_domainId].registered;
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}