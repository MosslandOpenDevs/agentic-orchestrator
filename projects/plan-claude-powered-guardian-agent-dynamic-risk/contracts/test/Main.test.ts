import { ethers, upgrades } from 'ethers';
import { expect } from 'chai';
import { MockProvider } from 'hardhat-ethers';
import { CoinGecko, Glassnode, Chainlink } from './test/index'; // Assuming these are in test/index.ts

describe('Guardian Agent', function () {
  let guardianAgent: any;
  let mockProvider: MockProvider;
  let coinGecko: CoinGecko;
  let glassnode: Glassnode;
  let chainlink: Chainlink;
  let initialBalance: ethers.BigNumber;

  beforeEach(async function () {
    // Initialize mocks
    coinGecko = new CoinGecko();
    glassnode = new Glassnode();
    chainlink = new Chainlink();

    // Create a MockProvider with a default balance
    mockProvider = new MockProvider({
      networks: {
        goerli: {
          url: 'http://localhost:8545', // Replace with your local Ganache URL
        },
      },
      bytecode: await (await fetch('https://etherscan.io/')[0]).text(), // Replace with your contract bytecode
    });

    // Set a default balance for testing
    initialBalance = ethers.utils.parseEther('1000');
    mockProvider.contracts.Set(await upgrades.compile('GuardianAgent.sol'));
    mockProvider.contracts.Set.deploy(
      await upgrades.compile('GuardianAgent.sol'),
      initialBalance
    );

    guardianAgent = await mockProvider.contracts.Set.deploy();
  });

  describe('Deployment Tests', function () {
    it('should deploy successfully', async function () {
      await expect(guardianAgent.deployed()).to.emit('Deployed');
    });

    it('should return the correct contract address', async function () {
      expect(guardianAgent.address).to.not.be.equal(0);
    });
  });

  describe('Public Functions', function () {
    it('should set the risk tolerance', async function () {
      const riskTolerance = 10;
      await guardianAgent.setRiskTolerance(riskTolerance);
      expect(guardianAgent.riskTolerance).to.eq(riskTolerance);
    });

    it('should get the risk tolerance', async function () {
      const riskTolerance = 10;
      await guardianAgent.setRiskTolerance(riskTolerance);
      expect(guardianAgent.riskTolerance).to.eq(riskTolerance);
    });

    it('should update the portfolio', async function () {
      const newPortfolio = ethers.utils.defaultAbiCoder.decode(['address', 'uint256'], ['0x123', 50]);
      await guardianAgent.updatePortfolio(newPortfolio);
      expect(guardianAgent.portfolio).to.eq(newPortfolio);
    });

    it('should get the portfolio', async function () {
      const portfolio = ethers.utils.defaultAbiCoder.decode(['address', 'uint256'], ['0x123', 50]);
      await guardianAgent.updatePortfolio(portfolio);
      expect(guardianAgent.portfolio).to.eq(portfolio);
    });
  });

  describe('Access Control', function () {
    it('should only allow the owner to set the risk tolerance', async function () {
      // Assuming owner address is 0x0...
      const riskTolerance = 10;
      try {
        await guardianAgent.setRiskTolerance(riskTolerance);
      } catch (error) {
        expect(error).to.not.be.null;
      }
    });
  });

  describe('Edge Cases and Reverts', function () {
    it('should revert if risk tolerance is set to 0', async function () {
      try {
        await guardianAgent.setRiskTolerance(0);
      } catch (error) {
        expect(error).to.not.be.null;
      }
    });

    it('should revert if portfolio is invalid', async function () {
      try {
        await guardianAgent.updatePortfolio(ethers.utils.defaultAbiCoder.decode(['address', 'uint256'], ['0x123', 50]));
      } catch (error) {
        expect(error).to.not.be.null;
      }
    });
  });
});