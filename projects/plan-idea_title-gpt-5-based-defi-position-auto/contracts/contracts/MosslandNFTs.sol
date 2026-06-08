// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTs is Ownable, AccessControl {
    mapping(string => uint256) public tokenPrices;
    mapping(string => address) public tokenOwners;
    string public baseURI;
    string public metadataURI;

    event NFTMinted(string tokenId, address owner);
    event NFTTransferred(address from, address to, string tokenId);

    constructor(
        string memory _baseURI,
        string memory _metadataURI
    ) {
        baseURI = _baseURI;
        metadataURI = _metadataURI;
    }

    modifier onlyAdmin() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function setTokenPrice(string memory _tokenId, uint256 _price) public onlyAdmin {
        require(tokenPrices[_tokenId] == 0, "Token already minted");
        tokenPrices[_tokenId] = _price;
        emit NFTMinted(_tokenId, msg.sender);
    }

    function mintNFT(string memory _tokenId, address _owner) public {
        require(tokenPrices[_tokenId] == 0, "Token already minted");
        require(_owner != address(0), "Invalid owner address");

        tokenOwners[_tokenId] = _owner;
        emit NFTMinted(_tokenId, _owner);
    }

    function transferNFT(string memory _tokenId, address _from, address _to) public {
        require(tokenOwners[_tokenId] != address(0), "Token does not exist");
        require(_from != address(0), "Invalid from address");
        require(_to != address(0), "Invalid to address");

        // Check if the caller owns the token
        if (tokenOwners[_tokenId] != _from) {
            revert("Caller does not own this token");
        }

        tokenOwners[_tokenId] = _to;
        emit NFTTransferred(_from, _to, _tokenId);
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {}
}