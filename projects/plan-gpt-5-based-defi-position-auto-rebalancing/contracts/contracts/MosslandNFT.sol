// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract MosslandNFT is Ownable, AccessControl, ReentrancyGuard {
    mapping(string => uint256) public tokenIds;
    mapping(string => address) public owners;
    string public constant ADMIN_ROLE = "Admin";

    event NFTMinted(string tokenId, address ownerAddress);
    event NFTTransferred(address fromAddress, address toAddress, string tokenId);

    constructor() {
        AccessControl.grantRole(ADMIN_ROLE, msg.sender);
    }

    modifier onlyAdmin() {
        require(hasRole(ADMIN_ROLE, msg.sender), "Only admin can call this function");
        _;
    }

    function mintNFT(string memory _tokenId, address _ownerAddress) public onlyAdmin {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty");
        require(!isTokenExists(_tokenId), "Token ID already exists");

        tokenIds[_tokenId] = uint256(0); // Placeholder value, actual logic would assign a unique ID
        owners[_tokenId] = _ownerAddress;

        emit NFTMinted(_tokenId, _ownerAddress);
    }

    function transferNFT(address _fromAddress, address _toAddress, string memory _tokenId) public {
        require(_fromAddress != address(0), "From address cannot be zero");
        require(_toAddress != address(0), "To address cannot be zero");
        require(string.length(_tokenId) > 0, "Token ID cannot be empty");
        require(isTokenExists(_tokenId), "Token ID does not exist");
        require(owners[_tokenId] == _fromAddress, "Only owner can transfer");

        owners[_tokenId] = _toAddress;

        emit NFTTransferred(_fromAddress, _toAddress, _tokenId);
    }

    function isTokenExists(string memory _tokenId) public view returns (bool) {
        return tokenIds[_tokenId] > 0;
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {
        revert("This contract does not accept Ether");
    }
}