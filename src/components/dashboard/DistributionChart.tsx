import React, { useEffect, useRef, useState } from 'react';
import type { ChartData } from '../../types/dashboard';

// Adding the ApexCharts type for better type checking
declare global {
  interface Window {
    ApexCharts: any;
  }
}

interface DistributionChartProps {
  chartData: ChartData;
  title?: string;
}

/**
 * Component for rendering charts based on the dashboard data
 */
export const DistributionChart: React.FC<DistributionChartProps> = ({ 
  chartData,
  title
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartInstance, setChartInstance] = useState<any>(null);

  useEffect(() => {
    // Load ApexCharts scripts dynamically if not already loaded
    if (!window.ApexCharts) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/apexcharts';
      script.async = true;
      script.onload = () => initializeChart();
      document.body.appendChild(script);
    } else {
      initializeChart();
    }

    return () => {
      // Cleanup chart instance when component unmounts
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  }, [chartData]);

  const initializeChart = () => {
    if (chartRef.current && window.ApexCharts) {
      // Destroy previous chart instance if it exists
      if (chartInstance) {
        chartInstance.destroy();
      }

      // Prepare series data in ApexCharts format
      const series = chartData.series.map(s => ({
        name: s.name,
        data: s.data.map(d => d.y)
      }));

      // Get categories (x-axis values)
      const categories = chartData.series[0]?.data.map(d => d.x.toString()) || [];

      // Select chart type
      const type = mapChartType(chartData.type);

      // Configure chart options
      const options = {
        chart: {
          type,
          height: 350,
          toolbar: {
            show: false
          },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800
          }
        },
        title: {
          text: title || chartData.title,
          align: 'left',
          style: {
            fontSize: '16px',
            fontWeight: 600,
            color: '#263238'
          }
        },
        series,
        xaxis: {
          categories,
          title: {
            text: chartData.xAxisLabel || ''
          }
        },
        yaxis: {
          title: {
            text: chartData.yAxisLabel || ''
          }
        },
        colors: chartData.series.map(s => s.color || undefined),
        plotOptions: {
          bar: {
            horizontal: false,
            columnWidth: '70%',
            borderRadius: 4,
            dataLabels: {
              position: 'top'
            }
          }
        },
        dataLabels: {
          enabled: type === 'bar' || type === 'pie',
          formatter: function(val: number) {
            return val.toFixed(0);
          },
          offsetY: -20,
          style: {
            fontSize: '12px',
            colors: ["#304758"]
          }
        },
        grid: {
          borderColor: '#e7e7e7',
          row: {
            colors: ['#f3f3f3', 'transparent'],
            opacity: 0.5
          }
        },
        legend: {
          position: 'top',
          horizontalAlign: 'right',
          floating: false,
          offsetY: -25,
          offsetX: -5
        },
        tooltip: {
          enabled: true,
          shared: true,
          intersect: false
        },
        responsive: [
          {
            breakpoint: 480,
            options: {
              chart: {
                height: 300
              },
              legend: {
                position: 'bottom'
              }
            }
          }
        ]
      };

      // Create and render chart
      const chart = new window.ApexCharts(chartRef.current, options);
      chart.render();
      setChartInstance(chart);
    }
  };

  // Map backend chart type to ApexCharts type
  const mapChartType = (type: string) => {
    switch (type) {
      case 'bar':
        return 'bar';
      case 'line':
        return 'line';
      case 'pie':
        return 'pie';
      case 'heatmap':
        return 'heatmap';
      default:
        return 'bar';
    }
  };

  return (
    <div className="h-full">
      <div ref={chartRef} className="w-full h-80"></div>
    </div>
  );
};
