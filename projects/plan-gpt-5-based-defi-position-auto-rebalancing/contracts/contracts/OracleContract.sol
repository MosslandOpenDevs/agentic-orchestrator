// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

contract OracleContract is Ownable, AccessControl {
    using EnumerableSet for EnumerableSet.AddressStorage;
    using Math for uint256;

    struct Prediction {
        float predictedValue;
        float confidenceInterval;
        datetime timestamp;
    }

    mapping(string => Prediction) public Predictions;
    mapping(string => bool) public PredictionExists;

    event PredictionGenerated(string tokenId, float predictedValue, float confidenceInterval, datetime timestamp);

    // GPT-5 API Key (Replace with your actual key)
    string public gpt5ApiKey;

    // Function to set the GPT-5 API key
    function setGPT5ApiKey(string memory _apiKey) public onlyOwner {
        gpt5ApiKey = _apiKey;
    }

    // Function to predict the value of an NFT
    function predictValue(string memory _tokenId) public returns (float, float) {
        require(PredictionExists[_tokenId], "Prediction does not exist");

        // Input Validation: Check if tokenId is valid (e.g., length)
        require(_tokenId.length > 0, "Token ID cannot be empty");

        // Simulate GPT-5 API call (Replace with actual API call)
        float predictedValue = simulateGPT5Prediction(_tokenId);

        // Calculate confidence interval (Example: 95% confidence)
        float confidenceInterval = predictedValue * 0.95;

        // Record the prediction
        Predictions[_tokenId] = Prediction({
            predictedValue: predictedValue,
            confidenceInterval: confidenceInterval,
            timestamp: block.timestamp
        });

        emit PredictionGenerated(_tokenId, predictedValue, confidenceInterval, block.timestamp);

        return (predictedValue, confidenceInterval);
    }

    // Simulate GPT-5 prediction - Replace with actual API call
    function simulateGPT5Prediction(string memory _tokenId) public returns (float) {
        // In a real implementation, this would call the GPT-5 API.
        // This is just a placeholder for demonstration purposes.
        // The actual API call would likely involve sending the tokenId
        // to the GPT-5 model and receiving a float value as the prediction.
        // This function should handle potential errors from the API call.
        if (_tokenId == "NFT123") {
            return 10.5;
        } else if (_tokenId == "NFT456") {
            return 25.2;
        } else {
            return 5.0;
        }
    }

    // Access control: Allow only the owner to call setGPT5ApiKey
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Access control: Allow only the owner to call setGPT5ApiKey
    function setGPT5ApiKey(string memory _apiKey) public onlyOwner {
        gpt5ApiKey = _apiKey;
    }
}