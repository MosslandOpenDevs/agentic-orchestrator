// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(address => string) public nftMetadata;
    event NFTMinted(address nftAddress, address owner);

    /**
     * @dev Mints a new Mossland NFT.
     * @param nftAddress The address of the newly minted NFT.
     */
    function mintNFT(string memory _nftAddress) public accessControl {
        require(bytes(_nftAddress).length > 0, "NFT address cannot be empty");
        nftMetadata[msg.sender] = _nftAddress;
        emit NFTMinted(_nftAddress, msg.sender);
    }

    /**
     * @dev Allows only the owner to change the NFT metadata.
     * @param nftAddress The address of the NFT.
     * @param _metadata The new metadata for the NFT.
     */
    function updateNFTMetadata(string memory _nftAddress) public accessControl {
        require(msg.sender == owner, "Only the owner can update metadata");
        nftMetadata[_nftAddress] = _nftAddress;
        emit NFTMinted(_nftAddress, msg.sender);
    }

    /**
     * @dev Returns the metadata for a given NFT address.
     * @param nftAddress The address of the NFT.
     * @return The metadata associated with the NFT address.
     */
    function getNFTMetadata(string memory _nftAddress) public view returns (string memory) {
        return nftMetadata[_nftAddress];
    }

    /**
     * @dev Fallback function to receive ETH.  Not used in this contract, but included for reentrancy protection.
     */
    receive() external payable {}
}