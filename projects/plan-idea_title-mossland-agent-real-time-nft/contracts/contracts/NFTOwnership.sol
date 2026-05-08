// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NFTOwnership is Ownable, AccessControl {
    mapping(address => string) public owner;
    string[] public tokenIds;

    event OwnershipTransferred(address owner, string tokenId);

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can perform this action");
        _;
    }

    // Function to transfer NFT ownership
    function transferNFT(address from, address to, string memory tokenId) public onlyOwner {
        require(owner[from] == tokenId, "Invalid NFT ID");
        require(owner[to] == "", "NFT already owned");

        owner[from] = "";
        owner[to] = tokenId;

        emit OwnershipTransferred(to, tokenId);
    }

    // Function to set the owner of an NFT
    function setOwner(address _from, string memory _tokenId) public {
        require(owner[_from] == "", "NFT already owned");
        owner[_from] = _tokenId;
        emit OwnershipTransferred(_from, _tokenId);
    }

    // Function to get the owner of an NFT
    function getOwner(string memory _tokenId) public view returns (address) {
        return owner[_tokenId];
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}