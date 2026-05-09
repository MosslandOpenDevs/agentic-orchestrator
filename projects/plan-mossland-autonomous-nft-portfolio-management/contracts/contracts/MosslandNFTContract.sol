// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract MosslandNFTContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(uint256 => address) public tokenIds;
    event NFTMinted(address owner, uint256 tokenId);
    event NFTTransferred(address owner, address newOwner, uint256 tokenId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function mintNFT(uint256 tokenId) public onlyOwner {
        require(tokenIds[tokenId] == address(0), "Token ID already exists.");
        tokenIds[tokenId] = msg.sender;
        emit NFTMinted(msg.sender, tokenId);
    }

    function transferNFT(address from, address to, uint256 tokenId) public {
        require(tokenIds[tokenId] != address(0), "Token ID does not exist.");
        require(from != to && tokenIds[tokenId] != to, "Cannot transfer to self or existing owner.");
        require(AccessControl.getActiveSheet(msg.sender) == msg.sender, "Only the active account can transfer");

        tokenIds[tokenId] = to;
        emit NFTTransferred(to, from, tokenId);
    }

    // Fallback function to receive ETH
    receive() external payable {}

    // Allows the owner to change the owner address
    function changeOwner(address newOwner) public onlyOwner {
        owner = newOwner;
    }

    // Helper function to get the owner address
    function getOwner() public view returns (address) {
        return owner;
    }
}