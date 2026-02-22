import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, BarChart3, PieChart } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] text-center space-y-8">
      <div className="space-y-4 max-w-3xl">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
          Investment Analytics
        </h1>
        <p className="text-xl text-muted-foreground max-w-[42rem] mx-auto">
          Analyze individual stocks with advanced forecasting models and build optimized portfolios using modern portfolio theory.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mt-8">
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <BarChart3 className="h-12 w-12 mb-4 text-primary" />
            <CardTitle className="text-2xl">Stock Viewer</CardTitle>
            <CardDescription className="text-base">
              Search for any stock to view its price history and generate forecasts using EWM, Prophet, or LSTM models.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/stock" passHref>
              <Button className="w-full group">
                Open Stock Viewer
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="flex flex-col justify-between">
          <CardHeader>
            <PieChart className="h-12 w-12 mb-4 text-primary" />
            <CardTitle className="text-2xl">Portfolio Builder</CardTitle>
            <CardDescription className="text-base">
              Construct a multi-asset portfolio and run PyPortfolioOpt to find the optimal weights for your investment goals.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/portfolio" passHref>
              <Button className="w-full group">
                Build Portfolio
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
