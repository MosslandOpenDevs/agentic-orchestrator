// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(string => uint256) public tokenPrices;
    string public baseURI;
    string public metadataName;

    event NFTMinted(address owner, string tokenId, string metadata);
    event NFTTransferred(address from, address to, string tokenId);

    constructor(string _baseURI, string _metadataName) {
        baseURI = _baseURI;
        metadataName = _metadataName;
    }

    modifier onlyAdmin() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function setBaseURI(string memory _baseURI) public onlyAdmin {
        baseURI = _baseURI;
    }

    function setMetadataName(string memory _metadataName) public onlyAdmin {
        metadataName = _metadataName;
    }

    function mintNFT(string memory tokenId, string memory metadata) public {
        require(tokenPrices[tokenId] > 0, "Token price must be set");
        require(bytes(metadata).length > 0, "Metadata cannot be empty");

        // Mint the NFT
        _mint(msg.sender, tokenId);

        // Emit event
        emit NFTMinted(msg.sender, tokenId, metadata);
    }

    function transferNFT(address from, address to, string memory tokenId) public {
        require(tokenPrices[tokenId] > 0, "Token price must be set");
        require(from != to, "Cannot transfer to yourself");

        _transfer(from, to, tokenId);

        // Emit event
        emit NFTTransferred(from, to, tokenId);
    }

    function _transfer(address from, address to, string memory tokenId) internal {
        require(tokenPrices[tokenId] > 0, "Token price must be set");
        _mint(to, tokenId);
        _burn(from, tokenId);
    }

    // Helper function to burn tokens
    function _burn(address owner, string memory tokenId) internal {
        tokenPrices[tokenId] = 0;
    }

    // Fallback function to receive ETH
    receive() external payable {}
}