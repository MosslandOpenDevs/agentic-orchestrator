// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract NFTContract is Ownable, AccessControl {
    using SafeMath for uint256;

    struct NFTMetadata {
        string name;
        string symbol;
        string description;
        uint256 royaltyPercentage;
        uint256 mintLimit;
        bool isMutable;
    }

    mapping(string => NFTMetadata) public nftMetadata;
    mapping(string => address) public tokenOwners;
    mapping(string => uint256) public tokenPrices;
    mapping(string => bool) public isSold;
    mapping(string => uint256) public totalSupply;

    event NFTCreated(string tokenId, string name, string symbol, NFTMetadata metadata);
    event NFTTransferred(address from, address to, string tokenId, NFTMetadata metadata);

    constructor() {
        // Initialize Ownable
        _init();
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Mint a new NFT
    function mintNFT(string memory _name, string memory _symbol, NFTMetadata memory _metadata) external onlyOwner {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_symbol).length > 0, "Symbol cannot be empty");
        require(_metadata.name.length > 0, "Metadata name cannot be empty");
        require(_metadata.symbol.length > 0, "Metadata symbol cannot be empty");

        string memory tokenId = string(uint256(block.timestamp));
        require(!isSold[tokenId], "NFT already exists");

        nftMetadata[tokenId] = _metadata;
        tokenOwners[tokenId] = msg.sender;
        tokenPrices[tokenId] = 0; // Initial price
        totalSupply[tokenId] = 1;
        isSold[tokenId] = true;

        emit NFTCreated(tokenId, _name, _symbol, _metadata);
    }

    // Transfer ownership of an NFT
    function transferNFT(string memory _tokenId, address _to, uint256 _price) external AccessControl {
        require(bytes(_tokenId).length > 0, "Token ID cannot be empty");
        require(tokenOwners[_tokenId] != address(0), "NFT does not exist");
        require(_to != address(0), "Recipient address cannot be zero");
        require(!isSold[_tokenId], "NFT already exists");

        NFTMetadata memory metadata = nftMetadata[_tokenId];
        require(metadata.mintLimit > 0 && totalSupply[_tokenId] < metadata.mintLimit, "Mint limit reached");

        // Check if the price is valid
        if (_price > 0) {
            tokenPrices[_tokenId] = _price;
        }

        tokenOwners[_tokenId] = _to;
        totalSupply[_tokenId] += 1;

        emit NFTTransferred(tokenOwners[_tokenId], _to, _tokenId, metadata);
    }

    // Get NFT metadata
    function getNFTMetadata(string memory _tokenId) public view returns (NFTMetadata memory) {
        NFTMetadata memory metadata = nftMetadata[_tokenId];
        return metadata;
    }

    // Get token price
    function getTokenPrice(string memory _tokenId) public view returns (uint256) {
        return tokenPrices[_tokenId];
    }

    // Get total supply
    function getTotalSupply(string memory _tokenId) public view returns (uint256) {
        return totalSupply[_tokenId];
    }
}