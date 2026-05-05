// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

contract RavePortfolioContract is Ownable, AccessControl {
    using Math for uint256;

    map(string => Portfolio) public portfolios;
    mapping(string => uint256) public portfolioIdsToUserId;
    string public constant PORTFOLIO_ID_PREFIX = "PORTFOLIO_";

    struct Portfolio {
        uint256 riskTolerance;
        uint256 totalValue;
    }

    event PortfolioCreated(string portfolioId, string userId, uint256 riskTolerance);
    event PortfolioUpdated(string portfolioId, uint256 riskTolerance);

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function.");
        _;
    }

    function createPortfolio(string memory _userId, uint256 _riskTolerance) public {
        require(_userId != "", "User ID cannot be empty.");
        require(_riskTolerance > 0, "Risk tolerance must be greater than 0.");

        string memory portfolioId = PORTFOLIO_ID_PREFIX + string(uint256(block.timestamp));
        portfolios[portfolioId] = Portfolio({riskTolerance: _riskTolerance, totalValue: 0});
        portfolioIdsToUserId[portfolioId] = _userId;

        emit PortfolioCreated(portfolioId, _userId, _riskTolerance);
    }

    function updatePortfolio(string memory _portfolioId, uint256 _riskTolerance) public {
        require(_portfolioId != "", "Portfolio ID cannot be empty.");
        require(_riskTolerance > 0, "Risk tolerance must be greater than 0.");

        Portfolio storage portfolio = portfolios[_portfolioId];
        portfolio.riskTolerance = _riskTolerance;

        emit PortfolioUpdated(_portfolioId, _riskTolerance);
    }

    function rebalancePortfolio(string memory _portfolioId) public {
        require(_portfolioId != "", "Portfolio ID cannot be empty.");

        Portfolio storage portfolio = portfolios[_portfolioId];
        // Placeholder for rebalancing logic.  This needs to be implemented
        // based on the specific portfolio strategy.  This example just sets
        // the total value to the risk tolerance.
        portfolio.totalValue = portfolio.riskTolerance;
    }

    // Access control functions
    function grantRole(address _user, role _role) public onlyOwner {
        _grantRole(_user, _role);
    }

    function removeRole(address _user, role _role) public onlyOwner {
        _revokeRole(_user, _role);
    }
}