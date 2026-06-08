// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract NFTOwnershipContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(address => string) public tokenAddresses;
    uint256 public tokenIdCounter = 0;

    event NFTMinted(address tokenAddress, address ownerAddress, uint256 tokenId);

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    modifier onlyToken(address tokenAddress) {
        require(tokenAddresses[tokenAddress] != "", "Token address not registered");
        _;
    }

    function mintNFT(address tokenAddress, address ownerAddress) public onlyOwner {
        require(tokenAddresses[tokenAddress] != "", "Token address not registered");
        require(tokenIdCounter >= 0, "Token ID must be non-negative");

        tokenIdCounter++;
        tokenAddresses[tokenAddress] = "NFT_" + uint256(tokenIdCounter);

        emit NFTMinted(tokenAddress, ownerAddress, tokenIdCounter);
    }

    function changeOwner(address tokenAddress, address newOwner) public onlyOwner {
        require(tokenAddresses[tokenAddress] != "", "Token address not registered");
        require(newOwner != address(0), "New owner address cannot be zero");

        // No actual ownership transfer - this is a simplified example.
        // In a real application, you'd use ERC721 transfer functions.
    }

    function setTokenAddress(address tokenAddress, string memory metadata) public onlyOwner {
        require(tokenAddress != address(0), "Token address cannot be zero");
        tokenAddresses[tokenAddress] = metadata;
    }

    // Access Control functions
    function grantRole(address recipient, string memory role) public onlyOwner {
        _grantRole(recipient, role);
    }

    function revokeRole(address recipient, string memory role) public onlyOwner {
        _revokeRole(recipient, role);
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}