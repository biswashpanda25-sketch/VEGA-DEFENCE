import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

const AXIS = {
  axisLine: { lineStyle: { color: '#1E2D3D' } },
  axisTick: { show: false },
  axisLabel: { color: '#8298AE', fontSize: 10 },
  splitLine: { lineStyle: { color: 'rgba(30, 45, 61, 0.45)' } },
}

export function EChart({ option, height = 220 }: { option: echarts.EChartsOption; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current, undefined, { renderer: 'canvas' })
    chartRef.current = chart
    const onResize = () => chart.resize()
    window.addEventListener('resize', onResize)
    return () => { window.removeEventListener('resize', onResize); chart.dispose(); chartRef.current = null }
  }, [])

  useEffect(() => { chartRef.current?.setOption(option, true) }, [option])

  return <div ref={ref} style={{ width: '100%', height }} className="chart" />
}

export const palette = ['#D5A13C', '#5FB3A1', '#6D8CFF', '#D9534F', '#8298AE', '#A78BFA', '#5AA87A']

export function barOption(data: Record<string, number>, horizontal = false): echarts.EChartsOption {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10)
  return {
    backgroundColor: 'transparent',
    grid: { left: horizontal ? 96 : 34, right: 16, top: 12, bottom: 22 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#15212D',
      borderColor: '#1E2D3D',
      textStyle: { color: '#E9EEF4', fontSize: 11 },
      extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.5); border-radius: 4px;',
    },
    xAxis: horizontal ? { type: 'value', ...AXIS } : { type: 'category', data: entries.map((e) => e[0]), ...AXIS },
    yAxis: horizontal ? { type: 'category', data: entries.map((e) => e[0]), ...AXIS } : { type: 'value', ...AXIS },
    series: [{
      type: 'bar',
      data: entries.map((e) => e[1]),
      barMaxWidth: 22,
      itemStyle: { color: '#D5A13C', borderRadius: [2, 2, 0, 0] },
    }],
  }
}

export function donutOption(data: Record<string, number>): echarts.EChartsOption {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#15212D',
      borderColor: '#1E2D3D',
      textStyle: { color: '#E9EEF4', fontSize: 11 },
      extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.5); border-radius: 4px;',
    },
    legend: {
      orient: 'vertical', right: 4, top: 'center',
      textStyle: { color: '#8298AE', fontSize: 10 }, itemWidth: 8, itemHeight: 8, itemGap: 7,
    },
    color: palette,
    series: [{
      type: 'pie',
      radius: ['50%', '72%'],
      center: ['34%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#15212D', borderWidth: 2 },
      label: { show: false },
      data: Object.entries(data).map(([name, value]) => ({ name, value })),
    }],
  }
}
