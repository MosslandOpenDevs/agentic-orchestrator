// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract NFTOwnershipContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(string => uint256) public tokenIds;
    mapping(string => address) public ownerAddresses;

    event NFTMinted(string tokenId, address owner);
    event NFTTransferred(string tokenId, address from, address to);

    constructor() {
        ownerAddresses[msg.sender] = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == ownerAddresses[msg.sender], "Only owner can call this function");
        _;
    }

    function mintNFT(string memory _tokenId) public {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty");
        require(!tokenIds.containsKey(_tokenId), "Token ID already exists");
        tokenIds[_tokenId] = uint256(0); // Placeholder value, can be updated with metadata
        emit NFTMinted(_tokenId, msg.sender);
    }

    function transferNFT(string memory _tokenId, address _from, address _to) public {
        require(tokenIds.containsKey(_tokenId), "Token ID does not exist");
        require(_from != _to, "Cannot transfer to yourself");
        require(ownerAddresses[msg.sender] == _from, "Only owner can transfer this NFT");

        tokenIds[_tokenId] = 0; // Placeholder value, can be updated with metadata
        emit NFTTransferred(_tokenId, _from, _to);
    }

    function safeTransferNFT(string memory _tokenId, address _from, address _to) public {
        transferNFT(_tokenId, _from, _to);
    }

    function ownerTransferNFT(string memory _tokenId, address _from, address _to) public {
        onlyOwner();
        transferNFT(_tokenId, _from, _to);
    }

    // Access Control functions (Inherited from AccessControl)
    function grantRole(bytes32 _role, address _target) external onlyOwner {
        _grantRole(_target, _role);
    }

    function revokeRole(bytes32 _role, address _target) external onlyOwner {
        _revokeRole(_target, _role);
    }

    function getRoleForAddress(address _owner) public view returns (bytes32) {
        return _getRoleForAddress(_owner);
    }
}