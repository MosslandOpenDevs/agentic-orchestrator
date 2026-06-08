// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract RebalancingContract is Ownable, AccessControl {
    uint256 public lastRebalanceTimestamp;
    address[] public authorizedAccounts;

    event RebalanceExecuted(nftPositions: address[]);

    EnumerableSet<address> public nftPositions;

    // Struct for NFT Position
    struct NFTPosition {
        address nftAddress;
        uint256 tokenId;
        uint256 quantity;
    }

    // Modifier to restrict access to authorized accounts
    modifier onlyAuthorized() {
        require(isAuthorized(), "Only authorized accounts can execute rebalancing.");
        _;
    }

    // Function to add an authorized account
    function addToAuthorized(address account) external onlyAuthorized {
        authorizedAccounts.add(account);
    }

    // Function to remove an authorized account
    function removeFromAuthorized(address account) external onlyAuthorized {
        uint256 index = authorizedAccounts.indexOf(account);
        require(index != uint256(0), "Account not authorized.");
        authorizedAccounts[index] = address(0);
    }

    // Function to check if an account is authorized
    function isAuthorized() public view returns (bool) {
        return authorizedAccounts.length > 0;
    }

    // Function to execute the rebalancing strategy
    function executeRebalance(NFTPosition[] memory _nftPositions) public onlyAuthorized {
        require(_nftPositions.length > 0, "No NFT positions provided.");

        lastRebalanceTimestamp = block.timestamp;
        nftPositions = _nftPositions;

        emit RebalanceExecuted(_nftPositions);
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}