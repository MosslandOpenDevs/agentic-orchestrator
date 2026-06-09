// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MOCOracleContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(address => uint256) public userBalances;

    struct Portfolio {
        string portfolioId;
        uint256[] holdings;
        string riskProfile;
    }

    mapping(string => Portfolio) public portfolios;

    event PortfolioUpdated(
        string portfolioId,
        uint256[] holdings,
        string riskProfile,
        uint256 timestamp
    );

    constructor() {
        _setupAccessControl();
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Function to update a user's portfolio holdings and risk profile
    function updatePortfolio(
        string memory portfolioId,
        uint256[] memory holdings,
        string memory riskProfile
    ) public {
        require(portfolioId.length > 0, "Portfolio ID cannot be empty");
        require(holdings.length > 0, "Holdings array cannot be empty");
        require(riskProfile.length > 0, "Risk profile cannot be empty");

        // Input Validation: Check if portfolioId already exists
        if (portfolios[portfolioId].portfolioId.length > 0) {
            // Update existing portfolio
            portfolios[portfolioId] = Portfolio(
                portfolioId,
                holdings,
                riskProfile
            );
            emit PortfolioUpdated(
                portfolioId,
                holdings,
                riskProfile,
                block.timestamp
            );
        } else {
            // Create new portfolio
            portfolios[portfolioId] = Portfolio(
                portfolioId,
                holdings,
                riskProfile
            );
            emit PortfolioUpdated(
                portfolioId,
                holdings,
                riskProfile,
                block.timestamp
            );
        }
    }

    // Function to generate a rebalancing rationale using the ChatGPT API
    function generateRebalanceRationale(
        string memory portfolioId,
        uint256[] memory holdings,
        string memory riskProfile
    ) public returns (string memory) {
        // Placeholder for ChatGPT API call
        // In a real implementation, this function would call the ChatGPT API
        // and return the generated rationale.
        // For now, it returns a simple string.
        return "Rebalancing rationale generated for portfolio: " + portfolioId;
    }

    // Function to get portfolio holdings by ID
    function getPortfolio(string memory portfolioId) public view returns (Portfolio memory) {
        return portfolios[portfolioId];
    }

    // Function to get user balance by address
    function getUserBalance(address user) public view returns (uint256) {
        return userBalances[user];
    }

    // Function to set user balance
    function setUserBalance(address user, uint256 balance) public onlyOwner {
        userBalances[user] = balance;
    }
}