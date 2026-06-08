import { ethers, Signer } from 'ethers';
import { expect } from 'chai';
import { Contract } from 'ethers';
import { MockProvider } from 'hardhat/providers/mockprovider';

// Replace with your contract's ABI and address
const CONTRACT_ABI = [...];
const CONTRACT_ADDRESS = '0x';

describe('Mossland Portfolio Agent', () => {
  let provider: MockProvider;
  let wallet: Signer;
  let contract: Contract;

  beforeAll(async () => {
    provider = new MockProvider({
      networks: {
        goerli: {
          blockGasLimit: 200000,
          bytecode: '',
          gasAccounting: true,
          feeLimit: 5000000000,
          forkBlock: '0x0',
          gasOptimizer: true,
          links: [],
          name: 'Goerli',
          networkId: 5,
          unpaddedSignature: '',
          wallets: {
            deployer: {
              address: '0x0000000000000000000000000000000