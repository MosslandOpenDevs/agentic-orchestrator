// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract PortfolioRebalanceContract is Ownable, AccessControl {
    using SafeMath for uint256;

    struct PortfolioAsset {
        uint256 quantity;
    }

    event RebalanceExecuted(string riskParameterId, uint256 timestamp);

    uint256 public lastRebalanceTimestamp;
    address public owner;

    mapping(string => uint256) public riskParameterIds;
    mapping(string => PortfolioAsset[]) public portfolios;

    constructor() {
        owner = msg.sender;
        lastRebalanceTimestamp = 0;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function setRiskParameterId(string memory _riskParameterId) external onlyOwner {
        riskParameterIds[_riskParameterId] = block.timestamp;
    }

    function addPortfolio(string memory _portfolioName, PortfolioAsset[] memory _assets) external onlyOwner {
        portfolios[_portfolioName] = _assets;
    }

    function executeRebalance(string memory riskParameterId) external {
        require(riskParameterIds[riskParameterId] > 0, "Risk parameter not set");
        require(block.timestamp > riskParameterIds[riskParameterId], "Rebalance already executed");

        uint256 timestamp = block.timestamp;
        lastRebalanceTimestamp = timestamp;
        emit RebalanceExecuted(riskParameterId, timestamp);

        // Placeholder for rebalancing logic - Replace with your actual strategy
        for (uint256 i = 0; i < portfolios.length; i++) {
            if (portfolios[i].length > 0) {
                // Example:  Simple rebalancing -  This needs to be replaced with your actual logic
                for (uint256 j = 0; j < portfolios[i].length; j++) {
                    portfolios[i][j].quantity = 100; // Example: Set all assets to 100
                }
            }
        }
    }

    // Access Control functions
    function grantRole(address _role, address _target) external onlyOwner {
        _grantRole(_role, _target);
    }

    function revokeRole(address _role, address _target) external onlyOwner {
        _revokeRole(_role, _target);
    }

    function getOwner() external view returns (address) {
        return owner;
    }
}