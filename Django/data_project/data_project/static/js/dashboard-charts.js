// Dashboard Charts Component
class DashboardCharts extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            fileStats: props.fileStats || { 
                csv: 0, 
                excel: 0, 
                db: 0,
                online: 0 
            },
            vizStats: props.vizStats || {
                bar: 0,
                line: 0,
                scatter: 0,
                pie: 0,
                histogram: 0
            }
        };
    }

    renderFileTypeChart() {
        const { fileStats } = this.state;
        const ctx = document.getElementById('fileTypeChart');
        
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['CSV', 'Excel', 'Database', 'Online DB'],
                    datasets: [{
                        data: [fileStats.csv, fileStats.excel, fileStats.db, fileStats.online],
                        backgroundColor: [
                            'rgba(13, 110, 253, 0.7)',  // Bootstrap primary (CSV)
                            'rgba(25, 135, 84, 0.7)',   // Bootstrap success (Excel)
                            'rgba(13, 202, 240, 0.7)',  // Bootstrap info (DB)
                            'rgba(255, 193, 7, 0.7)'    // Bootstrap warning (Online DB)
                        ],
                        borderColor: [
                            'rgba(13, 110, 253, 1)',
                            'rgba(25, 135, 84, 1)',
                            'rgba(13, 202, 240, 1)',
                            'rgba(255, 193, 7, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'File Types'
                        }
                    }
                }
            });
        }
    }

    renderVisualizationChart() {
        const { vizStats } = this.state;
        const ctx = document.getElementById('visualizationChart');
        
        if (ctx) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Bar', 'Line', 'Scatter', 'Pie', 'Histogram'],
                    datasets: [{
                        label: 'Number of Visualizations',
                        data: [
                            vizStats.bar, 
                            vizStats.line, 
                            vizStats.scatter, 
                            vizStats.pie, 
                            vizStats.histogram
                        ],
                        backgroundColor: 'rgba(13, 110, 253, 0.7)',
                        borderColor: 'rgba(13, 110, 253, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Visualization Types'
                        }
                    }
                }
            });
        }
    }

    componentDidMount() {
        // Render charts when component mounts
        this.renderFileTypeChart();
        this.renderVisualizationChart();
    }

    render() {
        return (
            <div className="row">
                <div className="col-md-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <canvas id="fileTypeChart"></canvas>
                        </div>
                    </div>
                </div>
                <div className="col-md-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <canvas id="visualizationChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

// Initialize the component if data is available
document.addEventListener('DOMContentLoaded', function() {
    const dashboardChartsContainer = document.getElementById('dashboard-charts');
    
    if (dashboardChartsContainer) {
        // Get data from the data attributes
        const fileStats = {
            csv: parseInt(dashboardChartsContainer.dataset.csvCount || 0),
            excel: parseInt(dashboardChartsContainer.dataset.excelCount || 0),
            db: parseInt(dashboardChartsContainer.dataset.dbCount || 0),
            online: parseInt(dashboardChartsContainer.dataset.onlineCount || 0)
        };
        
        const vizStats = {
            bar: parseInt(dashboardChartsContainer.dataset.barCount || 0),
            line: parseInt(dashboardChartsContainer.dataset.lineCount || 0),
            scatter: parseInt(dashboardChartsContainer.dataset.scatterCount || 0),
            pie: parseInt(dashboardChartsContainer.dataset.pieCount || 0),
            histogram: parseInt(dashboardChartsContainer.dataset.histogramCount || 0)
        };
        
        ReactDOM.render(
            <DashboardCharts fileStats={fileStats} vizStats={vizStats} />,
            dashboardChartsContainer
        );
    }
}); 