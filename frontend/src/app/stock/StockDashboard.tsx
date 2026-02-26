"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  AssetOut,
  PriceOut,
  StatsResponse,
  ForecastMetricsResponse,
} from "@/types/api";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Loader2, BarChart3 } from "lucide-react";
import { StockChart, type ChartModel } from "./StockChart";

const METRICS_MODEL_ORDER: ChartModel[] = ["base", "prophet", "lstm", "chronos2", "prophet_xgb"];

interface StockDashboardProps {
  assets: AssetOut[];
  initialSymbol?: string;
  initialPrices?: PriceOut[] | null;
  initialStats?: StatsResponse | null;
  initialFromDate?: string;
  initialToDate?: string;
}

export function StockDashboard({ assets, initialSymbol, initialPrices, initialStats, initialFromDate, initialToDate }: StockDashboardProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [syncSymbol, setSyncSymbol] = useState("");
  const [isSyncing, setIsSyncing] = useState(false);

  const [fromDate, setFromDate] = useState(initialFromDate || "");
  const [toDate, setToDate] = useState(initialToDate || "");
  const [metrics, setMetrics] = useState<ForecastMetricsResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [inProgressModels, setInProgressModels] = useState<ChartModel[]>([]);
  const [chartInterval, setChartInterval] = useState<"1wk" | "1mo">("1wk");
  const [chartHorizon, setChartHorizon] = useState<1 | 2 | 3 | 4>(4);
  const [chartModel, setChartModel] = useState<ChartModel>("base");
  const [compareAll, setCompareAll] = useState(false);

  const handleSelect = (symbol: string) => {
    setMetrics(null);
    router.push(`/stock?symbol=${symbol}&from=${fromDate}&to=${toDate}`);
  };

  const handleDateUpdate = () => {
    if (initialSymbol) {
      router.push(`/stock?symbol=${initialSymbol}&from=${fromDate}&to=${toDate}`);
    }
  };

  const handleSync = async () => {
    if (!syncSymbol) return;
    setIsSyncing(true);
    try {
      await api.syncAsset(syncSymbol);
      toast({ title: "Sync Successful", description: `${syncSymbol} has been synced.` });
      router.push(`/stock?symbol=${syncSymbol.toUpperCase()}&from=${fromDate}&to=${toDate}`);
      router.refresh();
      setSyncSymbol("");
    } catch (error: any) {
      toast({ title: "Sync Failed", description: error.message, variant: "destructive" });
    } finally {
      setIsSyncing(false);
    }
  };

  const stats = initialSymbol && initialStats?.individual?.[initialSymbol.toUpperCase()];

  const handleLoadMetrics = async () => {
    if (!initialSymbol) return;
    const symbol = initialSymbol.toUpperCase();
    const reqBase = {
      symbol,
      interval: chartInterval,
      last_n_weeks: 20,
      bounds_horizon_periods: chartHorizon,
    };

    if (!compareAll) {
      setMetricsLoading(true);
      setInProgressModels([chartModel]);
      setMetrics({
        symbol,
        interval: chartInterval,
        last_n_weeks: 20,
        bounds_horizon_weeks: chartHorizon,
        metrics: [],
        bounds: [],
        error: null,
      });
      try {
        const res = await api.getForecastMetrics({
          ...reqBase,
          models: [chartModel],
        });
        setMetrics(res);
        setInProgressModels([]);
        toast({
          title: "Metrics loaded",
          description: `${chartModel} — walk-forward and bounds.`,
        });
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load metrics";
        toast({ title: "Metrics failed", description: msg, variant: "destructive" });
        setInProgressModels([]);
      } finally {
        setMetricsLoading(false);
      }
      return;
    }

    setMetricsLoading(true);
    setInProgressModels([...METRICS_MODEL_ORDER]);
    setMetrics({
      symbol,
      interval: chartInterval,
      last_n_weeks: 20,
      bounds_horizon_weeks: chartHorizon,
      metrics: [],
      bounds: [],
      error: null,
    });

    METRICS_MODEL_ORDER.forEach((modelKey) => {
      api
        .getForecastMetrics({ ...reqBase, models: [modelKey] })
        .then((res) => {
          setMetrics((prev) =>
            prev
              ? {
                  ...prev,
                  metrics: [...prev.metrics, ...res.metrics],
                  bounds: [...prev.bounds, ...res.bounds],
                }
              : prev
          );
          setInProgressModels((prev) => {
            const next = prev.filter((m) => m !== modelKey);
            if (next.length === 0) setMetricsLoading(false);
            return next;
          });
        })
        .catch(() => {
          setInProgressModels((prev) => {
            const next = prev.filter((m) => m !== modelKey);
            if (next.length === 0) setMetricsLoading(false);
            return next;
          });
        });
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center bg-muted/50 p-4 rounded-lg border">
        <div className="flex items-center gap-4 w-full md:w-auto overflow-visible">
          <span className="font-medium whitespace-nowrap">Select Stock:</span>
          <Select
            value={initialSymbol ?? ""}
            onValueChange={(v) => v && v !== "__empty__" && handleSelect(v)}
          >
            <SelectTrigger className="w-[200px] bg-background">
              <SelectValue placeholder="Choose a stock..." />
            </SelectTrigger>
            <SelectContent className="z-[100]" position="popper">
              {assets.length === 0 ? (
                <SelectItem value="__empty__" disabled className="text-muted-foreground">
                  No stocks synced — add one below
                </SelectItem>
              ) : (
                assets.map((a) => (
                  <SelectItem key={a.symbol} value={a.symbol}>
                    {a.symbol} - {a.name || "Unknown"}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span className="font-medium whitespace-nowrap">Fetch New:</span>
          <Input
            placeholder="Ticker (e.g. TSLA)"
            value={syncSymbol}
            onChange={(e) => setSyncSymbol(e.target.value.toUpperCase())}
            className="w-[150px] bg-background"
          />
          <Button onClick={handleSync} disabled={isSyncing || !syncSymbol}>
            {isSyncing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sync
          </Button>
        </div>
      </div>

      {!initialSymbol && (
        <div className="text-center py-20 text-muted-foreground">
          Please select a stock from the dropdown or fetch a new one to view its details.
        </div>
      )}

      {initialSymbol && initialPrices && initialPrices.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>{initialSymbol.toUpperCase()} Price History & Forecast</CardTitle>
              </CardHeader>
              <CardContent>
                <StockChart
                symbol={initialSymbol.toUpperCase()}
                initialPrices={initialPrices}
                interval={chartInterval}
                horizonWeeks={chartHorizon}
                model={chartModel}
                compareAll={compareAll}
                onChartOptionsChange={(i, h, m, comp) => {
                  setChartInterval(i);
                  setChartHorizon(h);
                  if (m !== undefined) setChartModel(m);
                  if (comp !== undefined) setCompareAll(comp);
                }}
              />
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader className="pb-4">
                <CardTitle>Portfolio Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-3 mb-6">
                  <div className="flex items-center gap-2">
                    <Input 
                      type="date" 
                      value={fromDate} 
                      onChange={(e) => setFromDate(e.target.value)} 
                      className="h-8 text-xs"
                    />
                    <span className="text-muted-foreground text-xs">to</span>
                    <Input 
                      type="date" 
                      value={toDate} 
                      onChange={(e) => setToDate(e.target.value)} 
                      className="h-8 text-xs"
                    />
                  </div>
                  <Button size="sm" variant="secondary" onClick={handleDateUpdate} className="w-full">
                    Update Range
                  </Button>
                </div>
                {stats ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Avg Return</span>
                      <span className="font-medium">{(stats.avg_return * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Variance</span>
                      <span className="font-medium">{stats.variance?.toFixed(6)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Std Deviation</span>
                      <span className="font-medium">{(stats.std_deviation * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Cumulative Return</span>
                      <span className={`font-medium ${stats.cumulative_return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {(stats.cumulative_return * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Ann. Volatility</span>
                      <span className="font-medium">{(stats.annualized_volatility * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Sharpe Ratio</span>
                      <span className="font-medium">{stats.sharpe_score?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Max Drawdown</span>
                      <span className="font-medium text-red-500">{(stats.max_drawdown * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Skewness</span>
                      <span className="font-medium">{stats.skewness?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Kurtosis</span>
                      <span className="font-medium">{stats.kurtosis?.toFixed(2)}</span>
                    </div>
                    
                    <div className="pt-3 mt-3 border-t">
                      <div className="font-medium mb-3 text-muted-foreground">Returns Summary</div>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Min</span>
                          <span className="font-medium text-red-500">{(stats.returns_summary?.min * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Max</span>
                          <span className="font-medium text-green-500">{(stats.returns_summary?.max * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Mean</span>
                          <span className="font-medium">{(stats.returns_summary?.mean * 100).toFixed(2)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-muted-foreground text-sm">
                    Stats not available. The asset might not have enough historical data (minimum 52 weeks required).
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {initialSymbol && initialPrices && initialPrices.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle>Error Metrics Comparison</CardTitle>
              <Button
                size="sm"
                variant="secondary"
                onClick={handleLoadMetrics}
                disabled={metricsLoading}
              >
                {metricsLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {compareAll ? "Loading… (each model as it finishes)" : "Loading…"}
                  </>
                ) : (
                  <>
                    <BarChart3 className="mr-2 h-4 w-4" />
                    Load metrics
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">
                Walk-forward 1-step backtest over the last 20 weeks. Lower values indicate better accuracy.
                {compareAll
                  ? " Compare all: each model loads as it finishes."
                  : ` Single model (${chartModel}): one request.`}
              </p>
              {metrics?.error && (
                <p className="text-sm text-amber-600 dark:text-amber-400">{metrics.error}</p>
              )}
              {metrics && !metrics.error && metrics.metrics.length === 0 && inProgressModels.length === 0 && (
                <p className="text-sm text-muted-foreground">No metrics computed (models may have failed).</p>
              )}
              {(metrics?.metrics.length ?? 0) > 0 || inProgressModels.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 font-medium">Model</th>
                        <th className="text-right py-2 font-medium">MAE</th>
                        <th className="text-right py-2 font-medium">RMSE</th>
                        <th className="text-right py-2 font-medium">MAPE %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(compareAll
                          ? METRICS_MODEL_ORDER
                          : inProgressModels.length > 0
                            ? inProgressModels
                            : (metrics?.metrics ?? []).map((r) => r.model)
                      ).map((modelKey) => {
                        const row = metrics?.metrics.find((r) => r.model === modelKey);
                        const loading = inProgressModels.includes(modelKey as ChartModel);
                        return (
                          <tr key={modelKey} className="border-b border-border/50">
                            <td className="py-2 capitalize">{modelKey}</td>
                            {loading ? (
                              <>
                                <td className="text-right py-2" colSpan={3}>
                                  <span className="inline-flex items-center gap-1.5 text-muted-foreground">
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    Loading…
                                  </span>
                                </td>
                              </>
                            ) : row ? (
                              <>
                                <td className="text-right py-2">{row.mae.toFixed(2)}</td>
                                <td className="text-right py-2">{row.rmse.toFixed(2)}</td>
                                <td className="text-right py-2">{row.mape.toFixed(2)}%</td>
                              </>
                            ) : null}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>
                Forecast Bounds (
                {metrics
                  ? `${metrics.bounds_horizon_weeks}-${metrics.interval === "1mo" ? "Month" : "Week"} Horizon`
                  : `${chartHorizon}-${chartInterval === "1mo" ? "Month" : "Week"} Horizon`}
                )
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">
                Lowest expected price, highest expected price, and average forecast per model over the selected horizon.
              </p>
              {metrics && metrics.bounds.length === 0 && !metrics.error && inProgressModels.length === 0 && (
                <p className="text-sm text-muted-foreground">Load metrics to see bounds (uses same horizon as chart).</p>
              )}
              {(metrics?.bounds.length ?? 0) > 0 || inProgressModels.length > 0 ? (
                <div className="overflow-x-auto space-y-4">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 font-medium">Model</th>
                        <th className="text-right py-2 font-medium">Lowest expected</th>
                        <th className="text-right py-2 font-medium">Highest expected</th>
                        <th className="text-right py-2 font-medium">Average forecast</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(compareAll
                          ? METRICS_MODEL_ORDER
                          : inProgressModels.length > 0
                            ? inProgressModels
                            : (metrics?.bounds ?? []).map((b) => b.model)
                      ).map((modelKey) => {
                        const b = metrics?.bounds.find((x) => x.model === modelKey);
                        const loading = inProgressModels.includes(modelKey as ChartModel);
                        if (loading) {
                          return (
                            <tr key={modelKey} className="border-b border-border/50">
                              <td className="py-2 capitalize">{modelKey}</td>
                              <td className="text-right py-2" colSpan={3}>
                                <span className="inline-flex items-center gap-1.5 text-muted-foreground">
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  Loading…
                                </span>
                              </td>
                            </tr>
                          );
                        }
                        if (!b) return null;
                        const lowest = b.lower.length ? Math.min(...b.lower) : 0;
                        const highest = b.upper.length ? Math.max(...b.upper) : 0;
                        const avg =
                          b.forecast.length
                            ? b.forecast.reduce((s, v) => s + v, 0) / b.forecast.length
                            : 0;
                        return (
                          <tr key={b.model} className="border-b border-border/50">
                            <td className="py-2 capitalize">{b.model}</td>
                            <td className="text-right py-2">${lowest.toFixed(2)}</td>
                            <td className="text-right py-2">${highest.toFixed(2)}</td>
                            <td className="text-right py-2 font-medium">${avg.toFixed(2)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}

      {initialSymbol && (!initialPrices || initialPrices.length === 0) && (
        <div className="text-center py-20 text-muted-foreground">
          No price data found for {initialSymbol.toUpperCase()}. Try syncing it again.
        </div>
      )}
    </div>
  );
}
