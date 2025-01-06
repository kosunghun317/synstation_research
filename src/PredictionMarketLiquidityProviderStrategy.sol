// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "lib/solady/src/utils/FixedPointMathLib.sol";
import "lib/solady/src/utils/SafeTransferLib.sol";
import "./interfaces/IStrategy.sol";

contract PredictionMarketLiquidityProviderStrategy is IStrategy {
    address internal asset;
    uint internal marketCount;
    mapping(uint => MarketInfoStruct) internal marketInfo;

    struct MarketInfoStruct {
        address[] markets; // array of GM <> i-th outcome pairs.
        DutchAuctionStruct dutchAuction;
    }

    struct DutchAuctionStruct {
        bool isOpen;
        uint32 InitiationTime;
        uint InitiationPrice;
    }

    function totalAssets() public view override returns (uint256 assets) {
        // assets in the strategy.

        // idle assets
        assets = SafeTransferLib.balanceOf(asset, address(this));

        // locked assets provided as liquidity to the prediction markets.
        for (uint i = 0; i < marketCount; i++) {
            // query the locked assets in each position.
            // LP position NFT will contain the relevant information.
        }
    }

    // callable only by the vault.
    function allocate(uint256 assets) public override {
        // pull the assets from the vault.
        SafeTransferLib.safeTransferFrom(
            asset,
            msg.sender,
            address(this),
            assets
        );
    }

    function initiateHarvestAuction(uint marketId) external {
        require(
            marketInfo[marketId].dutchAuction.isOpen == false,
            "Dutch auction is already open."
        );
        marketInfo[marketId].dutchAuction.InitiationTime = uint32(
            block.timestamp
        );
        uint valueInLP = 0;
        for (uint i = 0; i < marketInfo[marketId].markets.length; i++) {
            // calculate the value of the LP position.
            // LP position NFT will contain the relevant information.
            valueInLP += 1e18;
        }
        marketInfo[marketId].dutchAuction.InitiationPrice = valueInLP;
    }

    function bid(uint marketId) external {
        // calculate the bid amount of asset.
        // 24 hours linear decay from the initiation time.
        uint amount = (marketInfo[marketId].dutchAuction.InitiationPrice *
            (86400 +
                marketInfo[marketId].dutchAuction.InitiationTime -
                block.timestamp)) / 86400;

        // transfer the collected fees from the pairs of market to the caller.
        address[] storage markets = marketInfo[marketId].markets;
        for (uint i = 0; i < markets.length; i++) {
            // harvest the fees from the market.
            // transfer the fees to the caller.
        }

        // pull the bid amount of asset from the caller.
        SafeTransferLib.safeTransferFrom(
            asset,
            msg.sender,
            address(this),
            amount
        );

        // close the dutch auction.
        marketInfo[marketId].dutchAuction.isOpen = false;
    }
}
