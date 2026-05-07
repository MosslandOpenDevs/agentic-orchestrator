// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(uint256 => uint256) public tokenPrices;
    mapping(uint256 => address) public owners;

    event NFTMinted(address owner, uint256 tokenId);
    event NFTTransferred(address owner, address newOwner, uint256 tokenId);

    constructor() {
        // Initialize token prices (can be adjusted)
        tokenPrices[1] = 1 ether;
        tokenPrices[2] = 2 ether;
        tokenPrices[3] = 3 ether;
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Mint a new NFT token
    function mintNFT(uint256 tokenId) public payable {
        require(tokenPrices[tokenId] > 0, "Token price must be set");
        require(tokenId > 0, "Token ID must be greater than 0");

        // Check if the token is already minted
        if (owners[tokenId] != address(0)) {
            revert("Token already minted");
        }

        // Mint the NFT
        owners[tokenId] = msg.sender;

        // Transfer the funds to the owner
        payable(msg.sender).transfer(tokenPrices[tokenId]);

        // Emit the NFTMinted event
        emit NFTMinted(msg.sender, tokenId);
    }

    // Transfer ownership of an NFT token
    function transferNFT(address from, address to, uint256 tokenId) public {
        require(from != address(0), "From address cannot be zero");
        require(to != address(0), "To address cannot be zero");
        require(tokenId > 0, "Token ID must be greater than 0");
        require(owners[tokenId] != address(0), "Token must be owned");
        require(from != to, "Cannot transfer to yourself");

        // Check if the sender is the owner
        require(owners[tokenId] == from, "Only owner can transfer this token");

        // Transfer the NFT
        owners[tokenId] = to;

        // Emit the NFTTransferred event
        emit NFTTransferred(to, from, tokenId);
    }

    // Fallback function to receive ETH
    receive() external payable {}

    // Owner function to set token prices
    function setTokenPrice(uint256 tokenId, uint256 _price) public onlyOwner {
        require(_price > 0, "Price must be greater than 0");
        tokenPrices[tokenId] = _price;
    }

    // Owner function to change the owner
    function changeOwner(address _newOwner) public onlyOwner {
        emit NFTTransferred(msg.sender, _newOwner, 1);
    }
}