// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandPortfolioContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(address => uint256[]) public portfolioHoldings;
    mapping(address => bool) public isControlled;

    event NFTDeposited(address owner, address depositedAddress, uint256 tokenId);
    event NFTWithdrawn(address owner, address withdrawnAddress, uint256 tokenId);

    // Constructor
    constructor() {
        isControlled.resize(1000, false); // Adjust size as needed
    }

    // Modifier to restrict access to the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    // Deposit NFT into the portfolio
    function depositNFT(string memory _tokenId, uint256 _amount) public {
        require(bytes(_tokenId).length > 0, "Token ID cannot be empty.");
        require(_amount > 0, "Amount must be greater than 0.");

        // Validate tokenId -  Simple check, can be expanded with NFT metadata lookup
        // For production, integrate with NFT metadata storage (e.g., IPFS)
        // This is a placeholder for a more robust validation
        // This implementation assumes tokenId is a string representation of the token ID.
        // In a real-world scenario, you would likely use a more sophisticated
        // mechanism to verify the token's authenticity and ownership.

        portfolioHoldings[msg.sender].push(_amount);
        emit NFTDeposited(msg.sender, address(0), _amount);
    }

    // Withdraw NFT from the portfolio
    function withdrawNFT(string memory _tokenId, uint256 _amount) public {
        require(bytes(_tokenId).length > 0, "Token ID cannot be empty.");
        require(_amount > 0, "Amount must be greater than 0.");

        uint256 index = -1;
        for (uint256 i = 0; i < portfolioHoldings[msg.sender].length; i++) {
            if (portfolioHoldings[msg.sender][i] == _amount) {
                index = i;
                break;
            }
        }

        require(index != -1, "NFT not found in portfolio.");

        portfolioHoldings[msg.sender][index] = 0;
        emit NFTWithdrawn(msg.sender, address(0), _amount);
    }

    // Rebalance Portfolio - Placeholder for future implementation
    function rebalancePortfolio() public onlyOwner {
        // This function is a placeholder.  A real implementation would
        // involve fetching market data, predicting future prices, and
        // adjusting portfolio holdings accordingly.
        // This is a simplified example and should be replaced with a robust
        // rebalancing strategy.
        for (uint256 i = 0; i < portfolioHoldings[msg.sender].length; i++) {
            portfolioHoldings[msg.sender][i] = 0;
        }
        emit NFTDeposited(msg.sender, address(0), 0);
    }

    // Fallback function to prevent accidental ETH transfers
    receive() external payable {
        revert("This contract does not accept ETH.");
    }

    // Access control functions
    function grantRole(address _role, address _target) public onlyOwner {
        _grantRole(msg.sender, _role);
    }

    function revokeRole(address _role, address _target) public onlyOwner {
        _revokeRole(_role, _target);
    }
}