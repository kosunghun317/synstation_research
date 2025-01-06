// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

interface IStrategy {
    function totalAssets() external view returns (uint256 assets);

    function allocate(uint256 assets) external;
}
