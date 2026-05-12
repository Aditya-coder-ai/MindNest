
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend
);

export default function MoodGraph({ data }) {
  const labels = data.map(d => d.day);
  const values = data.map(d => d.positivity ?? 0);
  const hasData = values.some(v => v > 0);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Positivity',
        data: values,
        fill: true,
        backgroundColor: (ctx) => {
          const { chart } = ctx;
          const { ctx: canvasCtx, chartArea } = chart;
          if (!chartArea) return 'rgba(123,94,167,0.1)';
          const gradient = canvasCtx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, 'rgba(123,94,167,0.25)');
          gradient.addColorStop(1, 'rgba(77,184,164,0.05)');
          return gradient;
        },
        borderColor: '#9b7bbd',
        borderWidth: 2.5,
        pointBackgroundColor: '#7b5ea7',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#3d2b52',
        titleColor: '#d5c0e8',
        bodyColor: '#ffffff',
        padding: 12,
        cornerRadius: 12,
        displayColors: false,
        titleFont: { family: 'Poppins', size: 11 },
        bodyFont: { family: 'Poppins', size: 13, weight: 600 },
        callbacks: {
          title: (items) => {
            const idx = items[0].dataIndex;
            return data[idx].mood ? `${data[idx].day} — ${data[idx].mood}` : data[idx].day;
          },
          label: (item) => `Positivity: ${item.raw}%`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          font: { family: 'Poppins', size: 11, weight: 500 },
          color: '#9a8ba8',
        },
        border: { display: false },
      },
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(107,77,138,0.06)',
          drawBorder: false,
        },
        ticks: {
          font: { family: 'Poppins', size: 10 },
          color: '#8b85ad',
          stepSize: 25,
          callback: v => `${v}%`,
        },
        border: { display: false },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  if (!hasData) {
    return (
      <div className="graph-empty">
        <span className="graph-empty-icon">📊</span>
        <p>No mood data yet. Start journaling to see your weekly trends!</p>
      </div>
    );
  }

  return (
    <div style={{ height: 220 }}>
      <Line data={chartData} options={options} />
    </div>
  );
}
