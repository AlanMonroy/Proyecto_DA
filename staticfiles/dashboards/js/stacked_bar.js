const series = JSON.parse(
    document.getElementById('chart-series').textContent
);

const categories = JSON.parse(
    document.getElementById('chart-categories').textContent
);

var options = {
  series: series,
  chart: {
    type: 'bar',
    height: 350,
    stacked: true,
  },
  plotOptions: {
    bar: {
      horizontal: true,
      dataLabels: {
        total: {
          enabled: true,
          offsetX: 0,
          style: {
            fontSize: '13px',
            fontWeight: 900,
          },
        },
      },
    },
  },
  stroke: {
    width: 1,
    colors: ['#fff'],
  },
  title: {
    text: 'Horas de actividades por proyecto y usuario',
  },
  xaxis: {
    categories: categories,
    labels: {
      formatter: function (val) {
        return val + 'H'
      },
    },
  },
  yaxis: {
    title: {
      text: undefined,
    },
  },
  tooltip: {
    y: {
      formatter: function (val) {
        return val + 'H'
      },
    },
  },
  fill: {
    opacity: 1,
  },
  legend: {
    position: 'top',
    horizontalAlign: 'left',
    offsetX: 40,
  },
}

var chart = new ApexCharts(document.querySelector('#chart'), options)
chart.render()
