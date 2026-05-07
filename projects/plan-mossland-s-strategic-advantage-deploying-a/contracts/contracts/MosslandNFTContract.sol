// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(string => address) public NFTs;
    mapping(string => uint256) public tokenIdToId;
    EnumerableSet.ControlledMapping<string, address> public ownedNFTs;

    event NFTMinted(string tokenId, address owner, uint256 metadataSize);
    event NFTTransferred(string tokenId, address from, address to);

    constructor() {
        AccessControl.grantRole(msg.sender, _ADMIN_ROLE);
    }

    modifier onlyAdmin() {
        require(msg.sender == _ADMIN_ROLE, "Only admin can call this function.");
        _;
    }

    function mintNFT(string memory _tokenId, address _owner, uint256 _metadataSize) public onlyAdmin {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty.");
        require(_metadataSize > 0, "Metadata size must be greater than 0.");

        NFTs[_tokenId] = _owner;
        tokenIdToId[_tokenId] = _metadataSize;
        ownedNFTs.add(_tokenId);

        emit NFTMinted(_tokenId, _owner, _metadataSize);
    }

    function transferNFT(string memory _tokenId, address _recipient) public onlyAdmin {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty.");
        require(NFTs[_tokenId] != address(0), "Token does not exist.");
        require(ownedNFTs.contains(_tokenId), "Token is not owned by the caller.");

        NFTs[_tokenId] = _recipient;
        ownedNFTs.remove(_tokenId);
        ownedNFTs.add(_tokenId);

        emit NFTTransferred(_tokenId, NFTs[_tokenId], _recipient);
    }

    function getNFTOwner(string memory _tokenId) public view returns (address) {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty.");
        return NFTs[_tokenId];
    }

    function getTokenIdSize(string memory _tokenId) public view returns (uint256) {
        require(string.length(_tokenId) > 0, "Token ID cannot be empty.");
        return tokenIdToId[_tokenId];
    }

    // Fallback function to prevent accidental Ether transfers
    receive() external payable {}
}