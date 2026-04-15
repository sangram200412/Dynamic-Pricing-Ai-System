"""
ML Analyzer — KMeans clustering + Isolation Forest outlier removal.

Pipeline:
  1. Collect all normalized prices
  2. Isolation Forest → detect & remove outliers
  3. KMeans (k=3) → cluster into budget / mid / premium
  4. Compute market_min, market_avg, market_max
  5. Calculate recommended_price
  6. Determine pricing strategy
"""
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

from config import ML_CLUSTERS, ML_OUTLIER_CONTAMINATION

logger = logging.getLogger(__name__)


@dataclass
class PriceCluster:
    """A single price cluster."""
    label: str  # budget / mid / premium
    centroid: float
    min_price: float
    max_price: float
    count: int
    prices: list[float]


@dataclass
class MLAnalysis:
    """Full ML analysis result."""
    market_min: float = 0.0
    market_avg: float = 0.0
    market_max: float = 0.0
    market_median: float = 0.0
    recommended_price: float = 0.0
    strategy: str = "competitive"  # cheap / competitive / premium
    confidence: float = 0.0
    clusters: list[PriceCluster] = None
    outliers_removed: int = 0
    total_prices: int = 0
    clean_prices: int = 0
    price_std: float = 0.0

    def __post_init__(self):
        if self.clusters is None:
            self.clusters = []

    def to_dict(self) -> dict:
        return {
            "market_min": round(self.market_min, 2),
            "market_avg": round(self.market_avg, 2),
            "market_max": round(self.market_max, 2),
            "market_median": round(self.market_median, 2),
            "recommended_price": round(self.recommended_price, 2),
            "strategy": self.strategy,
            "confidence": round(self.confidence, 2),
            "outliers_removed": self.outliers_removed,
            "total_data_points": self.total_prices,
            "clean_data_points": self.clean_prices,
            "price_std": round(self.price_std, 2),
            "clusters": [
                {
                    "label": c.label,
                    "centroid": round(c.centroid, 2),
                    "min": round(c.min_price, 2),
                    "max": round(c.max_price, 2),
                    "count": c.count,
                }
                for c in self.clusters
            ],
        }


def _remove_outliers(prices: np.ndarray) -> tuple[np.ndarray, int]:
    """Use Isolation Forest to remove outliers."""
    if len(prices) < 5:
        # Not enough data for meaningful outlier detection
        return prices, 0

    iso = IsolationForest(
        contamination=ML_OUTLIER_CONTAMINATION,
        random_state=42,
        n_estimators=100,
    )
    reshaped = prices.reshape(-1, 1)
    labels = iso.fit_predict(reshaped)

    clean = prices[labels == 1]
    outliers_count = int(np.sum(labels == -1))

    if len(clean) < 3:
        # If too many removed, keep original
        logger.warning("Outlier removal too aggressive, keeping all prices")
        return prices, 0

    return clean, outliers_count


def _cluster_prices(prices: np.ndarray, n_clusters: int = ML_CLUSTERS) -> list[PriceCluster]:
    """KMeans clustering into budget / mid / premium."""
    actual_clusters = min(n_clusters, len(prices))
    if actual_clusters < 2:
        return [
            PriceCluster(
                label="mid",
                centroid=float(np.mean(prices)),
                min_price=float(np.min(prices)),
                max_price=float(np.max(prices)),
                count=len(prices),
                prices=prices.tolist(),
            )
        ]

    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    reshaped = prices.reshape(-1, 1)
    labels = kmeans.fit_predict(reshaped)

    clusters = []
    for i in range(actual_clusters):
        mask = labels == i
        cluster_prices = prices[mask]
        if len(cluster_prices) == 0:
            continue
        clusters.append(
            PriceCluster(
                label="",  # assigned after sorting
                centroid=float(kmeans.cluster_centers_[i][0]),
                min_price=float(np.min(cluster_prices)),
                max_price=float(np.max(cluster_prices)),
                count=int(np.sum(mask)),
                prices=cluster_prices.tolist(),
            )
        )

    # Sort by centroid and assign labels
    clusters.sort(key=lambda c: c.centroid)
    label_map = {0: "budget", 1: "mid", 2: "premium"}
    if len(clusters) == 2:
        label_map = {0: "budget", 1: "premium"}
    elif len(clusters) == 1:
        label_map = {0: "mid"}

    for idx, cluster in enumerate(clusters):
        cluster.label = label_map.get(idx, "mid")

    return clusters


def _determine_strategy(recommended: float, clusters: list[PriceCluster]) -> str:
    """Determine pricing strategy based on where recommended price falls."""
    if not clusters:
        return "competitive"

    if len(clusters) >= 3:
        budget_max = clusters[0].max_price
        premium_min = clusters[-1].min_price
        mid_centroid = clusters[1].centroid

        if recommended <= budget_max:
            return "cheap"
        elif recommended >= premium_min:
            return "premium"
        else:
            return "competitive"
    elif len(clusters) == 2:
        midpoint = (clusters[0].centroid + clusters[1].centroid) / 2
        if recommended < midpoint:
            return "cheap"
        else:
            return "premium"

    return "competitive"


def analyze_prices(all_prices: list[float]) -> MLAnalysis:
    """
    Full ML analysis pipeline.
    Input: list of cleaned prices (INR).
    Output: MLAnalysis with stats, clusters, and strategy.
    """
    if not all_prices:
        return MLAnalysis(strategy="no_data", confidence=0.0)

    prices_arr = np.array(all_prices, dtype=float)
    total = len(prices_arr)

    # Step 1: Remove outliers
    clean_prices, outliers_removed = _remove_outliers(prices_arr)
    clean_count = len(clean_prices)

    # Step 2: Basic stats
    market_min = float(np.min(clean_prices))
    market_max = float(np.max(clean_prices))
    market_avg = float(np.mean(clean_prices))
    market_median = float(np.median(clean_prices))
    price_std = float(np.std(clean_prices))

    # Step 3: Cluster
    clusters = _cluster_prices(clean_prices)

    # Step 4: Recommended price
    # Weighted: 40% median, 30% mid-cluster centroid, 30% average
    mid_cluster = next((c for c in clusters if c.label == "mid"), None)
    mid_centroid = mid_cluster.centroid if mid_cluster else market_avg

    recommended = (
        0.40 * market_median
        + 0.30 * mid_centroid
        + 0.30 * market_avg
    )

    # Step 5: Strategy
    strategy = _determine_strategy(recommended, clusters)

    # Step 6: Confidence (based on data quantity and consistency)
    consistency = 1.0 - min(price_std / market_avg, 1.0) if market_avg > 0 else 0
    data_factor = min(clean_count / 10, 1.0)
    confidence = round(consistency * 0.6 + data_factor * 0.4, 2)

    return MLAnalysis(
        market_min=market_min,
        market_avg=market_avg,
        market_max=market_max,
        market_median=market_median,
        recommended_price=recommended,
        strategy=strategy,
        confidence=confidence,
        clusters=clusters,
        outliers_removed=outliers_removed,
        total_prices=total,
        clean_prices=clean_count,
        price_std=price_std,
    )
