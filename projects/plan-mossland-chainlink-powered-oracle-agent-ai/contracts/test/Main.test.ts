import { ethers, upgrades } from 'ethers';
import {
  SafeFactory,
  SafeFactoryInterface,
  Token,
  TokenInterface,
} from '../typechain';
import { constants } from 'ethers';

import { HardhatError } from 'hardhat';

contract('MosslandOracleAgent', function (this: any) {
  let mosslandOracleAgent: SafeFactory;
  let token: Token;
  const INITIAL_PRICE = 100;

  beforeEach(async function () {
    // Deploy contracts
    mosslandOracleAgent = await upgrades.deploy('MosslandOracleAgent');
    await upgrades.unwrapUpgrade(mosslandOracleAgent);
    await mosslandOracleAgent.waitFor();

    // Deploy token
    token = await Token.connect(this.ethers.provider, mosslandOracleAgent.address);
    await token.waitFor();
  });

  describe('Deployment Tests', function () {
    it('should deploy contract successfully', async function () {
      const deployedAddress = await mosslandOracleAgent.getAddress();
      assert.notEqual(deployedAddress, constants.zeroAddress, 'Contract failed to deploy');
    });

    it('should return correct contract name', async function () {
      const contractName = await mosslandOracleAgent.getContractName();
      assert.strictEqual(contractName, 'MosslandOracleAgent', 'Incorrect contract name');
    });
  });

  describe('Public Functions', function () {
    it('should set initial asset price', async function () {
      const initialPrice = 100;
      const result = await mosslandOracleAgent.setInitialAssetPrice(initialPrice);
      assert.notEqual(result.value, 0, 'Price setting failed');
    });

    it('should update asset price', async function () {
      const newPrice = 200;
      const result = await mosslandOracleAgent.setAssetPrice(newPrice);
      assert.notEqual(result.value, 0, 'Price update failed');
    });

    it('should get current asset price', async function () {
      const currentPrice = await mosslandOracleAgent.getCurrentAssetPrice();
      assert.strictEqual(currentPrice, 100, 'Incorrect current price');
    });
  });

  describe('Access Control', function () {
    it('should only allow owner to set initial price', async function () {
      // This test requires mocking the provider to simulate owner access.
      // In a real environment, you'd use a private key.
      const ownerAddress = '0xAb5801a7D890769444435f37439854744274c62f';
      await mosslandOracleAgent.connect(ownerAddress).setInitialAssetPrice(50);
    });
  });

  describe('Edge Cases and Reverts', function () {
    it('should revert if setting price to zero', async function () {
      try {
        await mosslandOracleAgent.setAssetPrice(0);
        assert.fail('Expected revert, but none occurred');
      } catch (error) {
        assert.strictEqual(error instanceof HardhatError, true, 'Incorrect error type');
      }
    });

    it('should revert if setting price to negative value', async function () {
      try {
        await mosslandOracleAgent.setAssetPrice(-100);
        assert.fail('Expected revert, but none occurred');
      } catch (error) {
        assert.strictEqual(error instanceof HardhatError, true, 'Incorrect error type');
      }
    });
  });
});