// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract MosslandNFT is Ownable, AccessControl {
    uint256 public tokenCounter = 0;
    mapping(string => JSON) public tokenMetadata;
    EnumerableSet.ControlledInterface public ownedTokens;

    event NFTCreated(uint256 tokenId, JSON metadata, address owner);
    event NFTTransferred(uint256 tokenId, address from, address to);

    // Constructor
    constructor() {
        AccessControl.grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    // Modifier to restrict access to only the owner and those with the admin role
    modifier onlyAdmin() {
        require(msg.sender == owner || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Only admin can call this function");
        _;
    }

    // Mint NFT
    function mintNFT(JSON metadata) public onlyAdmin {
        require(bytes(metadata).length > 0, "Metadata cannot be empty");

        uint256 tokenId = tokenCounter++;

        tokenMetadata[tokenId] = metadata;
        ownedTokens.add(tokenId);

        emit NFTCreated(tokenId, metadata, msg.sender);
    }

    // Transfer NFT
    function transferNFT(uint256 tokenId, address recipient) public onlyAdmin {
        require(tokenId > 0, "Token ID must be greater than 0");
        require(tokenMetadata[tokenId] != null, "Token does not exist");
        require(ownedTokens.contains(tokenId), "Token is not owned");
        require(recipient != address(0), "Recipient address cannot be zero");

        tokenMetadata[tokenId] = null;
        ownedTokens.remove(tokenId);

        // Transfer ownership
        tokenMetadata[tokenId]["owner"] = recipient;
        ownedTokens.add(tokenId);

        emit NFTTransferred(tokenId, msg.sender, recipient);
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {}

    // Helper function to check if an address has a specific role
    function hasRole(bytes32 role, address user) public view returns (bool) {
        return (AccessControl.hasRole(role, user));
    }
}