// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "lib/solady/src/tokens/ERC4626.sol";
import {IStrategy} from "./interfaces/IStrategy.sol";

contract stGM is ERC4626 {
    struct strategyStruct {
        address strategyAddress;
        uint96 weight; // in bps
    }
    address internal GM;
    uint8 internal strategyCount;
    mapping(uint8 => strategyStruct) internal strategies;

    function name() public pure override returns (string memory) {
        return "staked GM";
    }

    function symbol() public pure override returns (string memory) {
        return "stGM";
    }

    function asset() public view override returns (address) {
        return GM;
    }

    function totalAssets() public view override returns (uint256 assets) {
        // assets in the vault.
        // mostly unallocated deposits plus accidental transfers.
        assets = SafeTransferLib.balanceOf(asset(), address(this));

        // query the assets in the strategy contracts.
        for (uint8 i = 0; i < strategyCount; i++) {
            assets += IStrategy(strategies[i].strategyAddress).totalAssets();
        }
    }

    function _afterDeposit(uint256 assets, uint256) internal override {
        // deposit the assets to the strategy contracts according to weights.
        for (uint8 i = 0; i < strategyCount; i++) {
            uint256 amount = (assets * strategies[i].weight) / 10000;
            if (amount != 0) {
                SafeTransferLib.safeApprove(
                    asset(),
                    strategies[i].strategyAddress,
                    amount
                );
                IStrategy(strategies[i].strategyAddress).allocate(amount);
            }
        }
    }
}
