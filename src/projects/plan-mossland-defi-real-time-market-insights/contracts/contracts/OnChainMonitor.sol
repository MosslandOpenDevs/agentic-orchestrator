// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract OnChainMonitor is Ownable, ReentrancyGuard {
    struct SecurityAlert {
        string alertType;
    }

    mapping(address => SecurityAlert[]) public userAlerts;

    event NewSecurityAlert(address indexed userAddress, string alertType);

    constructor() {}

    function monitorTransactions(address userAddress, uint256 transactionId) external onlyOwner nonReentrant {
        require(userAddress != address(0), "Invalid user address");
        
        // Example logic for generating alerts
        if (transactionId % 2 == 0) {
            _generateAlert(userAddress, "EvenTransactionID");
        } else {
            _generateAlert(userAddress, "OddTransactionID");
        }
    }

    function _generateAlert(address userAddress, string memory alertType) internal {
        SecurityAlert memory newAlert = SecurityAlert({
            alertType: alertType
        });
        
        userAlerts[userAddress].push(newAlert);
        emit NewSecurityAlert(userAddress, alertType);
    }
}