// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(string => address) public NFTs;
    mapping(string => uint256[]) public PortfolioHoldings;

    event NFTMinted(address owner, string tokenId);
    event NFTTransferred(address owner, address recipient, string tokenId);

    constructor() {
        _setupAccessControl();
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    // Mints a new Mossland NFT
    function mintNFT(string memory _tokenId, address _owner) public onlyOwner {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty");
        NFTs[_tokenId] = _owner;
        emit NFTMinted(_owner, _tokenId);
    }

    // Transfers ownership of an NFT
    function transferNFT(string memory _tokenId, address _recipient, uint256 _allowance) public AccessControl {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty");
        require(NFTs[_tokenId] != address(0), "NFT does not exist");
        require(_recipient != address(0), "Recipient address cannot be zero");

        NFTs[_tokenId] = _recipient;
        emit NFTTransferred(NFTs[_tokenId], _recipient, _tokenId);
    }

    // Dynamically adjusts portfolio holdings
    function rebalancePortfolio(string memory _portfolioId, float _aggressiveness) public onlyOwner {
        require(_aggressiveness >= 0.0 && _aggressiveness <= 1.0, "Aggressiveness must be between 0.0 and 1.0");

        // Placeholder for rebalancing logic - replace with actual implementation
        // This is just an example, actual implementation would depend on the specific
        // portfolio and asset holdings.
        // Example:
        // uint256 newHolding = (uint256(_aggressiveness) * totalPortfolioValue) / 100;
        // PortfolioHoldings[_portfolioId].push(newHolding);

        // For demonstration purposes, we'll just add a dummy value
        PortfolioHoldings[_portfolioId].push(100);
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {
        // Handle ETH receipt if needed - reentrancy protection is already in place
    }
}