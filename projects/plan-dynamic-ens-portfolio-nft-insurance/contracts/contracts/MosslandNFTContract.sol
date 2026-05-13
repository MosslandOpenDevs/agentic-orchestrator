// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(string => uint256) public tokenPrices;
    uint256 public tokenSupply;
    string public baseTokenId;

    event NFTMinted(address owner, string tokenId);
    event NFTTransferred(address owner, address newOwner, string tokenId);

    constructor(string memory _baseTokenId) {
        tokenSupply = 100;
        baseTokenId = _baseTokenId;
    }

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function.");
        _;
    }

    function mintNFT(string memory _name, string memory _symbol, address _owner) public onlyOwner {
        require(tokenSupply > 0, "Token supply is exhausted.");
        require(bytes(_name).length > 0, "Name cannot be empty.");
        require(bytes(_symbol).length > 0, "Symbol cannot be empty.");

        string memory tokenId = bytes(baseTokenId) + uint256ToBytes(tokenSupply);
        tokenSupply--;
        tokenPrices[tokenId] = 1000000000000000000; // Default price
        emit NFTMinted(_owner, tokenId);
    }

    function transferNFT(address _from, address _to, string memory _tokenId) public {
        require(tokenPrices[_tokenId] > 0, "Token not owned or not for sale.");
        require(_to != _from, "Cannot transfer to yourself.");

        // Reentrancy protection
        require(!isLocked, "Reentrancy blocked.");
        _lock();

        // Transfer ownership
        _transfer(_from, _to, _tokenId);

        // Unlock
        _unlock();
    }

    function _transfer(address _from, address _to, string memory _tokenId) internal {
        // Prevent reentrancy
        require(!isLocked, "Reentrancy blocked.");
        _lock();

        // Transfer ownership
        _safeTransfer(_from, _to, _tokenId);

        // Unlock
        _unlock();
    }

    function _safeTransfer(address _from, address _to, string memory _tokenId) internal {
        _safeTransferAt(
            _from,
            _to,
            uint256(_tokenId.length()),
            keccak256(abi.encode(_tokenId))
        );
    }

    function _safeTransferAt(address _from, address _to, uint256 _tokenId, uint256 _offset) internal {
        // Prevent reentrancy
        require(!isLocked, "Reentrancy blocked.");
        _lock();

        // Transfer ownership
        _transferAt(_from, _to, _tokenId, _offset);

        // Unlock
        _unlock();
    }

    function _transferAt(address _from, address _to, uint256 _tokenId, uint256 _offset) internal {
        // Prevent reentrancy
        require(!isLocked, "Reentrancy blocked.");
        _lock();

        // Transfer ownership
        _transferAtHelper(_from, _to, _tokenId, _offset);

        // Unlock
        _unlock();
    }

    function _transferAtHelper(address _from, address _to, uint256 _tokenId, uint256 _offset) internal {
        // Prevent reentrancy
        require(!isLocked, "Reentrancy blocked.");
        _lock();

        // Transfer ownership
        _safeTransfer(_from, _to, _tokenId, _offset);

        // Unlock
        _unlock();
    }

    function owner() public view returns (address) {
        return owner();
    }

    // Helper functions for gas optimization
    function uint256ToBytes(uint256 _num) internal pure returns (bytes memory) {
        bytes memory buffer;
        buffer = new bytes(_num.length() + 1);
        for (uint256 i = 0; i < _num.length(); i++) {
            buffer[i] = (uint8(_num >> (i * 8))) & 0xFF;
        }
        return buffer;
    }

    bool public isLocked = false;

    function _lock() internal {
        isLocked = true;
    }

    function _unlock() internal {
        isLocked = false;
    }
}