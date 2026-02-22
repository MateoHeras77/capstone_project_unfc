"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { OptimizeResponse } from "@/types/api";
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
import { Loader2, X } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
  "#A4DE6C",
  "#D0ED57",
  "#F2C80F",
  "#FF6666",
];

export default function PortfolioBuilder() {
  const [symbols, setSymbols] = useState<string[]>(["AAPL", "MSFT", "GOOGL"]);
  const [newSymbol, setNewSymbol] = useState("");
  const [target, setTarget] = useState<
    "max_sharpe" | "min_volatility" | "efficient_return" | "efficient_risk"
  >("max_sharpe");
  const [targetValue, setTargetValue] = useState<string>("");
  const [results, setResults] = useState<OptimizeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAddSymbol = () => {
    const sym = newSymbol.trim().toUpperCase();
    if (sym && !symbols.includes(sym)) {
      if (symbols.length >= 10) {
        toast({
          title: "Limit Reached",
          description: "You can only add up to 10 symbols.",
          variant: "destructive",
        });
        return;
      }
      setSymbols([...symbols, sym]);
      setNewSymbol("");
    }
  };

  const handleRemoveSymbol = (sym: string) => {
    setSymbols(symbols.filter((s) => s !== sym));
  };

  const handleOptimize = async () => {
    if (symbols.length < 2) {
      toast({
        title: "Not Enough Assets",
        description: "Please add at least 2 assets to optimize.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const reqData: any = {
        symbols,
        target,
      };

      if (target === "efficient_return") {
        reqData.target_return = parseFloat(targetValue);
      } else if (target === "efficient_risk") {
        reqData.target_volatility = parseFloat(targetValue);
      }

      const res = await api.portfolioOptimize(reqData);
      setResults(res);
      toast({
        title: "Optimization Complete",
        description: "Portfolio weights have been calculated.",
      });
    } catch (error: any) {
      toast({
        title: "Optimization Failed",
        description: error.message || "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const pieData = results
    ? Object.entries(results.weights).map(([name, value]) => ({
        name,
        value: value * 100,
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio Builder</h1>
        <p className="text-muted-foreground">
          Construct and optimize your investment portfolio.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Assets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Add symbol (e.g. TSLA)"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddSymbol()}
                />
                <Button onClick={handleAddSymbol}>Add</Button>
              </div>
              <div className="space-y-2">
                {symbols.map((sym) => (
                  <div
                    key={sym}
                    className="flex items-center justify-between bg-muted/50 p-2 rounded-md"
                  >
                    <span className="font-medium">{sym}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => handleRemoveSymbol(sym)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Optimization Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Objective</label>
                <Select
                  value={target}
                  onValueChange={(val: any) => setTarget(val)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Objective" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="max_sharpe">Maximize Sharpe Ratio</SelectItem>
                    <SelectItem value="min_volatility">Minimize Volatility</SelectItem>
                    <SelectItem value="efficient_return">Target Return</SelectItem>
                    <SelectItem value="efficient_risk">Target Volatility</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {(target === "efficient_return" || target === "efficient_risk") && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    {target === "efficient_return" ? "Target Return (%)" : "Target Volatility (%)"}
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="e.g. 0.15"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                  />
                </div>
              )}

              <Button
                className="w-full"
                onClick={handleOptimize}
                disabled={isLoading || symbols.length < 2}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Run Optimization
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {results ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="text-sm font-medium text-muted-foreground">
                      Expected Return
                    </div>
                    <div className="text-2xl font-bold">
                      {(results.performance.expected_return * 100).toFixed(2)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="text-sm font-medium text-muted-foreground">
                      Volatility
                    </div>
                    <div className="text-2xl font-bold">
                      {(results.performance.volatility * 100).toFixed(2)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="text-sm font-medium text-muted-foreground">
                      Sharpe Ratio
                    </div>
                    <div className="text-2xl font-bold">
                      {results.performance.sharpe_ratio.toFixed(2)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Optimal Weights</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {pieData.map((entry, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={COLORS[index % COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value: number) => [`${value.toFixed(2)}%`, "Weight"]}
                        />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="h-full flex items-center justify-center min-h-[400px]">
              <CardContent className="text-center text-muted-foreground">
                Add assets and run optimization to see results.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
