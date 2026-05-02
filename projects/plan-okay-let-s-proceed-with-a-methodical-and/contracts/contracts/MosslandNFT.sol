// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "@openzeppelin/contracts/utils/bytes32.sol";

contract MosslandNFT is Ownable, AccessControl {
    mapping(string => JSON) public tokenMetadata;
    uint256 public tokenCounter;
    EnumerableSet.ControlledInterface public ownedTokens;

    event NFTCreated(string tokenId, string prompt, address owner);
    event NFTTransferred(string tokenId, address from, address to);

    // Constructor
    constructor() {
        tokenCounter = 0;
    }

    // Modifier to restrict access to the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function.");
        _;
    }

    // Mint a new NFT
    function mintNFT(string memory prompt) public onlyOwner {
        tokenCounter++;
        string memory tokenId = string(abi.encodePacked("MosslandNFT", tokenCounter));
        tokenMetadata[tokenId] = JSON.stringify({
            prompt: prompt,
            owner: msg.sender
        });
        ownedTokens.add(tokenId);
        emit NFTCreated(tokenId, prompt, msg.sender);
    }

    // Transfer ownership of an NFT
    function transferNFT(string memory tokenId, address recipient) public {
        require(tokenMetadata[tokenId] != "", "Token does not exist.");
        require(!ownedTokens.contains(tokenId), "Token already owned by recipient.");

        tokenMetadata[tokenId].prompt = tokenMetadata[tokenId].prompt;
        tokenMetadata[tokenId].owner = recipient;
        ownedTokens.add(tokenId);

        emit NFTTransferred(tokenId, msg.sender, recipient);
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {}

    // Access control functions
    function grantRole(address recipient) external onlyOwner {
        _grantRole(recipient, 0);
    }

    function revokeRole(address recipient) external onlyOwner {
        _revokeRole(recipient, 0);
    }

    // Helper function to get the owner address
    function getOwner() public view returns (address) {
        return owner();
    }
}