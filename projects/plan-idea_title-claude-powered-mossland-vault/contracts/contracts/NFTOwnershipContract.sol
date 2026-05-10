// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NFTOwnershipContract is Ownable, AccessControl {
    mapping(address => address) public ownerMap;
    event OwnershipTransferred(address indexed owner, address indexed tokenAddress);

    // Modifier to restrict access to only the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Verifies if a wallet address owns an NFT.
    function verifyOwnership(address tokenAddress) public view {
        require(ownerMap[msg.sender] == tokenAddress, "Not the owner of this NFT");
    }

    // Records ownership of an NFT for a given wallet address.
    function recordOwnership(address tokenAddress) public onlyOwner {
        require(ownerMap[msg.sender] == address(0), "Ownership already recorded");
        ownerMap[msg.sender] = tokenAddress;
        emit OwnershipTransferred(msg.sender, tokenAddress);
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}