"use client";

import { useState } from "react";
import {
  PriceOut,
  AnalyzeResponse,
  ForecastResponse,
  ForecastHorizonWeeks,
} from "@/types/api";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Legend,
  ReferenceLine,
} from "recharts";
import { useToast } from "@/hooks/use-toast";

const MODEL_LABELS: Record<string, string> = {
  base: "Base (EWM)",
  prophet: "Prophet",
  lstm: "LSTM",
  chronos2: "Chronos-2",
  prophet_xgb: "Prophet + XGBoost",
};

const HORIZON_OPTIONS_WK: { value: ForecastHorizonWeeks; label: string }[] = [
  { value: 1, label: "1 week ahead" },
  { value: 2, label: "2 weeks ahead" },
  { value: 3, label: "3 weeks ahead" },
  { value: 4, label: "4 weeks ahead" },
];
const HORIZON_OPTIONS_MO: { value: ForecastHorizonWeeks; label: string }[] = [
  { value: 1, label: "1 month ahead" },
  { value: 2, label: "2 months ahead" },
  { value: 3, label: "3 months ahead" },
  { value: 4, label: "4 months ahead" },
];

export type ChartModel = "base" | "prophet" | "lstm" | "chronos2" | "prophet_xgb";

interface StockChartProps {
  symbol: string;
  initialPrices: PriceOut[];
  /** Controlled: chart interval (for Load metrics alignment). */
  interval?: "1wk" | "1mo";
  /** Controlled: horizon periods (1–4). */
  horizonWeeks?: ForecastHorizonWeeks;
  /** Controlled: selected model when not comparing all. */
  model?: ChartModel;
  /** Controlled: whether "Compare all models" is checked. */
  compareAll?: boolean;
  /** Notify parent when interval, horizon, model, or compareAll changes (for Load metrics). */
  onChartOptionsChange?: (
    interval: "1wk" | "1mo",
    horizon: ForecastHorizonWeeks,
    model?: ChartModel,
    compareAll?: boolean
  ) => void;
}

type ChartPoint = {
  date: string;
  price?: number;
  forecast_point?: number;
  lower?: number;
  upper?: number;
  forecast_base?: number;
  forecast_prophet?: number;
  forecast_lstm?: number;
  forecast_chronos2?: number;
  forecast_prophet_xgb?: number;
};

const MAX_HISTORY_WEEKS = 104;
const MAX_HISTORY_MONTHS = 24;

export function StockChart({
  symbol,
  initialPrices,
  interval: controlledInterval,
  horizonWeeks: controlledHorizon,
  model: controlledModel,
  compareAll: controlledCompareAll,
  onChartOptionsChange,
}: StockChartProps) {
  const [modelState, setModelState] = useState<ChartModel>("base");
  const [intervalState, setIntervalState] = useState<"1wk" | "1mo">("1wk");
  const [horizonState, setHorizonState] = useState<ForecastHorizonWeeks>(4);
  const [compareAllState, setCompareAllState] = useState(false);
  const model = controlledModel ?? modelState;
  const compareAll = controlledCompareAll ?? compareAllState;
  const interval = controlledInterval ?? intervalState;
  const horizonWeeks = controlledHorizon ?? horizonState;
  const [forecast, setForecast] = useState<AnalyzeResponse | null>(null);
  const [compareForecasts, setCompareForecasts] = useState<{
    base?: ForecastResponse;
    prophet?: ForecastResponse;
    lstm?: ForecastResponse;
    chronos2?: ForecastResponse;
    prophet_xgb?: ForecastResponse;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const periods =
    interval === "1wk" ? horizonWeeks : horizonWeeks; // same numeric periods for 1mo (months)

  let baseData = [...initialPrices].reverse();
  if (interval === "1wk" && baseData.length > MAX_HISTORY_WEEKS) {
    baseData = baseData.slice(-MAX_HISTORY_WEEKS);
  }

  if (interval === "1mo") {
    const monthlyGroups: Record<
      string,
      { sum: number; count: number; date: string }
    > = {};
    baseData.forEach((p) => {
      const d = new Date(p.timestamp);
      const monthKey = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      if (!monthlyGroups[monthKey]) {
        monthlyGroups[monthKey] = { sum: 0, count: 0, date: p.timestamp };
      }
      monthlyGroups[monthKey].sum += p.close_price;
      monthlyGroups[monthKey].count += 1;
    });
    baseData = Object.values(monthlyGroups)
      .map((group) => ({
        ...baseData[0],
        timestamp: group.date,
        close_price: group.sum / group.count,
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    if (baseData.length > MAX_HISTORY_MONTHS) {
      baseData = baseData.slice(-MAX_HISTORY_MONTHS);
    }
  }

  const chartData: ChartPoint[] = baseData.map((p) => ({
    date: p.timestamp,
    price: p.close_price,
  }));

  if (forecast && forecast.dates?.length > 0 && forecast.point_forecast?.length > 0) {
    const lastHist = baseData[baseData.length - 1];
    if (lastHist) {
      chartData.push({
        date: lastHist.timestamp,
        forecast_point: lastHist.close_price,
        lower: lastHist.close_price,
        upper: lastHist.close_price,
      });
    }
    forecast.dates.forEach((dateStr, i) => {
      chartData.push({
        date: dateStr,
        forecast_point: forecast.point_forecast[i],
        lower: forecast.lower_bound?.[i],
        upper: forecast.upper_bound?.[i],
      });
    });
  } else if (compareForecasts) {
    const byDateIso: Record<string, Partial<ChartPoint>> = {};
    const addForecast = (
      key: "forecast_base" | "forecast_prophet" | "forecast_lstm" | "forecast_chronos2" | "forecast_prophet_xgb",
      res: ForecastResponse
    ) => {
      res.dates.forEach((dateStr, i) => {
        if (!byDateIso[dateStr]) byDateIso[dateStr] = { date: dateStr };
        byDateIso[dateStr][key] = res.point_forecast[i];
      });
    };
    if (compareForecasts.base) addForecast("forecast_base", compareForecasts.base);
    if (compareForecasts.prophet)
      addForecast("forecast_prophet", compareForecasts.prophet);
    if (compareForecasts.lstm)
      addForecast("forecast_lstm", compareForecasts.lstm);
    if (compareForecasts.chronos2)
      addForecast("forecast_chronos2", compareForecasts.chronos2);
    if (compareForecasts.prophet_xgb)
      addForecast("forecast_prophet_xgb", compareForecasts.prophet_xgb);
    const sortedIsos = Object.keys(byDateIso).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime()
    );
    sortedIsos.forEach((iso) => {
      chartData.push({ date: iso, ...byDateIso[iso] });
    });
  }

  chartData.sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const handleAnalyze = async () => {
    setIsLoading(true);
    setCompareForecasts(null);
    try {
      if (compareAll) {
        const req = {
          symbol,
          interval,
          periods,
          lookback_window: 20,
          epochs: 50,
          confidence_level: 0.95,
        };
        const [baseRes, prophetRes, lstmRes, chronos2Res, prophetXgbRes] = await Promise.all([
          api.forecastBase(req),
          api.forecastProphet(req).catch(() => null),
          api.forecastLstm(req).catch(() => null),
          api.forecastChronos2(req).catch(() => null),
          api.forecastProphetXgb(req).catch(() => null),
        ]);
        setForecast(null);
        setCompareForecasts({
          base: baseRes,
          prophet: prophetRes ?? undefined,
          lstm: lstmRes ?? undefined,
          chronos2: chronos2Res ?? undefined,
          prophet_xgb: prophetXgbRes ?? undefined,
        });
        toast({
          title: "Compare complete",
          description: "All model forecasts loaded for overlay.",
        });
      } else {
        const res = await api.analyze(symbol, {
          model,
          interval,
          periods,
        });
        setForecast(res);
        setCompareForecasts(null);
        toast({
          title: "Forecast generated",
          description: `Using ${MODEL_LABELS[model] || model}.`,
        });
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "An error occurred";
      toast({
        title: "Forecast failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const horizonOptions = interval === "1mo" ? HORIZON_OPTIONS_MO : HORIZON_OPTIONS_WK;
  const horizonLabel =
    horizonOptions.find((o) => o.value === horizonWeeks)?.label ??
    (interval === "1wk" ? `${horizonWeeks} weeks ahead` : `${horizonWeeks} months ahead`);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-2 items-center">
          <Select
            value={model}
            onValueChange={(val: ChartModel) => {
              setModelState(val);
              if (onChartOptionsChange) onChartOptionsChange(interval, horizonWeeks, val, compareAll);
              setForecast(null);
              setCompareForecasts(null);
            }}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Select Model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="base">Base (EWM)</SelectItem>
              <SelectItem value="prophet">Prophet</SelectItem>
              <SelectItem value="lstm">LSTM</SelectItem>
              <SelectItem value="chronos2">Chronos-2</SelectItem>
              <SelectItem value="prophet_xgb">Prophet + XGBoost</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={interval}
            onValueChange={(val: "1wk" | "1mo") => {
              setIntervalState(val);
              if (onChartOptionsChange) onChartOptionsChange(val, horizonWeeks, model, compareAll);
              setForecast(null);
              setCompareForecasts(null);
            }}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Interval" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1wk">Weekly</SelectItem>
              <SelectItem value="1mo">Monthly</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={String(horizonWeeks)}
            onValueChange={(val) => {
              const h = Number(val) as ForecastHorizonWeeks;
              setHorizonState(h);
              if (onChartOptionsChange) onChartOptionsChange(interval, h, model, compareAll);
              setForecast(null);
              setCompareForecasts(null);
            }}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Horizon" />
            </SelectTrigger>
            <SelectContent>
              {(interval === "1mo" ? HORIZON_OPTIONS_MO : HORIZON_OPTIONS_WK).map((o) => (
                <SelectItem key={o.value} value={String(o.value)}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={compareAll}
              onChange={(e) => {
                const checked = e.target.checked;
                setCompareAllState(checked);
                if (onChartOptionsChange) onChartOptionsChange(interval, horizonWeeks, model, checked);
                setForecast(null);
                setCompareForecasts(null);
              }}
              className="rounded border-input"
            />
            Compare all models
          </label>
        </div>

        <Button onClick={handleAnalyze} disabled={isLoading}>
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Generate Forecast
        </Button>
      </div>

      <div className="h-[400px] w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tickFormatter={(value) =>
                new Date(value).toLocaleDateString(undefined, {
                  month: "numeric",
                  day: "numeric",
                  year: "numeric",
                })
              }
            />
            <YAxis
              domain={["auto", "auto"]}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (typeof value !== "number") return [];
                const label = name === "Forecast" || name === "Price" ? "Price" : name;
                return [`$${value.toFixed(2)}`, label];
              }}
              labelFormatter={(label) =>
                new Date(label).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              }
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                padding: "10px 14px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
              }}
              labelStyle={{
                color: "hsl(var(--card-foreground))",
                fontWeight: 600,
                marginBottom: 4,
              }}
              itemStyle={{
                color: "hsl(var(--card-foreground))",
              }}
            />
            <Legend />
            {chartData.length > baseData.length && (
              <ReferenceLine
                x={
                  forecast?.dates?.[0] ??
                  chartData[baseData.length]?.date
                }
                stroke="hsl(var(--muted-foreground))"
                strokeDasharray="3 3"
              />
            )}
            <Line
              type="monotone"
              dataKey="price"
              name="Historical"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
            {forecast && (
              <>
                <Line
                  type="monotone"
                  dataKey="upper"
                  name="Upper bound"
                  stroke="hsl(var(--muted-foreground))"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="lower"
                  name="Lower bound"
                  stroke="hsl(var(--muted-foreground))"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="forecast_point"
                  name="Forecast"
                  stroke="hsl(199 89% 48%)"
                  strokeDasharray="6 4"
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              </>
            )}
            {compareForecasts?.base && (
              <Line
                type="monotone"
                dataKey="forecast_base"
                name="Baseline"
                stroke="hsl(0 0% 75%)"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            )}
            {compareForecasts?.prophet && (
              <Line
                type="monotone"
                dataKey="forecast_prophet"
                name="Prophet"
                stroke="#c084fc"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            )}
            {compareForecasts?.lstm && (
              <Line
                type="monotone"
                dataKey="forecast_lstm"
                name="LSTM"
                stroke="#fb923c"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            )}
            {compareForecasts?.chronos2 && (
              <Line
                type="monotone"
                dataKey="forecast_chronos2"
                name="Chronos-2"
                stroke="#4ade80"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            )}
            {compareForecasts?.prophet_xgb && (
              <Line
                type="monotone"
                dataKey="forecast_prophet_xgb"
                name="Prophet + XGBoost"
                stroke="#f59e0b"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {(forecast || compareForecasts) && (
        <p className="text-sm text-muted-foreground text-center">
          {forecast
            ? forecast.forecast_horizon_label
            : `Forecast horizon: ${horizonLabel}`}
        </p>
      )}
    </div>
  );
}
