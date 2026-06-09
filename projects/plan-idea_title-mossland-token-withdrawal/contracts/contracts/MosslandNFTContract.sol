// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract MosslandNFTContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(address => uint256) public nftBalances;
    event WithdrawalInitiated(address nftAddress, address senderAddress, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function depositNFT(address nftAddress) public {
        require(nftBalances[msg.sender] == 0, "User already has an NFT");
        require(nftAddress != address(0), "Invalid NFT address");
        nftBalances[msg.sender] = 1;
        emit WithdrawalInitiated(nftAddress, msg.sender, block.timestamp);
    }

    function withdrawNFT(address nftAddress, address senderAddress) public {
        require(nftBalances[senderAddress] > 0, "User does not own this NFT");
        require(nftAddress != address(0), "Invalid NFT address");

        nftBalances[senderAddress] = 0;
        emit WithdrawalInitiated(nftAddress, senderAddress, block.timestamp);
    }

    function transferNFT(address nftAddress, address senderAddress) public {
        require(nftBalances[senderAddress] > 0, "User does not own this NFT");
        require(nftAddress != address(0), "Invalid NFT address");

        nftBalances[senderAddress] = 0;
        nftBalances[msg.sender] = 1;
        emit WithdrawalInitiated(nftAddress, senderAddress, block.timestamp);
    }

    // Fallback function to receive ETH (reentrancy guard)
    receive() external payable onlyReentrancy {
        reEnter();
    }
}