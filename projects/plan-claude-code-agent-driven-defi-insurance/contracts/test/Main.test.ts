import { ethers, Signer } from 'ethers';
import { expect } from 'chai';
import { constants } from 'ethers';
import { deploy, deployAndSign, testContract } from '../test-setup';
import {
  ClaudeAgentProtocol,
  RiskAssessment,
  PortfolioManager,
  AaveProtocol,
} from '../src/contracts';
import {
  DEFAULT_ADDRESS,
  DEFAULT_PRIVATE_KEY,
  DEPLOY_RPC_URL,
} from '../test-config';

describe('Claude Agent-Driven DeFi Insurance Protocol', () => {
  let aave: AaveProtocol;
  let portfolioManager: PortfolioManager;
  let claudeAgentProtocol: ClaudeAgentProtocol;
  let riskAssessment: RiskAssessment;
  let deployer: Signer;
  let user: Signer;

  before(async () => {
    // Deploy contracts
    aave = await deployAndSign<AaveProtocol>(AaveProtocol, [
      constants.AddressZero,
      constants.AddressZero,
    ]);

    portfolioManager = await deployAndSign<PortfolioManager>(
      PortfolioManager,
      [aave.address, riskAssessment.address]
    );

    claudeAgentProtocol = await deployAndSign<ClaudeAgentProtocol>(
      ClaudeAgentProtocol,
      [portfolioManager.address]
    );

    riskAssessment = await deployAndSign<RiskAssessment>(RiskAssessment);

    // Deploy deployer and user accounts
    deployer = await ethers.getSigner(DEFAULT_ADDRESS);
    user = await ethers.getSigner(DEFAULT_ADDRESS);
  });

  describe('Aave Protocol', () => {
    it('should allow deposit and withdraw', async () => {
      const amount = ethers.parseEther('1');
      await aave.deposit(amount, user.address);
      expect(aave.balanceOf(user.address)).to.eq(amount);

      await aave.withdraw(amount, user.address);
      expect(aave.balanceOf(user.address)).to.eq(constants.AddressZero);
    });

    it('should revert if insufficient balance', async () => {
      await aave.deposit(ethers.parseEther('0.1'), user.address);
      await expect(aave.withdraw(ethers.parseEther('1'), user.address)).to.be.reverted();
    });
  });

  describe('Portfolio Manager', () => {
    it('should allow user to set risk parameters', async () => {
      const riskLevel = 1;
      await portfolioManager.setRiskLevel(riskLevel, user.address);
      expect(portfolioManager.riskLevel(user.address)).to.eq(riskLevel);
    });

    it('should allow user to update DeFi protocol', async () => {
      const newProtocol = aave.address;
      await portfolioManager.setProtocol(newProtocol, user.address);
      expect(portfolioManager.protocol(user.address)).to.eq(newProtocol);
    });
  });

  describe('Risk Assessment', () => {
    it('should calculate risk score based on volatility', async () => {
      // Mock volatility data for testing
      const volatility = 0.1;
      await riskAssessment.setVolatility(volatility);
      expect(riskAssessment.calculateRiskScore()).to.eq(volatility);
    });
  });

  describe('Claude Agent Protocol', () => {
    it('should allow agent to analyze protocol data', async () => {
      // Mock data for testing
      const protocolData = {
        apy: 5,
        volatility: 0.2,
      };
      await claudeAgentProtocol.setProtocolData(protocolData, user.address);
      expect(claudeAgentProtocol.protocolData(user.address)).to.eq(protocolData);
    });
  });

  describe('Portfolio Management Actions', () => {
    it('should execute a deposit transaction', async () => {
      const amount = ethers.parseEther('0.5');
      const result = await portfolioManager.executeDeposit(amount, user.address);
      expect(result.status).to.eq(true);
    });

    it('should execute a withdrawal transaction', async () => {
      const amount = ethers.parseEther('0.25');
      const result = await portfolioManager.executeWithdraw(amount, user.address);
      expect(result.status).to.eq(true);
    });
  });

  describe('Access Control', () => {
    it('should only allow deployer to set risk level', async () => {
      await expect(portfolioManager.setRiskLevel(2, user.address)).to.be.reverted();
    });
  });

  describe('Edge Cases and Reverts', () => {
    it('should revert if risk level is set to zero', async () => {
      await expect(portfolioManager.setRiskLevel(0, user.address)).to.be.reverted();
    });

    it('should revert if protocol address is invalid', async () => {
      await expect(portfolioManager.setProtocol(constants.AddressZero, user.address)).to.be.reverted();
    });
  });
});