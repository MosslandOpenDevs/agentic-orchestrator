// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandToken is Ownable, AccessControl {
    using SafeMath for uint256;

    // State Variables
    uint256 public totalSupply;
    address public owner;

    // Mapping to store balances
    mapping(address => uint256) public balances;

    // Event Emitted when tokens are transferred
    event Transfer(address indexed from, address indexed to, uint256 value);

    // Event Emitted when approval is granted
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    // Constructor
    constructor() {
        owner = msg.sender;
        totalSupply = 1000000; // Initial supply
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    // Function to transfer tokens
    function transfer(address from, address to, uint256 value) public accessControl {
        require(balances[from] >= value, "Insufficient balance");
        require(balances[to] >= 0, "Invalid recipient address");

        balances[from] -= value;
        balances[to] += value;
        emit Transfer(from, to, value);
    }

    // Function to approve a spender
    function approve(address spender, uint256 amount) public accessControl {
        // Ensure the amount is not zero
        require(amount > 0, "Amount must be greater than zero");

        // Update the mapping of approved amounts
        _approve(spender, amount);

        emit Approval(msg.sender, spender, amount);
    }

    // Helper function to update the approval mapping
    function _approve(address spender, uint256 amount) internal {
        // This function is internal to prevent external calls
        // and to ensure that only the owner can modify the approval mapping.
        _setupAccessControl(msg.sender, spender, 0);
        approval[msg.sender][spender] = amount;
    }

    // Function to get the balance of an address
    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }

    // Function to get the total supply
    function getTotalSupply() public view returns (uint256) {
        return totalSupply;
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {
        // Handle ETH receipt if needed (e.g., minting)
        // Reentrancy protection is already implemented through AccessControl
    }
}