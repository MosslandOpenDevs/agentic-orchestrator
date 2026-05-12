// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract MosslandPortfolioContract is Ownable, AccessControl {
    using Math for float;
    using EnumerableSet for uint[];

    mapping(string => RWAPortfolio) public portfolios;
    mapping(string => uint[]) public assetAllocations;
    event AssetQuantityUpdated(string assetId, float oldQuantity, float newQuantity);
    event PortfolioRebalanced(string portfolioId, uint[] newAssetAllocation);

    // Struct for RWA Portfolio
    struct RWAPortfolio {
        string portfolioId;
        uint[] assetQuantities;
    }

    // Risk Tolerance - String representation for simplicity
    string public riskTolerance;

    // Constructor
    constructor() {
        riskTolerance = "Medium";
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Function to update asset quantity
    function updateAssetQuantity(string memory assetId, float quantity) external accessControl {
        require(quantity >= 0, "Quantity must be non-negative");
        require(portfolios[assetId].assetQuantities.length > 0, "Asset must exist in portfolio");

        // Input validation - prevent large changes
        float currentQuantity = portfolios[assetId].assetQuantities[0];
        if (quantity > currentQuantity * 2) {
            quantity = currentQuantity * 2; // Limit change to 2x
        }

        // Update the portfolio
        portfolios[assetId].assetQuantities[0] = quantity;

        // Emit event
        emit AssetQuantityUpdated(assetId, currentQuantity, quantity);
    }

    // Function to rebalance portfolio
    function rebalancePortfolio(string memory _riskTolerance) external accessControl onlyOwner {
        require(_riskTolerance != "", "Risk tolerance cannot be empty");

        riskTolerance = _riskTolerance;

        // Rebalance logic - Simplified for demonstration
        for (uint i = 0; i < portfolios.length; i++) {
            // Calculate new allocation based on risk tolerance
            // This is a placeholder - Replace with actual rebalancing logic
            float newQuantity = portfolios[i].assetQuantities[0] * math.sqrt(0.5); // Example: 50/50 split

            // Update the portfolio
            portfolios[i].assetQuantities[0] = newQuantity;

            // Store the new allocation
            assetAllocations[i] = new uint[](portfolios[i].assetQuantities.length);
            portfolios[i].assetQuantities[0] = newQuantity;
            assetAllocations[i][0] = newQuantity;

            // Emit event
            emit PortfolioRebalanced(i, assetAllocations[i]);
        }
    }

    // Getter for portfolio allocations
    function getAssetAllocation(string memory portfolioId) public view returns (uint[]) {
        require(portfolios[portfolioId].portfolioId == portfolioId, "Invalid portfolio ID");
        return assetAllocations[portfolioId];
    }
}