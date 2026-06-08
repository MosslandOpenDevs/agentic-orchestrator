// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract MosslandNFTContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(uint256 => address) public tokenIds;
    mapping(uint256 => uint256) public balances;
    event NFTMinted(uint256 tokenId, address owner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function mint(uint256 tokenId, address owner) public onlyOwner {
        require(tokenIds[tokenId] == 0, "Token ID already exists");
        tokenIds[tokenId] = owner;
        balances[tokenId] = 1;
        emit NFTMinted(tokenId, owner);
    }

    function transferFrom(address from, address to, uint256 tokenId) public {
        require(tokenIds[tokenId] != 0, "Token ID does not exist");
        require(balances[tokenId] > 0, "Token has no balance");
        require(from != to, "Cannot transfer to yourself");

        // Prevent reentrancy
        _reentrancyGuard.notReentrant();

        // Transfer ownership
        tokenIds[tokenId] = to;
        balances[tokenId]--;

        // Check if the sender has any remaining tokens
        if (balances[from] > 0) {
            // Transfer tokens to the recipient
            tokenIds[to] = to;
            balances[to]++;
        }

        emit NFTMinted(tokenId, to);
    }

    function balanceOf(uint256 tokenId) public view returns (uint256) {
        return balances[tokenId];
    }

    // Access Control functions
    function grantRole(address recipient, string memory role) public onlyOwner {
        _grantRole(recipient, role);
    }

    function revokeRole(address recipient, string memory role) public onlyOwner {
        _revokeRole(recipient, role);
    }

    // Fallback function to receive ETH (reentrancy guard)
    receive() external payable {}
}