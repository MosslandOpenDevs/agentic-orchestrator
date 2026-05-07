// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(uint256 => uint256) public tokenPrices;
    uint256 public tokenSupply;
    uint256 public maxSupply;
    address public owner;

    event NFTMinted(uint256 tokenId, address mintedAddress);
    event NFTTransferred(uint256 tokenId, address from, address to);

    constructor(uint256 _maxSupply) {
        owner = msg.sender;
        tokenSupply = 0;
        maxSupply = _maxSupply;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    function setTokenPrice(uint256 _tokenId, uint256 _price) external onlyOwner {
        require(_tokenId > 0 && _tokenId <= maxSupply, "Invalid token ID.");
        require(_price > 0, "Price must be greater than zero.");
        tokenPrices[_tokenId] = _price;
    }

    function mintNFT(uint256 tokenId) external payable {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID.");
        require(tokenPrices[tokenId] > 0, "Token price must be set.");
        require(msg.value >= tokenPrices[tokenId], "Insufficient funds.");

        tokenSupply++;
        emit NFTMinted(tokenId, msg.sender);
    }

    function transferNFT(uint256 tokenId, address to) external {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID.");
        require(tokenPrices[tokenId] > 0, "Token price must be set.");
        require(msg.sender != to, "Cannot transfer to yourself.");

        // Check if the token is already owned by the sender
        if (tokenPrices[tokenId] > 0) {
            tokenPrices[tokenId] = 0;
        }

        emit NFTTransferred(tokenId, msg.sender, to);
    }

    // Fallback function to receive ETH
    receive() external payable {}

    // Owner can change max supply
    function setMaxSupply(uint256 _newMaxSupply) external onlyOwner {
        maxSupply = _newMaxSupply;
    }
}