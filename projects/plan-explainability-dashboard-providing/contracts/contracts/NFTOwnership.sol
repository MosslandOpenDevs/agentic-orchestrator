// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NFTOwnership is Ownable, AccessControl {
    address public ownerAddress;
    mapping(string => address) public tokenIdToOwner;

    event OwnershipTransferred(address owner, string tokenId);

    /**
     * @dev Constructor
     */
    constructor() {
        ownerAddress = msg.sender;
        emit OwnershipTransferred(ownerAddress, "0");
    }

    /**
     * @dev Transfers an NFT to a new owner.
     * @param from The address of the current owner.
     * @param to The address of the new owner.
     * @param tokenId The token ID of the NFT to transfer.
     */
    function transferNFT(address from, address to, string memory tokenId) public {
        // Input validation
        require(from != address(0), "From address cannot be zero address");
        require(to != address(0), "To address cannot be zero address");
        require(bytes(tokenId).length > 0, "Token ID cannot be empty");

        // Check if the current owner owns the NFT
        require(tokenIdToOwner[tokenId] == from, "Only the owner can transfer this NFT");

        // Transfer the NFT
        tokenIdToOwner[tokenId] = to;
        emit OwnershipTransferred(to, tokenId);
    }

    /**
     * @dev Checks if the owner address owns the specified NFT.
     * @param owner The address to check.
     * @param tokenId The token ID of the NFT to check.
     * @return True if the owner address owns the specified NFT, false otherwise.
     */
    function isOwner(address owner, string memory tokenId) public view returns (bool) {
        // Input validation
        require(bytes(tokenId).length > 0, "Token ID cannot be empty");

        return tokenIdToOwner[tokenId] == owner;
    }

    /**
     * @dev Allows only the owner to call this function.
     */
    function onlyOwner() public view {
        require(msg.sender == ownerAddress, "Only the owner can call this function");
    }
}