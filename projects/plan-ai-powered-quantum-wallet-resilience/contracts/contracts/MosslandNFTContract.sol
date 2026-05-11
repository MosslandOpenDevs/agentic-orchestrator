// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ERC1271.sol";

contract MosslandNFTContract is Ownable, AccessControl, ERC1271 {
    uint256 public totalSupply;
    mapping(uint256 => address) public tokenIds;

    event NFTMinted(uint256 tokenId, address owner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        _setupAccessControl();
    }

    function mintNFT(uint256 tokenId, address owner) public onlyOwner {
        require(tokenId > 0, "Token ID must be greater than 0");
        require(tokenId <= 10000, "Token ID exceeds maximum limit");
        require(tokenIds[tokenId] == address(0), "Token ID already exists");

        tokenIds[tokenId] = owner;
        totalSupply++;
        emit NFTMinted(tokenId, owner);
    }

    function transferNFT(address from, address to, uint256 tokenId) public {
        require(from != address(0), "From address cannot be zero");
        require(to != address(0), "To address cannot be zero");
        require(tokenId > 0, "Token ID must be greater than 0");
        require(tokenIds[tokenId] == from, "Invalid token ID");
        require(tokenIds[tokenId] != address(0), "Token ID does not exist");

        tokenIds[tokenId] = to;
    }

    function owner() public view returns (address) {
        return owner();
    }
}