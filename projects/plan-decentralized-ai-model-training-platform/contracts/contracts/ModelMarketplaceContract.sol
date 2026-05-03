// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract ModelMarketplaceContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(address => object) public models;
    mapping(address => address) public owners;

    event ModelDeployed(address modelId, address owner);
    event ModelPurchased(address modelId, address buyer, uint256 amount);

    constructor() {
        _setupAccessControl();
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Deploys a new model to the marketplace.
    function deployModel(string memory modelId, address owner) public {
        require(modelId.length > 0, "Model ID cannot be empty");
        require(owner != address(0), "Owner address cannot be zero");

        models[modelId] = {
            "name": "New Model",
            "version": "1.0",
            "description": "A new model for the marketplace"
        };
        owners[owner] = modelId;

        emit ModelDeployed(modelId, owner);
    }

    // Allows a user to purchase access to a model.
    function purchaseModel(string memory modelId, uint256 amount) public payable {
        require(modelId.length > 0, "Model ID cannot be empty");
        require(amount > 0, "Amount must be greater than zero");

        // Check if the model exists
        if (!models[modelId].isValid) {
            revert("Model does not exist");
        }

        // Transfer ETH to the owner
        payable(owners[modelId]).transfer(amount);

        emit ModelPurchased(modelId, msg.sender, amount);
    }

    // Updates the metadata of a deployed model
    function updateModelMetadata(string memory modelId, string memory metadata) public onlyOwner {
        require(modelId.length > 0, "Model ID cannot be empty");

        if (!models[modelId].isValid) {
            revert("Model does not exist");
        }

        models[modelId] = {
            "name": "Updated Model Name",
            "version": "2.0",
            "description": metadata,
            "metadata": metadata
        };
    }

    // Fallback function to receive ETH
    receive() external payable {}
}