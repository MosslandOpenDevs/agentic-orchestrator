// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract NFTContract is Ownable, AccessControl {
    mapping(string => string) public domainNFTs;
    mapping(string => object) public nfts;
    EnumerableSet<string> public mintedNFTs;

    event NFTMinted(string tokenId, string domainId, object metadata);
    event NFTMetadataUpdated(string tokenId, object metadata);

    constructor() {
        AccessControl.grantRole(msg.sender, _adminRole);
    }

    modifier onlyAdmin() {
        require(hasRole(_adminRole, msg.sender), "Only admin can call this function");
        _;
    }

    function mintNFT(string memory _domainId, object memory _metadata) public onlyAdmin {
        require(bytes(_domainId).length > 0, "Domain ID cannot be empty");
        require(domainNFTs[_domainId] == "", "NFT already minted for this domain");
        require(_metadata.blockNumber == block.number, "Metadata block number mismatch");

        string memory tokenId = generateTokenId();
        nfts[tokenId] = _metadata;
        mintedNFTs.add(tokenId);
        domainNFTs[_domainId] = tokenId;

        emit NFTMinted(tokenId, _domainId, _metadata);
    }

    function updateNFTMetadata(string memory _tokenId, object memory _metadata) public onlyAdmin {
        require(bytes(_tokenId).length > 0, "Token ID cannot be empty");
        require(nfts[_tokenId] != "", "NFT does not exist");
        require(mintedNFTs.contains(_tokenId), "NFT not minted");
        require(_metadata.blockNumber == block.number, "Metadata block number mismatch");

        nfts[_tokenId] = _metadata;
        emit NFTMetadataUpdated(_tokenId, _metadata);
    }

    function generateTokenId() internal pure returns (string memory) {
        return string(abi.encodeHex(keccak256(block.timestamp, msg.sender)));
    }

    // Helper function to check if a role is granted to an address
    function hasRole(string memory _role, address _addr) public view returns (bool) {
        return (AccessControl.hasRole(_role, _addr));
    }

    // Admin role
    string private _adminRole = "Admin";
}