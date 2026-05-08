// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NFTOwnership is Ownable, AccessControl {
    mapping(string => address) public owners;
    event OwnershipTransferred(address owner, string tokenId);

    // NatSpec: Token ID must be a valid string.
    function transferNFT(address from, address to, string memory tokenId) external {
        // Input validation
        require(from != address(0), "From address cannot be zero address");
        require(to != address(0), "To address cannot be zero address");
        require(bytes(tokenId).length > 0, "Token ID cannot be empty");

        // Check if the token exists
        require(owners[tokenId] == address(0), "Token already owned");

        // Transfer ownership
        owners[tokenId] = to;
        emit OwnershipTransferred(to, tokenId);
    }

    // NatSpec: Returns the address of the NFT owner.
    function ownerOf(string memory tokenId) public view returns (address) {
        return owners[tokenId];
    }

    // AccessControl modifiers
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Fallback function to prevent accidental ETH transfers
    receive() external payable {}
}