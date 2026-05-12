// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract PortfolioContract is Ownable, AccessControl {
    using SafeMath for float;
    mapping(string => Portfolio) public portfolios;

    enum RiskProfile {
        Conservative,
        Moderate,
        Aggressive
    }

    struct Portfolio {
        string portfolioId;
        string userId;
        RiskProfile riskProfile;
        float returnTarget;
        mapping(string => float) assets;
    }

    event PortfolioCreated(string portfolioId, string userId, RiskProfile riskProfile, float returnTarget);
    event AssetAdded(string portfolioId, string assetType, float quantity);

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function.");
        _;
    }

    modifier onlyPortfolioOwner(string memory _portfolioId) {
        require(msg.sender == portfolios[_portfolioId].userId, "Only portfolio owner can call this function.");
        _;
    }

    function createPortfolio(string memory _userId, RiskProfile _riskProfile, float _returnTarget) public onlyOwner {
        require(_userId.length > 0, "User ID cannot be empty.");
        require(_riskProfile != RiskProfile(0), "Risk profile must be specified.");
        require(_returnTarget > 0, "Return target must be greater than 0.");

        string memory portfolioId = generatePortfolioId();

        portfolios[portfolioId] = Portfolio({
            portfolioId: portfolioId,
            userId: _userId,
            riskProfile: _riskProfile,
            returnTarget: _returnTarget,
            assets: mapping(string => 0.0)
        });

        emit PortfolioCreated(portfolioId, _userId, _riskProfile, _returnTarget);
    }

    function addAsset(string memory _portfolioId, string memory _assetType, float _quantity) public onlyPortfolioOwner(_portfolioId) {
        require(_portfolioId.length > 0, "Portfolio ID cannot be empty.");
        require(_assetType.length > 0, "Asset type cannot be empty.");
        require(_quantity > 0, "Quantity must be greater than 0.");

        portfolios[_portfolioId].assets[_assetType] = _quantity;

        emit AssetAdded(_portfolioId, _assetType, _quantity);
    }

    function generatePortfolioId() internal pure returns (string memory) {
        return string(uint256(block.timestamp));
    }

    function updateReturnTarget(string memory _portfolioId, float _returnTarget) public onlyPortfolioOwner(_portfolioId) {
        require(_returnTarget > 0, "Return target must be greater than 0.");
        portfolios[_portfolioId].returnTarget = _returnTarget;
    }

    function getPortfolio(string memory _portfolioId) public view returns (Portfolio memory) {
        return portfolios[_portfolioId];
    }
}