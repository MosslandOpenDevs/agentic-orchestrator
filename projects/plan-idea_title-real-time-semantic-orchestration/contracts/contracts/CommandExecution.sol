// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/Ownable.sol";

contract CommandExecution is Ownable, AccessControl {
    mapping(address => object) public executions;
    event CommandExecuted(address agentId, string command, string result, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function.");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function executeCommand(address agentId, string memory command) public {
        require(agentId != address(0), "Agent ID cannot be zero.");
        require(bytes(command).length > 0, "Command cannot be empty.");

        // Input validation - basic check, can be expanded
        // For example, check command length, allowed characters, etc.

        string memory result = "Command executed successfully"; // Default result

        executions[agentId] = {
            "command": command,
            "result": result,
            "timestamp": block.timestamp
        };

        emit CommandExecuted(agentId, command, result, block.timestamp);
    }

    function getExecution(address agentId) public view returns (string memory command, string memory result, uint256 timestamp) {
        require(agentId != address(0), "Agent ID cannot be zero.");
        if (executions[agentId] != null) {
            return (
                executions[agentId].command,
                executions[agentId].result,
                executions[agentId].timestamp
            );
        } else {
            return (
                "",
                "",
                0
            );
        }
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}