// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/datetime.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract ENSRegistryContract is Ownable, AccessControl {
    using EnumerableSet for ArrayGroupBy<string>;
    using Datetime for datetimes;

    struct ENSDomain {
        string registrar;
        datetime expiry;
        bool isRegistered;
    }

    mapping(string => ENSDomain) public domains;
    mapping(string => uint256) public domainIds;
    EnumerableSet.ControlledArrayGroupBy<string> public domainNames;

    event DomainRegistered(string domainId, string domainName, string registrar, datetime registrationExpiry);
    event DomainUpdated(string domainId, datetime expiry);

    constructor() {
        // Initialize the domainNames set
        domainNames = EnumerableSet.ControlledArrayGroupBy<string>({
            data: new string[](0),
            hash: false
        });
    }

    // Modifier to restrict access to the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Function to query domain ownership
    function queryDomainOwnership(string memory _domainName) public view returns (bool) {
        return domains[_domainName].isRegistered;
    }

    // Function to register a new ENS domain
    function registerDomain(string memory _domainName, string memory _registrar) public onlyOwner {
        require(_domainName.length > 0, "Domain name cannot be empty");
        require(!domains[_domainName].isRegistered, "Domain already registered");

        uint256 newDomainId = domainIds[_domainName];
        if (newDomainId == 0) {
            newDomainId = domainIds.length;
            domainNames.add(_domainName);
        }

        domains[_domainName].registrar = _registrar;
        domains[_domainName].expiry = datetimes.now().add(datetime.days(365)); // Default expiry
        domains[_domainName].isRegistered = true;
        domainIds[_domainName] = newDomainId;

        emit DomainRegistered(newDomainId, _domainName, _registrar, domains[_domainName].expiry);
    }

    // Function to update the domain registration expiry date
    function updateDomainRegistrationExpiry(string memory _domainId, datetime _expiryDate) public onlyOwner {
        require(_domainId.length > 0, "Domain ID cannot be empty");
        require(domains[_domainId].isRegistered, "Domain not registered");

        domains[_domainId].expiry = _expiryDate;

        emit DomainUpdated(_domainId, _expiryDate);
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}