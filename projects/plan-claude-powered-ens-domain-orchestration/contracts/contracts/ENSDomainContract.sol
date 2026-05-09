// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract ENSDomainContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(string => address) private domains;
    mapping(string => uint256) private tokenIdToDomain;
    string public baseDomain = "mossland.eth"; // Default base domain
    event DomainRegistered(string name, address owner, uint256 tokenId);
    event DomainTransferred(address from, address to, uint256 tokenId);

    constructor() {
        // Ensure base domain is set
        require(bytes(baseDomain).length > 0, "Base domain must be non-empty");
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Function to register a new ENS domain
    function registerDomain(string memory name) public onlyOwner {
        require(bytes(name).length > 0, "Domain name must be non-empty");
        require(domains[name] == address(0), "Domain already registered");

        uint256 tokenId = generateTokenId();
        domains[name] = msg.sender;
        tokenIdToDomain[name] = tokenId;
        emit DomainRegistered(name, msg.sender, tokenId);
    }

    // Function to transfer ownership of an ENS domain
    function transferDomain(string memory name, address newOwner) public onlyOwner {
        require(bytes(name).length > 0, "Domain name must be non-empty");
        require(domains[name] != address(0), "Domain not registered");
        require(newOwner != address(0), "New owner must be a valid address");

        domains[name] = newOwner;
        emit DomainTransferred(domains[name], newOwner, tokenIdToDomain[name]);
    }

    // Helper function to generate a unique token ID
    function generateTokenId() internal pure returns (uint256) {
        uint256 now = uint256(block.timestamp);
        return now;
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {
        revert("This contract does not accept Ether");
    }

    // Access Control functions (Inherited from AccessControl)
    function grantRole(address _role, address _user) public onlyOwner {
        _grantRole(_role, _user);
    }

    function revokeRole(address _role, address _user) public onlyOwner {
        _revokeRole(_role, _user);
    }
}