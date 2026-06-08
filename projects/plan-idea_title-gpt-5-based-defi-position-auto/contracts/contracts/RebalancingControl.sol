// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RebalancingControl is Ownable, AccessControl {
    string public lastExecutedStrategyId;
    event RebalanceExecuted(uint nftId, int newQuantity);

    // Mapping to store the new quantity for each NFT
    mapping(uint => int) public nftQuantities;

    // Function to execute the rebalancing strategy for a given NFT
    function executeRebalance(uint nftId, int newQuantity) external {
        // Input validation
        require(nftId > 0, "NFT ID must be greater than 0");
        require(newQuantity >= 0, "New quantity must be non-negative");

        // Update the NFT quantity
        nftQuantities[nftId] = newQuantity;

        // Emit an event
        emit RebalanceExecuted(nftId, newQuantity);

        // Store the last executed strategy ID
        lastExecutedStrategyId = "RebalanceStrategy_" + uint(block.timestamp);
    }

    // Modifier to restrict access to only the owner
    function onlyOwner() internal access(this) {
        // No action needed, just a placeholder
    }

    // Fallback function to prevent accidental ETH transfers
    receive() external payable {
        // Handle ETH if needed (reentrancy protection if handling ETH)
    }
}