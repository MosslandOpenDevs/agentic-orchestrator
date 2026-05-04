// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract AgentReceiptContract is Ownable, AccessControl, ReentrancyGuard {
    using SafeTransferableERC721 for IERC721;

    struct AgentReceipt {
        string tokenId;
        string asset;
        uint256 quantity;
        string verifier;
        uint256 timestamp;
        address owner;
    }

    mapping(string => AgentReceipt) public receipts;
    mapping(string => bool) public receiptStatus; // Track if receipt is verified
    mapping(string => uint256) public receiptTimestamps; // Store timestamps for efficient retrieval

    event ReceiptCreated(
        string receiptId,
        string tokenId,
        string asset,
        uint256 quantity,
        uint256 timestamp,
        string verifier,
        address owner
    );

    event ReceiptVerified(string receiptId, string asset, uint256 quantity);

    error InvalidInput(string message);

    constructor() {
        AccessControl.grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    modifier onlyAdmin() {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Only admin can call this function");
        _;
    }

    function createReceipt(
        string memory _tokenId,
        string memory _asset,
        uint256 _quantity,
        string memory _verifier
    ) public onlyAdmin {
        require(_tokenId.length > 0, "Token ID cannot be empty");
        require(_asset.length > 0, "Asset cannot be empty");
        require(_quantity > 0, "Quantity must be greater than 0");
        require(_verifier.length > 0, "Verifier cannot be empty");

        string memory receiptId = generateReceiptId(_tokenId);

        AgentReceipt storage receipt = receipts[receiptId];
        receipt.tokenId = _tokenId;
        receipt.asset = _asset;
        receipt.quantity = _quantity;
        receipt.verifier = _verifier;
        receipt.timestamp = block.timestamp;
        receipt.owner = msg.sender;
        receiptStatus[receiptId] = false; // Initially not verified
        receiptTimestamps[receiptId] = block.timestamp;

        emit ReceiptCreated(
            receiptId,
            _tokenId,
            _asset,
            _quantity,
            block.timestamp,
            _verifier,
            msg.sender
        );
    }

    function verifyReceipt(string memory _receiptId, string memory _asset, uint256 _quantity) public onlyAdmin {
        require(receipts[_receiptId].asset == _asset, "Asset mismatch");
        require(receipts[_receiptId].quantity == _quantity, "Quantity mismatch");
        require(!receiptStatus[_receiptId], "Receipt already verified");

        receipts[_receiptId].timestamp = block.timestamp;
        receiptStatus[_receiptId] = true;

        emit ReceiptVerified(_receiptId, _asset, _quantity);
    }

    // Helper function to generate a unique receipt ID
    function generateReceiptId(string memory _tokenId) public pure returns (string memory) {
        return string(abi.encodePacked(_tokenId, block.timestamp));
    }

    // Fallback function to prevent accidental ETH transfers
    receive() external payable {
        revert("This contract does not accept ETH");
    }
}