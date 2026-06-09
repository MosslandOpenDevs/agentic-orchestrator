import { ethers, Signer } from 'ethers';
import { expect } from 'chai';
import { Contract } from 'ethers';

// Mock contract interface
interface MockContract {
  deploy: () => Contract;
  connect: (signer: Signer) => void;
}

// Mock implementation for testing
class MockContractImpl implements MockContract {
  contract: Contract | null = null;

  deploy = (): Contract => {
    if (!this.contract) {
      this.contract = new ethers.Contract(
        '0x0000000000000000000000000000000