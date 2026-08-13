// A contribution-style calendar heatmap built on the standard heatmap: 7 rows
// (one weekday each) x ~53 columns (one week each). The trick that makes the
// columns line up is that every cell in a week shares the SAME x = the date of
// that week's Sunday. Because the x axis is datetime, the cells sit on a real
// time scale and the axis labels the months for us (continuous-x heatmap).
//
// The year runs from ~52 weeks ago through today, and a cell is emitted only
// for real in-range days: the first and last weeks are partial, so their
// off-range corners are simply left blank (the "hanging" edges of a year view)
// rather than padded. In-range days with zero activity still get a cell (the
// lightest color); only days outside the range are absent. All dates are in
// UTC so a day is always exactly 86400000 ms (no daylight-saving drift that
// would shift a cell into the wrong weekday).
var DAY = 86400000

var calNow = new Date()
var calEnd = Date.UTC(
  calNow.getUTCFullYear(),
  calNow.getUTCMonth(),
  calNow.getUTCDate(),
)
var calStart = calEnd - 364 * DAY

// The Sunday that starts the week containing a given day = that week's column x.
function weekStartOf(ms) {
  return ms - new Date(ms).getUTCDay() * DAY
}

// Datos enviados por Django
var rawCalendarData = JSON.parse(
    document.getElementById('calendar-data').textContent
);

function buildCalendar() {
  var weekdays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
  var byDay = weekdays.map(function (n) {
    return { name: n, data: [] }
  })

  // Deterministic PRNG so the demo looks the same on every reload.
  /*var seed = 20240407
  function rand() {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff
    return seed / 0x7fffffff
  }*/

  rawCalendarData.forEach(function (item) {
    // Fecha YYYY-MM-DD proveniente de Django
    var parts = item.date.split('-');
    var year = parseInt(parts[0]);
    var month = parseInt(parts[1]) - 1;
    var day = parseInt(parts[2]);

    // Siempre UTC
    var timestamp = Date.UTC(
        year,
        month,
        day
    );

    var dow = new Date(timestamp).getUTCDay();

    byDay[dow].data.push({

        // X = domingo de esa semana
        x: weekStartOf(timestamp),

        // Cantidad de actividades
        y: item.count,

        // Fecha real para tooltip
        date: timestamp
    });
  });

  // Rows read Sun (top) -> Sat (bottom). ApexCharts draws the last series on
  // top, so reverse the weekday order before returning.
  return byDay.reverse()
}

var calendarData = buildCalendar()
// Pad half a week on each side so the first and last columns are full width.
var calMinX = weekStartOf(calStart) - 3.5 * DAY
var calMaxX = weekStartOf(calEnd) + 3.5 * DAY

var options = {
  series: calendarData,
  chart: {
    height: 186,
    width: '100%',
    type: 'heatmap',
    toolbar: { show: false },
    animations: { enabled: false },
  },
  title: {
    text: 'Calendario de actividades',
    align: 'center',
    style: { fontSize: '14px', fontWeight: 600 },
  },
  dataLabels: { enabled: false },
  // A small light gap between cells, like a contributions calendar.
  stroke: { width: 3, colors: ['#fff'] },
  legend: { show: false },
  states: {
    active: {
      filter: {
        type: 'none',
      },
    },
  },
  plotOptions: {
    heatmap: {
      radius: 2,
      // Flat bucket colors (no within-range shading), so each level is one color.
      enableShades: false,
      colorScale: {
        ranges: [
          { from: 0, to: 0, name: '0', color: '#ebedf0' },
          { from: 1, to: 3, name: '1-3', color: '#9be9a8' },
          { from: 4, to: 7, name: '4-7', color: '#40c463' },
          { from: 8, to: 11, name: '8-11', color: '#30a14e' },
          { from: 12, to: 100, name: '12+', color: '#216e39' },
        ],
      },
    },
  },
  xaxis: {
    type: 'datetime',
    min: calMinX,
    max: calMaxX,
    position: 'top',
    labels: {
      format: 'MMM',
      datetimeUTC: false,
      formatter: function(val) {
        var meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
        var d = new Date(val);
        return meses[d.getUTCMonth()];
      },
      style: { colors: '#767676', fontSize: '12px' },
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
    tooltip: { enabled: false },
    crosshairs: {
      show: false,
    },
  },
  yaxis: {
    // Show only alternate weekday labels (Mon / Wed / Fri), like the original.
    labels: {
      formatter: function (val) {
        return ['Lun', 'Mié', 'Vie'].indexOf(val) >= 0 ? val : ''
      },
      style: { colors: ['#767676'], fontSize: '12px' },
    },
  },
  grid: {
    yaxis: {
      lines: {
        show: false,
      },
    },
  },
  tooltip: {
    // Custom tooltip so it can show the cell's real date (stashed on the datum)
    // plus the count, e.g. "5 contributions on Monday, January 8, 2024".
    custom: function (opts) {
      var pt = opts.w.config.series[opts.seriesIndex].data[opts.dataPointIndex]
      var n = pt.y
      var when = new Date(pt.date).toLocaleDateString('es-MX', {
        dateStyle: 'medium',
        timeZone: 'UTC',
      })
      var count =
        n === 0
          ? 'Sin actividaes'
          : n + (n === 1 ? ' actividad' : ' actividades')
      return (
        '<div style="padding:6px 10px;font-size:13px">' +
        '<b>' +
        count +
        '</b> on ' +
        when +
        '</div>'
      )
    },
  },
}

var chart = new ApexCharts(document.querySelector('#calendar_heatmap'), options)
chart.render()
