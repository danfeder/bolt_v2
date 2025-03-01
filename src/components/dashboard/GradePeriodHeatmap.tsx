import React, { useEffect, useRef, useState } from 'react';
import type { GradePeriodHeatmapCell } from '../../types/dashboard';

// Adding the ApexCharts type for better type checking
declare global {
  interface Window {
    ApexCharts: any;
  }
}

interface GradePeriodHeatmapProps {
  data: GradePeriodHeatmapCell[];
}

/**
 * Component for displaying grade-period distribution as a heatmap
 */
export const GradePeriodHeatmap: React.FC<GradePeriodHeatmapProps> = ({ data }) => {
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
  }, [data]);

  const initializeChart = () => {
    if (chartRef.current && window.ApexCharts && data.length > 0) {
      // Destroy previous chart instance if it exists
      if (chartInstance) {
        chartInstance.destroy();
      }

      // Get unique grades and periods
      const uniqueGrades = [...new Set(data.map(d => d.grade))].sort();
      const uniquePeriods = [...new Set(data.map(d => d.period))].sort((a, b) => a - b);
      
      // Organize data into format required by ApexCharts
      const seriesData = uniqueGrades.map(grade => {
        const gradeData = uniquePeriods.map(period => {
          const cell = data.find(d => d.grade === grade && d.period === period);
          return {
            x: `Period ${period}`,
            y: cell ? cell.value : 0
          };
        });
        
        return {
          name: grade,
          data: gradeData
        };
      });

      // Configure chart options
      const options = {
        chart: {
          type: 'heatmap',
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
          text: 'Grade-Period Distribution',
          align: 'left',
          style: {
            fontSize: '16px',
            fontWeight: 600,
            color: '#263238'
          }
        },
        series: seriesData,
        dataLabels: {
          enabled: true,
          style: {
            colors: ['#fff']
          }
        },
        colors: ['#008FFB'],
        plotOptions: {
          heatmap: {
            shadeIntensity: 0.5,
            radius: 0,
            useFillColorAsStroke: true,
            colorScale: {
              ranges: [
                {
                  from: 0,
                  to: 0,
                  name: 'No Classes',
                  color: '#F5F5F5'
                },
                {
                  from: 1,
                  to: 1,
                  name: '1 Class',
                  color: '#C5E8B7'
                },
                {
                  from: 2,
                  to: 2,
                  name: '2 Classes',
                  color: '#83D475'
                },
                {
                  from: 3,
                  to: 3,
                  name: '3 Classes',
                  color: '#4CB944'
                },
                {
                  from: 4,
                  to: 1000,
                  name: '4+ Classes',
                  color: '#2E8540'
                }
              ]
            }
          }
        },
        xaxis: {
          categories: uniquePeriods.map(p => `Period ${p}`),
          labels: {
            rotate: 0
          }
        },
        tooltip: {
          y: {
            formatter: function(val: number) {
              return val === 1 ? '1 class' : val + ' classes';
            }
          }
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

  return (
    <div className="h-full">
      <div ref={chartRef} className="w-full h-80"></div>
      {data.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">No grade-period data available</p>
        </div>
      )}
    </div>
  );
};
