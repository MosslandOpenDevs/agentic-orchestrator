// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(uint256 => {
        string name;
        string symbol;
        uint8 decimals;
    }) public nftMetadata;
    mapping(address => uint256) public owners;

    event NFTMinted(address owner, uint256 tokenId, string metadata);

    /**
     * @dev Mint a new NFT.
     * @param _name The name of the NFT.
     * @param _symbol The symbol of the NFT.
     * @param _metadata The metadata of the NFT.
     */
    function mintNFT(string memory _name, string memory _symbol, string memory _metadata) public accessControl {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_symbol).length > 0, "Symbol cannot be empty");
        require(bytes(_metadata).length > 0, "Metadata cannot be empty");

        uint256 tokenId = uint256(nftMetadata.length + 1);
        nftMetadata[tokenId] = ({
            name: _name,
            symbol: _symbol,
            decimals: 18 // Default decimals
        });
        owners[msg.sender] = tokenId;
        emit NFTMinted(msg.sender, tokenId, _metadata);
    }

    /**
     * @dev Get the owner of a given NFT address.
     * @param _tokenId The ID of the NFT.
     * @return The address of the owner.
     */
    function ownerOf(uint256 _tokenId) public view returns (address) {
        require(_tokenId > 0, "Token ID must be greater than 0");
        require(nftMetadata[_tokenId].name.length > 0, "NFT metadata must exist");
        return owners[_tokenId];
    }

    /**
     * @dev Transfer ownership of an NFT to a new owner.
     * @param _tokenId The ID of the NFT.
     * @param _newOwner The address of the new owner.
     */
    function transferOwnership(uint256 _tokenId, address _newOwner) public accessControl {
        require(_tokenId > 0, "Token ID must be greater than 0");
        require(nftMetadata[_tokenId].name.length > 0, "NFT metadata must exist");
        require(_newOwner != address(0), "New owner cannot be the zero address");

        owners[_tokenId] = _newOwner;
        emit NFTMinted(_newOwner, _tokenId, nftMetadata[_tokenId].name);
    }

    /**
     * @dev Get the metadata of a given NFT.
     * @param _tokenId The ID of the NFT.
     * @return The metadata of the NFT.
     */
    function getNFTMetadata(uint256 _tokenId) public view returns (string memory) {
        require(_tokenId > 0, "Token ID must be greater than 0");
        require(nftMetadata[_tokenId].name.length > 0, "NFT metadata must exist");
        return nftMetadata[_tokenId].name;
    }
}